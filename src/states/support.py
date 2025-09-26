from ..core.base import State, Context, Action, ActionType, Position
from ..sensors import SituationAwareness
import logging


logger = logging.getLogger(__name__)


class SupportState(State):
    """辅助状态"""

    def __init__(self, name: str = "SupportState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入辅助状态"""
        logger.info(f"{context.role.name} 进入辅助状态")

    def update(self, context: Context) -> State:
        """更新辅助状态"""
        role = context.role
        game_state = context.game_state

        # 寻找需要帮助的队友
        target_ally = self._find_ally_in_need(game_state, role)

        if target_ally:
            distance = role.position.distance_to(target_ally.position)

            # 检查是否有治疗技能
            has_heal_skill = any("heal" in skill.lower() for skill in role.skills)

            if has_heal_skill and distance <= 300 and role.mana_percentage > 0.3:
                # 使用治疗技能
                heal_skill = next(skill for skill in role.skills if "heal" in skill.lower())
                action = Action(
                    action_type=ActionType.SKILL_SUPPORT,
                    target_id=target_ally.id,
                    skill_id=heal_skill,
                    priority=3
                )
                context.set_action(action)
                logger.debug(f"{role.name} 治疗 {target_ally.name}")
            else:
                # 移向需要帮助的队友
                action = Action(
                    action_type=ActionType.MOVE,
                    position=target_ally.position,
                    priority=2
                )
                context.set_action(action)
                logger.debug(f"{role.name} 前往支援 {target_ally.name}")
        else:
            # 没有队友需要帮助，跟随最近的队友
            nearest_ally = self._find_nearest_ally(game_state, role)
            if nearest_ally:
                distance = role.position.distance_to(nearest_ally.position)

                if distance > 200:  # 保持一定距离
                    action = Action(
                        action_type=ActionType.MOVE,
                        position=nearest_ally.position,
                        priority=1
                    )
                    context.set_action(action)
                    logger.debug(f"{role.name} 跟随 {nearest_ally.name}")

        # 检查是否需要自卫
        status = self.situation_awareness.analyze_role_status(game_state, role)
        if status.is_in_danger:
            from .defensive import RetreatState
            return RetreatState()

        # 检查是否可以参与进攻
        if self.situation_awareness.should_attack(game_state, role):
            from .offensive import AttackState
            return AttackState()

        return None

    def exit(self, context: Context) -> None:
        """离开辅助状态"""
        logger.debug(f"{context.role.name} 离开辅助状态")

    def _find_ally_in_need(self, game_state, role):
        """寻找需要帮助的队友"""
        best_ally = None
        best_score = 0

        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            score = 0
            # 血量越低得分越高
            score += (1 - ally.health_percentage) * 100

            # 距离越近得分越高
            distance = role.position.distance_to(ally.position)
            if distance < 500:
                score += (500 - distance) / 5

            if score > best_score and score > 30:
                best_score = score
                best_ally = ally

        return best_ally

    def _find_nearest_ally(self, game_state, role):
        """寻找最近的队友"""
        nearest_ally = None
        min_distance = float('inf')

        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            distance = role.position.distance_to(ally.position)
            if distance < min_distance:
                min_distance = distance
                nearest_ally = ally

        return nearest_ally


class FollowState(State):
    """跟随状态"""

    def __init__(self, name: str = "FollowState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入跟随状态"""
        logger.info(f"{context.role.name} 进入跟随状态")

    def update(self, context: Context) -> State:
        """更新跟随状态"""
        role = context.role
        game_state = context.game_state

        # 寻找要跟随的目标（通常是攻击力最高的队友）
        target = self._find_follow_target(game_state, role)

        if target:
            distance = role.position.distance_to(target.position)

            if distance > 150:  # 保持跟随距离
                action = Action(
                    action_type=ActionType.MOVE,
                    position=target.position,
                    priority=1
                )
                context.set_action(action)
                logger.debug(f"{role.name} 跟随 {target.name}")

        # 检查是否需要支援
        if self._should_support_allies(game_state, role):
            return SupportState()

        # 检查是否需要自卫
        status = self.situation_awareness.analyze_role_status(game_state, role)
        if status.is_in_danger:
            from .defensive import RetreatState
            return RetreatState()

        return None

    def exit(self, context: Context) -> None:
        """离开跟随状态"""
        logger.debug(f"{context.role.name} 离开跟随状态")

    def _find_follow_target(self, game_state, role):
        """寻找跟随目标"""
        best_target = None
        best_score = 0

        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            # 选择攻击力最高的队友作为跟随目标
            score = ally.attack_damage + ally.defense * 0.5

            if score > best_score:
                best_score = score
                best_target = ally

        return best_target

    def _should_support_allies(self, game_state, role):
        """判断是否需要支援队友"""
        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            # 队友血量低时需要支援
            if ally.health_percentage < 0.4:
                return True

        return False


class BuffState(State):
    """增益状态"""

    def __init__(self, name: str = "BuffState"):
        super().__init__(name)
        self.situation_awareness = SituationAwareness()

    def enter(self, context: Context) -> None:
        """进入增益状态"""
        logger.info(f"{context.role.name} 进入增益状态")

    def update(self, context: Context) -> State:
        """更新增益状态"""
        role = context.role
        game_state = context.game_state

        # 寻找增益技能
        buff_skills = [skill for skill in role.skills
                      if any(word in skill.lower() for word in ["buff", "boost", "haste", "shield"])]

        if buff_skills and role.mana_percentage > 0.4:
            # 寻找增益目标
            target = self._find_buff_target(game_state, role)

            if target:
                distance = role.position.distance_to(target.position)

                if distance <= 300:
                    # 使用增益技能
                    action = Action(
                        action_type=ActionType.SKILL_SUPPORT,
                        target_id=target.id,
                        skill_id=buff_skills[0],
                        priority=2
                    )
                    context.set_action(action)
                    logger.debug(f"{role.name} 对 {target.name} 使用增益技能 {buff_skills[0]}")

                    # 使用增益后返回辅助状态
                    return SupportState()

        # 没有增益技能或目标，返回辅助状态
        return SupportState()

    def exit(self, context: Context) -> None:
        """离开增益状态"""
        logger.debug(f"{context.role.name} 离开增益状态")

    def _find_buff_target(self, game_state, role):
        """寻找增益目标"""
        # 优先选择攻击力高的队友
        best_target = None
        best_score = 0

        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            score = ally.attack_damage
            distance = role.position.distance_to(ally.position)

            # 距离较近的队友优先
            if distance <= 300:
                score += 50

            if score > best_score:
                best_score = score
                best_target = ally

        return best_target