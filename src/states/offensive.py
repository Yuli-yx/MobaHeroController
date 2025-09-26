from ..core.base import State, Context, Action, ActionType, Position
from ..sensors import SituationAwareness
import logging


logger = logging.getLogger(__name__)


class AttackState(State):
    """攻击状态"""

    def __init__(self, name: str = "AttackState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入攻击状态"""
        logger.info(f"{context.role.name} 进入攻击状态")

    def update(self, context: Context) -> State:
        """更新攻击状态"""
        role = context.role
        game_state = context.game_state

        # 寻找最佳目标
        target = self.situation_awareness.find_best_target(game_state, role)

        if not target:
            # 没有目标，切换到移动状态
            from .offensive import PursueState
            return PursueState()

        distance = role.position.distance_to(target.position)

        if distance <= role.attack_range:
            # 在攻击范围内，执行攻击
            action = Action(
                action_type=ActionType.ATTACK,
                target_id=target.id,
                priority=2
            )
            context.set_action(action)
            logger.debug(f"{role.name} 攻击 {target.name}")
        else:
            # 超出攻击范围，追击目标
            from .offensive import PursueState
            return PursueState()

        # 检查是否需要撤退
        if self.situation_awareness.should_retreat(game_state, role):
            from .defensive import RetreatState
            return RetreatState()

        return None

    def exit(self, context: Context) -> None:
        """离开攻击状态"""
        logger.debug(f"{context.role.name} 离开攻击状态")


class PursueState(State):
    """追击状态"""

    def __init__(self, name: str = "PursueState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入追击状态"""
        logger.info(f"{context.role.name} 进入追击状态")

    def update(self, context: Context) -> State:
        """更新追击状态"""
        role = context.role
        game_state = context.game_state

        # 寻找目标
        target = self.situation_awareness.find_best_target(game_state, role)

        if not target:
            # 没有目标，待机
            return None

        distance = role.position.distance_to(target.position)

        if distance <= role.attack_range:
            # 进入攻击范围，切换到攻击状态
            return AttackState()

        # 向目标移动
        action = Action(
            action_type=ActionType.MOVE,
            position=target.position,
            priority=1
        )
        context.set_action(action)
        logger.debug(f"{role.name} 追击 {target.name}")

        # 检查是否需要撤退
        if self.situation_awareness.should_retreat(game_state, role):
            from .defensive import RetreatState
            return RetreatState()

        return None

    def exit(self, context: Context) -> None:
        """离开追击状态"""
        logger.debug(f"{context.role.name} 离开追击状态")


class SkillState(State):
    """技能状态"""

    def __init__(self, name: str = "SkillState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入技能状态"""
        logger.info(f"{context.role.name} 进入技能状态")

    def update(self, context: Context) -> State:
        """更新技能状态"""
        role = context.role
        game_state = context.game_state

        # 检查是否有技能可用
        if not role.skills or role.mana_percentage < 0.3:
            # 没有技能或魔法不足，返回攻击状态
            return AttackState()

        # 寻找技能目标
        target = self.situation_awareness.find_best_target(game_state, role)

        if target:
            distance = role.position.distance_to(target.position)

            # 使用技能
            action = Action(
                action_type=ActionType.SKILL_ATTACK,
                target_id=target.id,
                skill_id=role.skills[0],  # 使用第一个技能
                priority=3
            )
            context.set_action(action)
            logger.debug(f"{role.name} 对 {target.name} 使用技能 {role.skills[0]}")

            # 技能使用后返回攻击状态
            return AttackState()

        return None

    def exit(self, context: Context) -> None:
        """离开技能状态"""
        logger.debug(f"{context.role.name} 离开技能状态")