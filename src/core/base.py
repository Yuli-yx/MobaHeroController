from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


class ActionType(Enum):
    MOVE = "move"
    ATTACK = "attack"
    SKILL_ATTACK = "skill_attack"
    SKILL_SUPPORT = "skill_support"
    SKILL_MOVE = "skill_move"
    SKILL_POSITION = "skill_position"  # 位置技能（指定位置释放）
    DEFEND = "defend"
    HEAL = "heal"
    RETREAT = "retreat"


@dataclass
class Position:
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class Action:
    action_type: ActionType
    target_id: Optional[str] = None
    position: Optional[Position] = None
    skill_id: Optional[str] = None
    priority: int = 0

    def __post_init__(self):
        if self.action_type == ActionType.MOVE and self.position is None:
            raise ValueError("移动动作需要目标位置")
        if self.action_type in [ActionType.ATTACK, ActionType.SKILL_ATTACK] and self.target_id is None:
            raise ValueError("攻击动作需要目标ID")


@dataclass
class Role:
    id: str
    name: str
    position: Position
    health: float
    max_health: float
    mana: float
    max_mana: float
    attack_damage: float
    defense: float
    move_speed: float
    attack_range: float
    skills: List[str]
    is_alive: bool = True
    # 英雄特有属性
    hero_type: str = "normal"  # "mage", "warrior", "monkey", "normal"
    vision_range: float = 4.0
    diamonds: int = 100  # 钻石数量
    skill_cooldowns: Dict[str, int] = None
    buffs: List[Dict[str, Any]] = None
    # 技能冷却属性（兼容性）
    skill1_cooldown: int = 0
    skill2_cooldown: int = 0

    def __post_init__(self):
        if self.skill_cooldowns is None:
            self.skill_cooldowns = {}
        if self.buffs is None:
            self.buffs = []

    @property
    def health_percentage(self) -> float:
        return self.health / self.max_health if self.max_health > 0 else 0

    @property
    def mana_percentage(self) -> float:
        return self.mana / self.max_mana if self.max_mana > 0 else 0

    def get_skill_cooldown(self, skill_id: str) -> int:
        """获取技能冷却时间"""
        return self.skill_cooldowns.get(skill_id, 0)

    def set_skill_cooldown(self, skill_id: str, cooldown: int = 10) -> None:
        """设置技能冷却时间（所有英雄CD都是10）"""
        self.skill_cooldowns[skill_id] = cooldown
        # 同步到兼容性属性
        if len(self.skills) >= 1 and skill_id == self.skills[0]:
            self.skill1_cooldown = cooldown
        elif len(self.skills) >= 2 and skill_id == self.skills[1]:
            self.skill2_cooldown = cooldown

    def update_cooldowns(self) -> None:
        """更新所有技能冷却"""
        for skill_id in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[skill_id] > 0:
                self.skill_cooldowns[skill_id] -= 1
                # 同步到兼容性属性
                if len(self.skills) >= 1 and skill_id == self.skills[0]:
                    self.skill1_cooldown = self.skill_cooldowns[skill_id]
                elif len(self.skills) >= 2 and skill_id == self.skills[1]:
                    self.skill2_cooldown = self.skill_cooldowns[skill_id]

    def can_use_skill(self, skill_id: str) -> bool:
        """检查是否可以使用技能"""
        # 检查冷却
        if self.get_skill_cooldown(skill_id) > 0:
            return False

        # 检查钻石（所有技能消耗5钻石）
        if self.diamonds < 5:
            return False

        # 检查是否被沉默
        for buff in self.buffs:
            if buff.get('effect_type') == 'silence':
                return False

        return True

    def use_diamonds(self, amount: int) -> bool:
        """消耗钻石"""
        if self.diamonds >= amount:
            self.diamonds -= amount
            return True
        return False

    def add_buff(self, buff_data: Dict[str, Any]) -> None:
        """添加增益/减益效果"""
        self.buffs.append(buff_data)

    def remove_buff(self, buff_name: str) -> None:
        """移除指定buff"""
        self.buffs = [buff for buff in self.buffs if buff.get('name') != buff_name]

    def update_buffs(self) -> None:
        """更新buff状态"""
        # 减少所有buff的持续时间
        for buff in self.buffs[:]:
            if 'duration' in buff:
                buff['duration'] -= 1
                if buff['duration'] <= 0:
                    self.buffs.remove(buff)

    def get_damage_multiplier(self) -> float:
        """获取伤害倍率"""
        multiplier = 1.0
        for buff in self.buffs:
            if buff.get('effect_type') == 'damage_reduction':
                multiplier *= (1 - buff.get('value', 0))
        return multiplier

    def can_move(self) -> bool:
        """检查是否可以移动"""
        for buff in self.buffs:
            if buff.get('effect_type') == 'immobilize':
                return False
        return True

    def is_in_vision_range(self, target_position: Position) -> bool:
        """检查目标位置是否在视野范围内"""
        return self.position.distance_to(target_position) <= self.vision_range


@dataclass
class GameState:
    roles: Dict[str, Role]
    enemies: Dict[str, Role]
    towers: List[Dict[str, Any]]
    crystals: List[Dict[str, Any]]
    minions: List[Dict[str, Any]]
    current_turn: int
    map_width: float
    map_height: float
    # 游戏地图信息（实时更新）
    game_map: Optional[Dict[str, Any]] = None  # 实时地图信息
    lane_info: Optional[Dict[str, Any]] = None  # 分路信息
    structure_status: Optional[Dict[str, Any]] = None  # 建筑状态
    minion_waves: Optional[List[Dict[str, Any]]] = None  # 小兵波次信息
    # 队伍和资源信息
    team_side: str = "defender"  # "defender" or "challenger"
    diamonds_num: int = 1000  # 团队钻石总数

    def get_team_health_percentage(self) -> float:
        if not self.roles:
            return 0.0
        total_health = sum(role.health_percentage for role in self.roles.values())
        return total_health / len(self.roles)

    def get_enemy_team_health_percentage(self) -> float:
        if not self.enemies:
            return 0.0
        total_health = sum(enemy.health_percentage for enemy in self.enemies.values())
        return total_health / len(self.enemies)

    def get_visible_enemies(self, role_id: str) -> Dict[str, Role]:
        """获取指定角色可见的敌方单位"""
        if role_id not in self.roles:
            return {}

        role = self.roles[role_id]
        visible_enemies = {}

        # 检查每个敌人是否在视野范围内
        for enemy_id, enemy in self.enemies.items():
            if hasattr(role, 'is_in_vision_range'):
                if role.is_in_vision_range(enemy.position):
                    visible_enemies[enemy_id] = enemy
            else:
                # 对于普通角色，使用基础视野范围
                vision_range = 4.0
                if role.position.distance_to(enemy.position) <= vision_range:
                    visible_enemies[enemy_id] = enemy

        return visible_enemies

    def get_visible_structures(self, role_id: str) -> List[Dict[str, Any]]:
        """获取指定角色可见的建筑"""
        if role_id not in self.roles:
            return []

        role = self.roles[role_id]
        visible_structures = []

        vision_range = getattr(role, 'vision_range', 4.0)

        # 检查防御塔
        for tower in self.towers:
            if 'position' in tower:
                tower_pos = Position(tower['position']['x'], tower['position']['y'])
                if role.position.distance_to(tower_pos) <= vision_range:
                    visible_structures.append(tower)

        # 检查水晶
        for crystal in self.crystals:
            if 'position' in crystal:
                crystal_pos = Position(crystal['position']['x'], crystal['position']['y'])
                if role.position.distance_to(crystal_pos) <= vision_range:
                    visible_structures.append(crystal)

        return visible_structures

    def get_minions_in_range(self, center: Position, range: float) -> List[Dict[str, Any]]:
        """获取指定范围内的所有小兵"""
        minions_in_range = []

        for minion in self.minions:
            if 'position' in minion:
                minion_pos = Position(minion['position']['x'], minion['position']['y'])
                if center.distance_to(minion_pos) <= range:
                    minions_in_range.append(minion)

        return minions_in_range

    def process_minion_kill(self, killer_id: str, minion: Dict[str, Any]) -> None:
        """处理小兵击杀"""
        if killer_id in self.roles:
            killer = self.roles[killer_id]
            if hasattr(killer, 'heal_minion_kill'):
                killer.heal_minion_kill()

        # 从游戏中移除小兵
        if minion in self.minions:
            self.minions.remove(minion)

    def update_all_heroes(self) -> None:
        """更新所有英雄状态（buff、冷却等）"""
        # 更新我方英雄
        for role in self.roles.values():
            if hasattr(role, 'update_buffs'):
                role.update_buffs()
            if hasattr(role, 'update_cooldowns'):
                role.update_cooldowns()

        # 更新敌方英雄
        for enemy in self.enemies.values():
            if hasattr(enemy, 'update_buffs'):
                enemy.update_buffs()
            if hasattr(enemy, 'update_cooldowns'):
                enemy.update_cooldowns()

    def process_dot_effects(self) -> None:
        """处理持续伤害效果"""
        all_units = list(self.roles.values()) + list(self.enemies.values())

        for unit in all_units:
            if hasattr(unit, 'buffs'):
                damage_to_apply = 0
                buffs_to_remove = []

                for buff in unit.buffs:
                    if buff.effect_type == "dot":
                        damage_to_apply += buff.value

                # 应用伤害
                if damage_to_apply > 0:
                    unit.health = max(0, unit.health - damage_to_apply)
                    if unit.health == 0:
                        unit.is_alive = False


class State(ABC):
    """状态基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def enter(self, context: 'Context') -> None:
        """进入状态时调用"""
        pass

    @abstractmethod
    def update(self, context: 'Context') -> Optional['State']:
        """更新状态，返回下一个状态"""
        pass

    @abstractmethod
    def exit(self, context: 'Context') -> None:
        """离开状态时调用"""
        pass


class Context:
    """状态机上下文"""

    def __init__(self, game_state: GameState, role: Role):
        self.game_state = game_state
        self.role = role
        self.current_state: Optional[State] = None
        self.previous_state: Optional[State] = None
        self.state_history: List[State] = []
        self.action: Optional[Action] = None
        self.memory: Dict[str, Any] = {}

    def change_state(self, new_state: State) -> None:
        """切换状态"""
        if self.current_state:
            self.current_state.exit(self)
            self.previous_state = self.current_state

        self.current_state = new_state
        self.current_state.enter(self)
        self.state_history.append(new_state)

    def update(self) -> None:
        """更新状态机"""
        if self.current_state:
            next_state = self.current_state.update(self)
            if next_state and next_state != self.current_state:
                self.change_state(next_state)

    def set_action(self, action: Action) -> None:
        """设置动作"""
        self.action = action

    def get_memory(self, key: str, default: Any = None) -> Any:
        """获取记忆数据"""
        return self.memory.get(key, default)

    def set_memory(self, key: str, value: Any) -> None:
        """设置记忆数据"""
        self.memory[key] = value