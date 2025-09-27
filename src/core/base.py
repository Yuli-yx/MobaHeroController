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

    @property
    def health_percentage(self) -> float:
        return self.health / self.max_health if self.max_health > 0 else 0

    @property
    def mana_percentage(self) -> float:
        return self.mana / self.max_mana if self.max_mana > 0 else 0


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
    # 新增字段
    game_map: Optional[Any] = None  # 游戏地图对象
    vision_map: Optional[Dict[str, Any]] = None  # 视野地图
    structure_effects: Optional[Dict[str, Any]] = None  # 建筑效果

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