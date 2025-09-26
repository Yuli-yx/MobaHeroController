import random
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy, StrategyResult, StrategyType
from ..core.base import GameState, Role, Action, ActionType, Position
from ..sensors import ThreatLevel


class OffensiveStrategy(BaseStrategy):
    """进攻策略"""

    def __init__(self):
        super().__init__("进攻策略", StrategyType.OFFENSIVE)
        self.weights = {
            "enemy_health": 0.4,
            "distance": 0.3,
            "threat_level": 0.2,
            "ally_support": 0.1
        }

    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估进攻策略的适用性"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        score = 0.5  # 基础分数

        # 血量充足时更适合进攻
        if status.health_percentage > 0.7:
            score += 0.3
        elif status.health_percentage < 0.4:
            score -= 0.4

        # 敌人血量低时适合进攻
        if situation.average_enemy_health < 0.5:
            score += 0.2

        # 团队优势时适合进攻
        if situation.team_advantage > 0.2:
            score += 0.3

        # 威胁等级低时适合进攻
        if situation.threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]:
            score += 0.2
        elif situation.threat_level == ThreatLevel.CRITICAL:
            score -= 0.5

        return max(0.0, min(1.0, score))

    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行进攻策略"""
        target = self.situation_awareness.find_best_target(game_state, role)

        if not target:
            return StrategyResult(
                action=None,
                confidence=0.0,
                reasoning="没有找到合适的目标",
                priority=1
            )

        distance = role.position.distance_to(target.position)

        # 如果在攻击范围内，进行攻击
        if distance <= role.attack_range:
            action = Action(
                action_type=ActionType.ATTACK,
                target_id=target.id,
                priority=2
            )
            confidence = 0.9
            reasoning = f"攻击范围内的敌人 {target.name}"

            # 检查是否可以使用技能
            if status.can_use_skills and not self.is_on_cooldown("skill"):
                action = Action(
                    action_type=ActionType.SKILL_ATTACK,
                    target_id=target.id,
                    skill_id=role.skills[0] if role.skills else None,
                    priority=3
                )
                self.set_cooldown("skill", 3)
                confidence = 0.95
                reasoning = f"使用技能攻击敌人 {target.name}"
        else:
            # 移动向目标
            action = Action(
                action_type=ActionType.MOVE,
                position=target.position,
                priority=1
            )
            confidence = 0.7
            reasoning = f"接近敌人 {target.name}"

        return StrategyResult(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            priority=2
        )

    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        return {
            StrategyType.DEFENSIVE: 0.3,  # 血量低于30%时转换为防守
            StrategyType.SUPPORT: 0.1,   # 团队需要辅助时转换
            StrategyType.TEAM_FIGHT: 0.6 # 团战时转换
        }


class DefensiveStrategy(BaseStrategy):
    """防守策略"""

    def __init__(self):
        super().__init__("防守策略", StrategyType.DEFENSIVE)
        self.weights = {
            "health": 0.5,
            "threat_level": 0.3,
            "enemy_count": 0.2
        }

    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估防守策略的适用性"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        score = 0.3  # 基础分数

        # 血量低时适合防守
        if status.health_percentage < 0.4:
            score += 0.4
        elif status.health_percentage < 0.2:
            score += 0.4

        # 威胁等级高时适合防守
        if situation.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            score += 0.3

        # 敌人数量多时适合防守
        if situation.enemy_count > situation.ally_count:
            score += 0.2

        # 团队劣势时适合防守
        if situation.team_advantage < -0.2:
            score += 0.2

        return max(0.0, min(1.0, score))

    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行防守策略"""
        status = self.get_role_status(game_state, role)
        situation = self.get_battle_situation(game_state, role)

        # 血量过低，寻找安全位置
        if status.is_low_health:
            safe_position = self.situation_awareness.find_safest_position(game_state, role)
            action = Action(
                action_type=ActionType.MOVE,
                position=safe_position,
                priority=3
            )
            return StrategyResult(
                action=action,
                confidence=0.9,
                reasoning="血量过低，撤退到安全位置",
                priority=3
            )

        # 有敌人 nearby 但血量尚可，准备防守
        if situation.enemy_count > 0:
            nearest_enemy = status.nearest_enemy
            if nearest_enemy:
                distance = role.position.distance_to(nearest_enemy.position)

                if distance <= role.attack_range:
                    action = Action(
                        action_type=ActionType.ATTACK,
                        target_id=nearest_enemy.id,
                        priority=2
                    )
                    return StrategyResult(
                        action=action,
                        confidence=0.7,
                        reasoning="防守反击",
                        priority=2
                    )
                else:
                    # 保持距离
                    action = Action(
                        action_type=ActionType.MOVE,
                        position=self._calculate_defensive_position(game_state, role, nearest_enemy),
                        priority=2
                    )
                    return StrategyResult(
                        action=action,
                        confidence=0.8,
                        reasoning="保持防守距离",
                        priority=2
                    )

        # 默认：向友方靠拢
        safe_position = self.situation_awareness.find_safest_position(game_state, role)
        action = Action(
            action_type=ActionType.MOVE,
            position=safe_position,
            priority=1
        )
        return StrategyResult(
            action=action,
            confidence=0.6,
            reasoning="向友方靠拢",
            priority=1
        )

    def _calculate_defensive_position(self, game_state: GameState, role: Role, enemy: Role) -> Position:
        """计算防守位置"""
        # 计算远离敌人的位置，但不要移动太远
        dx = role.position.x - enemy.position.x
        dy = role.position.y - enemy.position.y
        distance = (dx**2 + dy**2)**0.5

        if distance > 0:
            # 标准化方向向量并移动到合适的距离
            target_distance = 400  # 保持400距离
            scale = target_distance / distance
            new_x = role.position.x + dx * scale * 0.5  # 移动一半距离
            new_y = role.position.y + dy * scale * 0.5

            # 确保不超出地图边界
            new_x = max(0, min(game_state.map_width, new_x))
            new_y = max(0, min(game_state.map_height, new_y))

            return Position(new_x, new_y)

        return role.position

    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        return {
            StrategyType.OFFENSIVE: 0.7,  # 血量恢复后转为进攻
            StrategyType.SUPPORT: 0.2,   # 支援队友
            StrategyType.TEAM_FIGHT: 0.4 # 团战时参与
        }


class SupportStrategy(BaseStrategy):
    """辅助策略"""

    def __init__(self):
        super().__init__("辅助策略", StrategyType.SUPPORT)
        self.weights = {
            "ally_health": 0.4,
            "ally_distance": 0.3,
            "mana": 0.2,
            "threat_level": 0.1
        }

    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估辅助策略的适用性"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        score = 0.3  # 基础分数

        # 有治疗技能时更适合辅助
        if any("heal" in skill.lower() for skill in role.skills):
            score += 0.3

        # 队友血量低时适合辅助
        low_health_allies = sum(1 for ally in game_state.roles.values()
                              if ally.id != role.id and ally.health_percentage < 0.4)
        if low_health_allies > 0:
            score += 0.4

        # 自身血量充足时适合辅助
        if status.health_percentage > 0.6:
            score += 0.2

        # 团队人数优势时适合辅助
        if situation.ally_count >= situation.enemy_count:
            score += 0.2

        return max(0.0, min(1.0, score))

    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行辅助策略"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        # 寻找需要帮助的队友
        target_ally = self._find_ally_in_need(game_state, role)

        if target_ally:
            distance = role.position.distance_to(target_ally.position)

            # 如果在治疗范围内，使用治疗技能
            if distance <= 300 and status.can_use_skills:
                heal_skill = self._find_heal_skill(role)
                if heal_skill and not self.is_on_cooldown("heal"):
                    action = Action(
                        action_type=ActionType.SKILL_SUPPORT,
                        target_id=target_ally.id,
                        skill_id=heal_skill,
                        priority=3
                    )
                    self.set_cooldown("heal", 5)
                    return StrategyResult(
                        action=action,
                        confidence=0.9,
                        reasoning=f"治疗队友 {target_ally.name}",
                        priority=3
                    )

            # 移动向需要帮助的队友
            action = Action(
                action_type=ActionType.MOVE,
                position=target_ally.position,
                priority=2
            )
            return StrategyResult(
                action=action,
                confidence=0.8,
                reasoning=f"接近需要帮助的队友 {target_ally.name}",
                priority=2
            )

        # 没有需要帮助的队友，跟随最近的队友
        nearest_ally = self._find_nearest_ally(game_state, role)
        if nearest_ally:
            action = Action(
                action_type=ActionType.MOVE,
                position=nearest_ally.position,
                priority=1
            )
            return StrategyResult(
                action=action,
                confidence=0.6,
                reasoning=f"跟随队友 {nearest_ally.name}",
                priority=1
            )

        # 默认：保持当前位置
        return StrategyResult(
            action=None,
            confidence=0.1,
            reasoning="等待队友需要帮助",
            priority=0
        )

    def _find_ally_in_need(self, game_state: GameState, role: Role) -> Optional[Role]:
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

            if score > best_score:
                best_score = score
                best_ally = ally

        return best_ally if best_score > 30 else None

    def _find_nearest_ally(self, game_state: GameState, role: Role) -> Optional[Role]:
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

    def _find_heal_skill(self, role: Role) -> Optional[str]:
        """寻找治疗技能"""
        for skill in role.skills:
            if "heal" in skill.lower() or "treat" in skill.lower():
                return skill
        return None

    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        return {
            StrategyType.OFFENSIVE: 0.5,  # 没有队友需要帮助时转为进攻
            StrategyType.DEFENSIVE: 0.4,  # 自身危险时转为防守
            StrategyType.TEAM_FIGHT: 0.6  # 团战时参与
        }


class TeamFightStrategy(BaseStrategy):
    """团战策略"""

    def __init__(self):
        super().__init__("团战策略", StrategyType.TEAM_FIGHT)
        self.weights = {
            "team_strength": 0.4,
            "enemy_strength": 0.3,
            "positioning": 0.2,
            "cooldowns": 0.1
        }

    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估团战策略的适用性"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        score = 0.2  # 基础分数

        # 双方都有较多角色时适合团战
        total_combatants = situation.ally_count + situation.enemy_count
        if total_combatants >= 6:
            score += 0.3

        # 团队血量均衡时适合团战
        if situation.average_ally_health > 0.6:
            score += 0.2

        # 自身血量和魔法充足
        if status.health_percentage > 0.5 and status.mana_percentage > 0.5:
            score += 0.2

        # 在重要目标附近（如塔、水晶）
        if self._is_near_objective(game_state, role):
            score += 0.3

        return max(0.0, min(1.0, score))

    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行团战策略"""
        situation = self.get_battle_situation(game_state, role)
        status = self.get_role_status(game_state, role)

        # 寻找集火目标
        target = self._find_priority_target(game_state, role)

        if target:
            distance = role.position.distance_to(target.position)

            # 优先使用技能
            if status.can_use_skills and not self.is_on_cooldown("ultimate"):
                ultimate_skill = self._find_ultimate_skill(role)
                if ultimate_skill:
                    action = Action(
                        action_type=ActionType.SKILL_ATTACK,
                        target_id=target.id,
                        skill_id=ultimate_skill,
                        priority=5
                    )
                    self.set_cooldown("ultimate", 10)
                    return StrategyResult(
                        action=action,
                        confidence=0.95,
                        reasoning=f"团战中使用终极技能攻击 {target.name}",
                        priority=5
                    )

            # 普通攻击
            if distance <= role.attack_range:
                action = Action(
                    action_type=ActionType.ATTACK,
                    target_id=target.id,
                    priority=3
                )
                return StrategyResult(
                    action=action,
                    confidence=0.8,
                    reasoning=f"团战中集火攻击 {target.name}",
                    priority=3
                )

            # 移动到合适位置
            optimal_position = self._calculate_optimal_position(game_state, role, target)
            action = Action(
                action_type=ActionType.MOVE,
                position=optimal_position,
                priority=2
            )
            return StrategyResult(
                action=action,
                confidence=0.7,
                reasoning="移动到团战最优位置",
                priority=2
            )

        # 没有明确目标，向队友靠拢
        allies_center = self._calculate_allies_center(game_state, role)
        action = Action(
            action_type=ActionType.MOVE,
            position=allies_center,
            priority=1
        )
        return StrategyResult(
            action=action,
            confidence=0.5,
            reasoning="向队友集结准备团战",
            priority=1
        )

    def _find_priority_target(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找优先攻击目标"""
        best_target = None
        best_score = -1

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            score = 0
            # 血量低的优先
            score += (1 - enemy.health_percentage) * 50

            # 威胁高的优先
            score += enemy.attack_damage * 2

            # 脆皮优先
            if enemy.defense < role.defense:
                score += 20

            # 距离适中的优先
            distance = role.position.distance_to(enemy.position)
            if 200 <= distance <= 600:
                score += 30

            if score > best_score:
                best_score = score
                best_target = enemy

        return best_target

    def _find_ultimate_skill(self, role: Role) -> Optional[str]:
        """寻找终极技能"""
        for skill in role.skills:
            if any(word in skill.lower() for word in ["ultimate", "ulti", "nova", "blast"]):
                return skill
        return None

    def _calculate_optimal_position(self, game_state: GameState, role: Role, target: Role) -> Position:
        """计算最优团战位置"""
        # 简化实现：在攻击范围内保持移动
        angle = random.uniform(0, 2 * 3.14159)
        optimal_distance = role.attack_range * 0.8

        new_x = target.position.x + optimal_distance * 0.7 * (1 if random.random() > 0.5 else -1)
        new_y = target.position.y + optimal_distance * 0.7 * (1 if random.random() > 0.5 else -1)

        # 确保不超出地图边界
        new_x = max(0, min(game_state.map_width, new_x))
        new_y = max(0, min(game_state.map_height, new_y))

        return Position(new_x, new_y)

    def _calculate_allies_center(self, game_state: GameState, role: Role) -> Position:
        """计算队友中心位置"""
        allies = [ally for ally in game_state.roles.values()
                 if ally.id != role.id and ally.is_alive]

        if allies:
            center_x = sum(ally.position.x for ally in allies) / len(allies)
            center_y = sum(ally.position.y for ally in allies) / len(allies)
            return Position(center_x, center_y)

        return role.position

    def _is_near_objective(self, game_state: GameState, role: Role) -> bool:
        """检查是否在重要目标附近"""
        # 简化实现：检查是否在地图中心区域
        center_x, center_y = game_state.map_width / 2, game_state.map_height / 2
        distance = ((role.position.x - center_x)**2 + (role.position.y - center_y)**2)**0.5
        return distance < 500

    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        return {
            StrategyType.OFFENSIVE: 0.4,  # 团战结束转为进攻
            StrategyType.DEFENSIVE: 0.6,  # 血量危险时转为防守
            StrategyType.SUPPORT: 0.3     # 队友需要帮助时转为辅助
        }