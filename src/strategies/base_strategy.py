from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from ..core.base import GameState, Role, Action, ActionType, Position
from ..sensors import SituationAwareness, BattleSituation, RoleStatus


logger = logging.getLogger(__name__)


class StrategyType(Enum):
    OFFENSIVE = "offensive"      # 进攻型
    DEFENSIVE = "defensive"      # 防守型
    SUPPORT = "support"          # 辅助型
    PUSH = "push"               # 推塔型
    FARM = "farm"               # 打野/发育型
    TEAM_FIGHT = "team_fight"   # 团战型
    SPLIT_PUSH = "split_push"   # 分推型


@dataclass
class StrategyResult:
    """策略执行结果"""
    action: Optional[Action]
    confidence: float  # 0-1之间的置信度
    reasoning: str     # 策略选择的原因
    priority: int      # 优先级


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, strategy_type: StrategyType):
        self.name = name
        self.strategy_type = strategy_type
        self.situation_awareness = SituationAwareness()
        self.weights: Dict[str, float] = {}
        self.cooldowns: Dict[str, int] = {}

    @abstractmethod
    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估当前策略的适用性，返回0-1的分数"""
        pass

    @abstractmethod
    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行策略"""
        pass

    @abstractmethod
    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        pass

    def can_execute(self, game_state: GameState, role: Role) -> bool:
        """检查是否可以执行该策略"""
        return role.is_alive

    def update_cooldowns(self) -> None:
        """更新冷却时间"""
        for key in list(self.cooldowns.keys()):
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1

    def set_cooldown(self, action_name: str, turns: int) -> None:
        """设置冷却时间"""
        self.cooldowns[action_name] = turns

    def is_on_cooldown(self, action_name: str) -> bool:
        """检查是否在冷却中"""
        return self.cooldowns.get(action_name, 0) > 0

    def get_battle_situation(self, game_state: GameState, role: Role) -> BattleSituation:
        """获取战场态势"""
        return self.situation_awareness.analyze_battle_situation(game_state, role)

    def get_role_status(self, game_state: GameState, role: Role) -> RoleStatus:
        """获取角色状态"""
        return self.situation_awareness.analyze_role_status(game_state, role)


class StrategySelector:
    """策略选择器"""

    def __init__(self):
        self.strategies: Dict[StrategyType, BaseStrategy] = {}
        self.current_strategy: Optional[BaseStrategy] = None
        self.strategy_history: List[Tuple[int, StrategyType]] = []
        self.minimum_strategy_duration = 3  # 最小策略持续回合数
        self.last_strategy_change = 0

    def register_strategy(self, strategy: BaseStrategy) -> None:
        """注册策略"""
        self.strategies[strategy.strategy_type] = strategy

    def select_strategy(self, game_state: GameState, role: Role, current_turn: int) -> BaseStrategy:
        """选择最优策略"""
        if self.current_strategy:
            # 检查是否满足最小持续时间
            if current_turn - self.last_strategy_change < self.minimum_strategy_duration:
                return self.current_strategy

        best_strategy = None
        best_score = -1

        for strategy in self.strategies.values():
            if not strategy.can_execute(game_state, role):
                continue

            score = strategy.evaluate(game_state, role)
            if score > best_score:
                best_score = score
                best_strategy = strategy

        if best_strategy and best_strategy != self.current_strategy:
            self.current_strategy = best_strategy
            self.last_strategy_change = current_turn
            self.strategy_history.append((current_turn, best_strategy.strategy_type))
            logger.info(f"策略切换: {best_strategy.name} (得分: {best_score:.2f})")

        return self.current_strategy or list(self.strategies.values())[0]

    def get_current_strategy_type(self) -> Optional[StrategyType]:
        """获取当前策略类型"""
        return self.current_strategy.strategy_type if self.current_strategy else None

    def get_strategy_history(self) -> List[Tuple[int, StrategyType]]:
        """获取策略历史"""
        return self.strategy_history.copy()


class StrategyManager:
    """策略管理器"""

    def __init__(self):
        self.selector = StrategySelector()
        self.role_strategies: Dict[str, StrategySelector] = {}
        self.team_strategy: Optional[BaseStrategy] = None

    def register_role_strategy(self, role_id: str, selector: StrategySelector) -> None:
        """为角色注册策略选择器"""
        self.role_strategies[role_id] = selector

    def set_team_strategy(self, strategy: BaseStrategy) -> None:
        """设置团队策略"""
        self.team_strategy = strategy

    def get_action_for_role(self, game_state: GameState, role: Role, current_turn: int) -> Optional[Action]:
        """为角色获取动作"""
        if role.id not in self.role_strategies:
            return None

        selector = self.role_strategies[role.id]
        strategy = selector.select_strategy(game_state, role, current_turn)

        if strategy:
            result = strategy.execute(game_state, role)
            return result.action

        return None

    def update_all_cooldowns(self) -> None:
        """更新所有冷却时间"""
        for selector in self.role_strategies.values():
            for strategy in selector.strategies.values():
                strategy.update_cooldowns()

    def get_team_strategy_status(self) -> Dict[str, Any]:
        """获取团队策略状态"""
        return {
            "team_strategy": self.team_strategy.name if self.team_strategy else None,
            "role_strategies": {
                role_id: selector.get_current_strategy_type().value
                for role_id, selector in self.role_strategies.items()
            }
        }