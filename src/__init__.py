"""
Honor For Legends - 分层状态机架构

这是一个为类MOBA回合制对战游戏设计的分层状态机实现，
提供了策略抽象、态势感知、动作执行和多角色协同功能。
"""

from .core import (
    ActionType,
    Position,
    Action,
    Role,
    GameState,
    State,
    Context,
    HierarchicalStateMachine,
    StateMachineFactory,
)
from .sensors import (
    SituationAwareness,
    BattleSituation,
    RoleStatus,
    ThreatLevel,
)
from .strategies import (
    BaseStrategy,
    StrategyResult,
    StrategyType,
    StrategySelector,
    StrategyManager,
    OffensiveStrategy,
    DefensiveStrategy,
    SupportStrategy,
    TeamFightStrategy,
)
from .actions import (
    ActionExecutor,
    ActionValidator,
    ActionResult,
    ExecutionResult,
    ActionOptimizer,
)
from .coordinators import (
    TeamCoordinator,
    TeamObjective,
    TeamPlan,
    RoleAssignment,
    RoleCoordinator,
    RoleType,
    RoleDirective,
)

__version__ = "1.0.0"
__author__ = "Claude AI"

__all__ = [
    # 核心基础类
    ActionType,
    Position,
    Action,
    Role,
    GameState,
    State,
    Context,
    HierarchicalStateMachine,
    StateMachineFactory,

    # 感知模块
    SituationAwareness,
    BattleSituation,
    RoleStatus,
    ThreatLevel,

    # 策略模块
    BaseStrategy,
    StrategyResult,
    StrategyType,
    StrategySelector,
    StrategyManager,
    OffensiveStrategy,
    DefensiveStrategy,
    SupportStrategy,
    TeamFightStrategy,

    # 动作执行模块
    ActionExecutor,
    ActionValidator,
    ActionResult,
    ExecutionResult,
    ActionOptimizer,

    # 协同模块
    TeamCoordinator,
    TeamObjective,
    TeamPlan,
    RoleAssignment,
    RoleCoordinator,
    RoleType,
    RoleDirective,
]