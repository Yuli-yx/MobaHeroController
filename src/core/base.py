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