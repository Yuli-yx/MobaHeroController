from typing import Dict, List, Optional, Type, Any
from .base import State, Context, GameState, Role
import logging


logger = logging.getLogger(__name__)


class HierarchicalStateMachine:
    """分层状态机"""

    def __init__(self, initial_state: Type[State]):
        self.initial_state = initial_state
        self.states: Dict[str, State] = {}
        self.transitions: Dict[str, List[str]] = {}
        self.context: Optional[Context] = None

    def register_state(self, state_class: Type[State]) -> None:
        """注册状态"""
        state_instance = state_class(state_class.__name__)
        self.states[state_instance.name] = state_instance

    def add_transition(self, from_state: str, to_state: str) -> None:
        """添加状态转移"""
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        if to_state not in self.transitions[from_state]:
            self.transitions[from_state].append(to_state)

    def initialize(self, game_state: GameState, role: Role) -> None:
        """初始化状态机"""
        self.context = Context(game_state, role)
        initial_state_instance = self.initial_state(self.initial_state.__name__)
        self.context.change_state(initial_state_instance)
        logger.info(f"状态机初始化完成，角色: {role.name}, 初始状态: {initial_state_instance.name}")

    def update(self) -> None:
        """更新状态机"""
        if self.context:
            self.context.update()

    def get_current_state(self) -> Optional[State]:
        """获取当前状态"""
        return self.context.current_state if self.context else None

    def get_action(self) -> Optional[Any]:
        """获取当前动作"""
        return self.context.action if self.context else None

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查是否可以转移"""
        return to_state in self.transitions.get(from_state, [])

    def get_state_history(self) -> List[str]:
        """获取状态历史"""
        if self.context:
            return [state.name for state in self.context.state_history]
        return []

    def force_change_state(self, state_name: str) -> bool:
        """强制切换状态"""
        if self.context and state_name in self.states:
            self.context.change_state(self.states[state_name])
            logger.info(f"强制切换状态到: {state_name}")
            return True
        return False


class StateMachineFactory:
    """状态机工厂"""

    @staticmethod
    def create_offensive_machine() -> HierarchicalStateMachine:
        """创建进攻型状态机"""
        from ..states.offensive import AttackState, PursueState, SkillState
        machine = HierarchicalStateMachine(AttackState)

        for state_class in [AttackState, PursueState, SkillState]:
            machine.register_state(state_class)

        machine.add_transition("AttackState", "PursueState")
        machine.add_transition("PursueState", "AttackState")
        machine.add_transition("AttackState", "SkillState")
        machine.add_transition("SkillState", "AttackState")

        return machine

    @staticmethod
    def create_defensive_machine() -> HierarchicalStateMachine:
        """创建防守型状态机"""
        from ..states.defensive import DefendState, RetreatState, HealState
        machine = HierarchicalStateMachine(DefendState)

        for state_class in [DefendState, RetreatState, HealState]:
            machine.register_state(state_class)

        machine.add_transition("DefendState", "RetreatState")
        machine.add_transition("RetreatState", "HealState")
        machine.add_transition("HealState", "DefendState")

        return machine

    @staticmethod
    def create_support_machine() -> HierarchicalStateMachine:
        """创建辅助型状态机"""
        from ..states.support import SupportState, FollowState, BuffState
        machine = HierarchicalStateMachine(SupportState)

        for state_class in [SupportState, FollowState, BuffState]:
            machine.register_state(state_class)

        machine.add_transition("SupportState", "FollowState")
        machine.add_transition("FollowState", "BuffState")
        machine.add_transition("BuffState", "SupportState")

        return machine