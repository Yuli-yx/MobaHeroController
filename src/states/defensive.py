from ..core.base import State, Context, Action, ActionType, Position
from ..sensors import SituationAwareness
import logging


logger = logging.getLogger(__name__)


class DefendState(State):
    """防守状态"""

    def __init__(self, name: str = "DefendState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入防守状态"""
        logger.info(f"{context.role.name} 进入防守状态")

    def update(self, context: Context) -> State:
        """更新防守状态"""
        role = context.role
        game_state = context.game_state

        # 分析角色状态
        status = self.situation_awareness.analyze_role_status(game_state, role)
        situation = self.situation_awareness.analyze_battle_situation(game_state, role)

        # 寻找附近的敌人
        if status.nearest_enemy:
            distance = role.position.distance_to(status.nearest_enemy.position)

            if distance <= role.attack_range:
                # 敌人在攻击范围内，进行防守反击
                action = Action(
                    action_type=ActionType.ATTACK,
                    target_id=status.nearest_enemy.id,
                    priority=2
                )
                context.set_action(action)
                logger.debug(f"{role.name} 防守反击 {status.nearest_enemy.name}")
            else:
                # 保持安全距离
                safe_position = self._calculate_safe_position(role, status.nearest_enemy)
                action = Action(
                    action_type=ActionType.MOVE,
                    position=safe_position,
                    priority=1
                )
                context.set_action(action)
                logger.debug(f"{role.name} 移动到安全位置")
        else:
            # 没有敌人 nearby，向友方靠拢
            safe_position = self.situation_awareness.find_safest_position(game_state, role)
            action = Action(
                action_type=ActionType.MOVE,
                position=safe_position,
                priority=1
            )
            context.set_action(action)

        # 检查是否可以转为进攻
        if self.situation_awareness.should_attack(game_state, role):
            from .offensive import AttackState
            return AttackState()

        # 检查是否需要撤退
        if status.is_low_health and situation.threat_level.value >= 3:
            from .defensive import RetreatState
            return RetreatState()

        return None

    def exit(self, context: Context) -> None:
        """离开防守状态"""
        logger.debug(f"{context.role.name} 离开防守状态")

    def _calculate_safe_position(self, role, enemy) -> Position:
        """计算安全位置"""
        # 计算远离敌人的位置
        dx = role.position.x - enemy.position.x
        dy = role.position.y - enemy.position.y
        distance = (dx**2 + dy**2)**0.5

        if distance > 0:
            # 保持400距离
            target_distance = 400
            scale = target_distance / distance
            new_x = role.position.x + dx * scale * 0.5
            new_y = role.position.y + dy * scale * 0.5

            return Position(new_x, new_y)

        return role.position


class RetreatState(State):
    """撤退状态"""

    def __init__(self, name: str = "RetreatState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入撤退状态"""
        logger.info(f"{context.role.name} 进入撤退状态")

    def update(self, context: Context) -> State:
        """更新撤退状态"""
        role = context.role
        game_state = context.game_state

        # 寻找安全位置
        safe_position = self.situation_awareness.find_safest_position(game_state, role)

        # 向安全位置移动
        action = Action(
            action_type=ActionType.MOVE,
            position=safe_position,
            priority=3  # 高优先级
        )
        context.set_action(action)
        logger.debug(f"{role.name} 撤退到安全位置")

        # 检查是否已经安全
        status = self.situation_awareness.analyze_role_status(game_state, role)
        if status.health_percentage > 0.6 and not status.is_in_danger:
            # 已经安全，转为防守状态
            return DefendState()

        return None

    def exit(self, context: Context) -> None:
        """离开撤退状态"""
        logger.debug(f"{context.role.name} 离开撤退状态")


class HealState(State):
    """治疗状态"""

    def __init__(self, name: str = "HealState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入治疗状态"""
        logger.info(f"{context.role.name} 进入治疗状态")

    def update(self, context: Context) -> State:
        """更新治疗状态"""
        role = context.role
        game_state = context.game_state

        # 检查是否有治疗技能
        has_heal_skill = any("heal" in skill.lower() for skill in role.skills)

        if has_heal_skill and role.mana_percentage > 0.4:
            # 使用治疗技能
            action = Action(
                action_type=ActionType.SKILL_SUPPORT,
                target_id=role.id,  # 治疗自己
                skill_id=next(skill for skill in role.skills if "heal" in skill.lower()),
                priority=4
            )
            context.set_action(action)
            logger.debug(f"{role.name} 使用治疗技能")

        # 移动到更安全的位置
        safe_position = self.situation_awareness.find_safest_position(game_state, role)
        move_action = Action(
            action_type=ActionType.MOVE,
            position=safe_position,
            priority=2
        )
        context.set_action(move_action)

        # 检查是否恢复完成
        if role.health_percentage > 0.8:
            # 恢复完成，转为防守状态
            return DefendState()

        return None

    def exit(self, context: Context) -> None:
        """离开治疗状态"""
        logger.debug(f"{context.role.name} 离开治疗状态")