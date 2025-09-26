import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from ..core.base import GameState, Role, Action, ActionType, Position
from ..strategies.base_strategy import StrategyType, StrategyResult
from ..sensors import SituationAwareness, ThreatLevel


logger = logging.getLogger(__name__)


class RoleType(Enum):
    TANK = "tank"          # 坦克 - 高血量，高防御
    ASSASSIN = "assassin"  # 刺客 - 高爆发，低生存
    MAGE = "mage"         # 法师 - 技能伤害高
    MARKSMAN = "marksman" # 射手 - 持续输出
    SUPPORT = "support"    # 辅助 - 治疗，增益
    WARRIOR = "warrior"    # 战士 - 平衡型


@dataclass
class RoleDirective:
    """角色指令"""
    primary_target: Optional[str]  # 主要目标ID
    secondary_target: Optional[str]  # 次要目标ID
    position_priority: List[Position]  # 优先位置列表
    engagement_rules: Dict[str, Any]  # 交战规则
    coordination_requests: List[str]  # 协同请求的角色ID列表


class RoleCoordinator:
    """角色协调器 - 负责单个角色的决策协调"""

    def __init__(self, role_id: str):
        self.role_id = role_id
        self.situation_awareness = SituationAwareness()
        self.directive: Optional[RoleDirective] = None
        self.personal_history: List[Tuple[int, str, Action]] = []  # (turn, situation, action)
        self.preferred_targets: Dict[str, float] = {}  # 目标偏好分数
        self.avoidance_list: List[str] = []  # 回避的目标列表
        self.last_strategy_type: Optional[StrategyType] = None
        self.strategy_consistency = 0  # 策略连续性计数器

    def update_directive(self, directive: RoleDirective) -> None:
        """更新角色指令"""
        self.directive = directive
        logger.info(f"角色 {self.role_id} 收到新指令")

    def get_coordinated_action(self, game_state: GameState, role: Role,
                             strategy_result: StrategyResult,
                             current_turn: int) -> Action:
        """获取协调后的动作"""
        # 记录个人历史
        self._record_personal_history(current_turn, strategy_result.reasoning, strategy_result.action)

        # 分析当前情况
        battle_situation = self.situation_awareness.analyze_battle_situation(game_state, role)
        role_status = self.situation_awareness.analyze_role_status(game_state, role)

        # 检查是否需要紧急反应
        emergency_action = self._check_emergency_response(game_state, role, battle_situation, role_status)
        if emergency_action:
            logger.info(f"角色 {role.name} 执行紧急动作")
            return emergency_action

        # 获取基础动作
        base_action = strategy_result.action

        # 如果有指令，根据指令调整动作
        if self.directive:
            coordinated_action = self._apply_directive(game_state, role, base_action, battle_situation)
        else:
            coordinated_action = self._apply_personal_preferences(game_state, role, base_action, battle_situation)

        # 更新策略连续性
        self._update_strategy_consistency(strategy_result)

        return coordinated_action or base_action

    def should_request_support(self, game_state: GameState, role: Role) -> bool:
        """判断是否应该请求支援"""
        battle_situation = self.situation_awareness.analyze_battle_situation(game_state, role)
        role_status = self.situation_awareness.analyze_role_status(game_state, role)

        # 血量过低且被包围
        if (role_status.is_low_health and
            battle_situation.enemy_count > battle_situation.ally_count + 1):
            return True

        # 面对高威胁目标
        if battle_situation.threat_level == ThreatLevel.CRITICAL:
            return True

        # 发现高价值目标但无法单独处理
        high_value_target = self._find_high_value_target(game_state, role)
        if high_value_target and not self._can_handle_target_alone(role, high_value_target):
            return True

        return False

    def get_support_request_info(self, game_state: GameState, role: Role) -> Dict[str, Any]:
        """获取支援请求信息"""
        battle_situation = self.situation_awareness.analyze_battle_situation(game_state, role)

        return {
            "role_id": self.role_id,
            "position": {"x": role.position.x, "y": role.position.y},
            "health_percentage": role.health_percentage,
            "threat_level": battle_situation.threat_level.value,
            "enemy_count": battle_situation.enemy_count,
            "ally_count": battle_situation.ally_count,
            "urgency": self._calculate_urgency(game_state, role),
            "preferred_support_roles": self._get_preferred_support_types(),
            "reason": self._get_support_request_reason(game_state, role)
        }

    def evaluate_target_opportunity(self, game_state: GameState, role: Role,
                                  target_id: str) -> float:
        """评估目标机会 (0-1)"""
        target = game_state.enemies.get(target_id)
        if not target or not target.is_alive:
            return 0.0

        score = 0.0

        # 基础目标价值
        score += self._calculate_base_target_value(role, target)

        # 位置优势
        score += self._calculate_positional_advantage(role, target) * 0.3

        # 击杀概率
        kill_probability = self._calculate_kill_probability(role, target)
        score += kill_probability * 0.4

        # 风险评估
        risk_factor = self._calculate_engagement_risk(game_state, role, target)
        score -= risk_factor * 0.3

        return max(0.0, min(1.0, score))

    def get_preferred_engagement_range(self, role: Role) -> Tuple[float, float]:
        """获取偏好的交战距离范围"""
        role_type = self._classify_role(role)

        if role_type == RoleType.MARKSMAN:
            return (role.attack_range, role.attack_range + 100)
        elif role_type == RoleType.MAGE:
            return (200, 400)
        elif role_type == RoleType.ASSASSIN:
            return (0, 200)
        elif role_type == RoleType.TANK:
            return (0, 300)
        elif role_type == RoleType.SUPPORT:
            return (300, 500)
        else:  # WARRIOR
            return (0, role.attack_range + 50)

    def update_target_preferences(self, game_state: GameState, role: Role) -> None:
        """更新目标偏好"""
        # 根据战斗历史更新偏好
        for target_id in game_state.enemies.keys():
            preference = self.preferred_targets.get(target_id, 0.5)

            # 如果成功击杀过该目标，增加偏好
            if self._has_killed_target_before(target_id):
                preference += 0.1

            # 如果被该目标击杀过，减少偏好
            if self._was_killed_by_target_before(target_id):
                preference -= 0.2

            # 考虑目标类型克制
            target = game_state.enemies[target_id]
            target_type = self._classify_role(target)
            my_role_type = self._classify_role(role)

            matchup_score = self._get_matchup_score(my_role_type, target_type)
            preference += matchup_score * 0.1

            self.preferred_targets[target_id] = max(0.1, min(1.0, preference))

    def _check_emergency_response(self, game_state: GameState, role: Role,
                                battle_situation: Any, role_status: Any) -> Optional[Action]:
        """检查紧急响应"""
        # 血量极低
        if role.health_percentage < 0.2:
            return self._create_emergency_retreat_action(game_state, role)

        # 被多个敌人包围
        if battle_situation.enemy_count > 2 and battle_situation.ally_count == 0:
            return self._create_emergency_escape_action(game_state, role)

        # 即将被击杀
        if self._is_about_to_be_killed(game_state, role):
            return self._create_desperate_action(game_state, role)

        return None

    def _apply_directive(self, game_state: GameState, role: Role, base_action: Action,
                        battle_situation: Any) -> Action:
        """应用指令调整动作"""
        if not self.directive:
            return base_action

        # 检查主要目标
        if self.directive.primary_target:
            target = game_state.enemies.get(self.directive.primary_target)
            if target and target.is_alive:
                return self._create_target_focus_action(role, target)

        # 检查位置优先级
        if self.directive.position_priority:
            best_position = self._select_best_position(role, self.directive.position_priority)
            distance = role.position.distance_to(best_position)

            if distance > 100:  # 离目标位置较远
                return Action(
                    action_type=ActionType.MOVE,
                    position=best_position,
                    priority=base_action.priority + 1
                )

        # 应用交战规则
        if self.directive.engagement_rules:
            return self._apply_engagement_rules(role, base_action, self.directive.engagement_rules)

        return base_action

    def _apply_personal_preferences(self, game_state: GameState, role: Role,
                                 base_action: Action, battle_situation: Any) -> Action:
        """应用个人偏好"""
        # 根据历史经验调整动作
        if base_action.target_id:
            target_preference = self.preferred_targets.get(base_action.target_id, 0.5)
            if target_preference < 0.3:  # 不喜欢这个目标
                # 寻找替代目标
                alternative_target = self._find_preferred_target(game_state, role)
                if alternative_target:
                    return Action(
                        action_type=base_action.action_type,
                        target_id=alternative_target.id,
                        priority=base_action.priority
                    )

        # 调整位置偏好
        if base_action.position:
            preferred_range = self.get_preferred_engagement_range(role)
            # 检查当前位置是否符合偏好
            current_situation = self.situation_awareness.analyze_role_status(game_state, role)
            if current_situation.nearest_enemy:
                distance_to_enemy = role.position.distance_to(current_situation.nearest_enemy.position)
                if distance_to_enemy < preferred_range[0] or distance_to_enemy > preferred_range[1]:
                    # 调整到偏好距离
                    return self._create_position_adjustment_action(role, current_situation.nearest_enemy, preferred_range)

        return base_action

    def _record_personal_history(self, turn: int, situation: str, action: Optional[Action]) -> None:
        """记录个人历史"""
        self.personal_history.append((turn, situation, action))

        # 限制历史长度
        if len(self.personal_history) > 50:
            self.personal_history = self.personal_history[-30:]

    def _update_strategy_consistency(self, strategy_result: StrategyResult) -> None:
        """更新策略连续性"""
        current_type = strategy_result.reasoning  # 简化处理

        if current_type == self.last_strategy_type:
            self.strategy_consistency += 1
        else:
            self.strategy_consistency = 1
            self.last_strategy_type = current_type

    def _calculate_urgency(self, game_state: GameState, role: Role) -> float:
        """计算紧急程度 (0-1)"""
        battle_situation = self.situation_awareness.analyze_battle_situation(game_state, role)
        role_status = self.situation_awareness.analyze_role_status(game_state, role)

        urgency = 0.0

        # 血量因素
        if role_status.is_low_health:
            urgency += 0.4

        # 威胁等级
        if battle_situation.threat_level == ThreatLevel.CRITICAL:
            urgency += 0.4
        elif battle_situation.threat_level == ThreatLevel.HIGH:
            urgency += 0.2

        # 数量劣势
        if battle_situation.enemy_count > battle_situation.ally_count + 1:
            urgency += 0.3

        return min(1.0, urgency)

    def _get_preferred_support_types(self) -> List[str]:
        """获取偏好的支援类型"""
        return ["tank", "support", "mage"]  # 简化实现

    def _get_support_request_reason(self, game_state: GameState, role: Role) -> str:
        """获取支援请求原因"""
        battle_situation = self.situation_awareness.analyze_battle_situation(game_state, role)
        role_status = self.situation_awareness.analyze_role_status(game_state, role)

        if role_status.is_low_health:
            return "血量过低需要支援"
        elif battle_situation.threat_level == ThreatLevel.CRITICAL:
            return "面临致命威胁"
        elif battle_situation.enemy_count > battle_situation.ally_count + 1:
            return "数量劣势需要支援"
        else:
            return "战术需要协同"

    def _find_high_value_target(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找高价值目标"""
        best_target = None
        best_value = 0

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            value = self._calculate_base_target_value(role, enemy)
            if value > best_value:
                best_value = value
                best_target = enemy

        return best_target if best_value > 0.7 else None

    def _can_handle_target_alone(self, role: Role, target: Role) -> bool:
        """判断是否能单独处理目标"""
        # 简化实现：比较战斗力
        my_power = role.attack_damage + role.defense + role.health * 0.1
        target_power = target.attack_damage + target.defense + target.health * 0.1

        return my_power >= target_power * 0.8  # 可以处理80%战斗力的目标

    def _calculate_base_target_value(self, role: Role, target: Role) -> float:
        """计算基础目标价值"""
        value = 0.5

        # 血量越低价值越高
        value += (1 - target.health_percentage) * 0.3

        # 威胁越高价值越高
        threat_score = (target.attack_damage + target.defense) / 200
        value += min(0.3, threat_score)

        return min(1.0, value)

    def _calculate_positional_advantage(self, role: Role, target: Role) -> float:
        """计算位置优势"""
        distance = role.position.distance_to(target.position)

        # 在攻击范围内最有利
        if distance <= role.attack_range:
            return 1.0
        elif distance <= role.attack_range + 100:
            return 0.8
        elif distance <= 500:
            return 0.5
        else:
            return 0.2

    def _calculate_kill_probability(self, role: Role, target: Role) -> float:
        """计算击杀概率"""
        # 简化的击杀概率计算
        my_damage_potential = role.attack_damage * (1 + len(role.skills) * 0.5)
        target_survivability = target.health + target.defense * 10

        if my_damage_potential >= target_survivability:
            return 0.8
        elif my_damage_potential >= target_survivability * 0.7:
            return 0.6
        elif my_damage_potential >= target_survivability * 0.5:
            return 0.4
        else:
            return 0.2

    def _calculate_engagement_risk(self, game_state: GameState, role: Role, target: Role) -> float:
        """计算交战风险"""
        risk = 0.0

        # 目标的反击能力
        risk += target.attack_damage / 100

        # 附近的其他敌人
        nearby_enemies = 0
        for enemy in game_state.enemies.values():
            if enemy.id != target.id and enemy.is_alive:
                if enemy.position.distance_to(target.position) < 300:
                    nearby_enemies += 1

        risk += nearby_enemies * 0.2

        return min(1.0, risk)

    def _classify_role(self, role: Role) -> RoleType:
        """分类角色类型"""
        # 简化的角色分类逻辑
        if role.defense > 80:
            return RoleType.TANK
        elif role.attack_damage > 100 and role.health < 80:
            return RoleType.ASSASSIN
        elif len(role.skills) > 2:
            return RoleType.MAGE
        elif role.attack_range > 150:
            return RoleType.MARKSMAN
        elif role.attack_damage < 60:
            return RoleType.SUPPORT
        else:
            return RoleType.WARRIOR

    def _get_matchup_score(self, my_type: RoleType, target_type: RoleType) -> float:
        """获取对抗分数"""
        # 简化的克制关系
        matchups = {
            (RoleType.ASSASSIN, RoleType.MAGE): 0.3,
            (RoleType.MAGE, RoleType.TANK): 0.2,
            (RoleType.MARKSMAN, RoleType.TANK): 0.1,
            (RoleType.WARRIOR, RoleType.ASSASSIN): 0.2,
        }

        return matchups.get((my_type, target_type), 0.0)

    def _has_killed_target_before(self, target_id: str) -> bool:
        """检查是否曾经击杀过目标"""
        # 简化实现
        return False

    def _was_killed_by_target_before(self, target_id: str) -> bool:
        """检查是否曾经被目标击杀"""
        # 简化实现
        return False

    def _create_emergency_retreat_action(self, game_state: GameState, role: Role) -> Action:
        """创建紧急撤退动作"""
        # 向基地方向撤退
        retreat_position = Position(
            max(0, role.position.x - 200),
            max(0, role.position.y - 200)
        )

        return Action(
            action_type=ActionType.MOVE,
            position=retreat_position,
            priority=10
        )

    def _create_emergency_escape_action(self, game_state: GameState, role: Role) -> Action:
        """创建紧急逃生动作"""
        # 随机方向逃跑
        import random
        escape_x = role.position.x + random.uniform(-300, 300)
        escape_y = role.position.y + random.uniform(-300, 300)

        # 确保在地图范围内
        escape_x = max(0, min(game_state.map_width, escape_x))
        escape_y = max(0, min(game_state.map_height, escape_y))

        return Action(
            action_type=ActionType.MOVE,
            position=Position(escape_x, escape_y),
            priority=9
        )

    def _create_desperate_action(self, game_state: GameState, role: Role) -> Action:
        """创建拼命动作"""
        # 寻找最近的敌人进行最后一击
        nearest_enemy = self._find_nearest_enemy(game_state, role)
        if nearest_enemy:
            return Action(
                action_type=ActionType.ATTACK,
                target_id=nearest_enemy.id,
                priority=8
            )

        # 默认：原地不动
        return Action(
            action_type=ActionType.MOVE,
            position=role.position,
            priority=1
        )

    def _find_nearest_enemy(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找最近的敌人"""
        nearest_enemy = None
        min_distance = float('inf')

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            distance = role.position.distance_to(enemy.position)
            if distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy

        return nearest_enemy

    def _create_target_focus_action(self, role: Role, target: Role) -> Action:
        """创建目标专注动作"""
        distance = role.position.distance_to(target.position)

        if distance <= role.attack_range:
            return Action(
                action_type=ActionType.ATTACK,
                target_id=target.id,
                priority=5
            )
        else:
            return Action(
                action_type=ActionType.MOVE,
                position=target.position,
                priority=4
            )

    def _select_best_position(self, role: Role, positions: List[Position]) -> Position:
        """选择最佳位置"""
        # 选择最近的位置
        best_position = positions[0]
        min_distance = float('inf')

        for pos in positions:
            distance = role.position.distance_to(pos)
            if distance < min_distance:
                min_distance = distance
                best_position = pos

        return best_position

    def _apply_engagement_rules(self, role: Role, base_action: Action,
                              rules: Dict[str, Any]) -> Action:
        """应用交战规则"""
        # 简化实现
        if rules.get("cautious", False) and base_action.action_type == ActionType.ATTACK:
            # 谨慎模式，降低优先级
            modified_action = Action(**base_action.__dict__)
            modified_action.priority = max(1, base_action.priority - 1)
            return modified_action

        return base_action

    def _find_preferred_target(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找偏好的目标"""
        best_target = None
        best_preference = 0

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            preference = self.preferred_targets.get(enemy.id, 0.5)
            if preference > best_preference:
                best_preference = preference
                best_target = enemy

        return best_target if best_preference > 0.5 else None

    def _create_position_adjustment_action(self, role: Role, enemy: Role,
                                         preferred_range: Tuple[float, float]) -> Action:
        """创建位置调整动作"""
        current_distance = role.position.distance_to(enemy.position)

        # 计算最佳距离
        optimal_distance = (preferred_range[0] + preferred_range[1]) / 2

        if current_distance < optimal_distance:
            # 太近了，需要拉远距离
            dx = role.position.x - enemy.position.x
            dy = role.position.y - enemy.position.y
            if current_distance > 0:
                scale = (optimal_distance - current_distance) / current_distance
                new_x = role.position.x + dx * scale
                new_y = role.position.y + dy * scale
                return Action(
                    action_type=ActionType.MOVE,
                    position=Position(new_x, new_y),
                    priority=3
                )

        return Action(
            action_type=ActionType.MOVE,
            position=role.position,
            priority=1
        )

    def _is_about_to_be_killed(self, game_state: GameState, role: Role) -> bool:
        """判断是否即将被击杀"""
        # 简化实现：血量很低且有敌人 nearby
        if role.health_percentage < 0.15:
            for enemy in game_state.enemies.values():
                if enemy.is_alive and role.position.distance_to(enemy.position) < enemy.attack_range:
                    return True
        return False

    def get_personal_summary(self) -> Dict[str, Any]:
        """获取个人状态摘要"""
        return {
            "role_id": self.role_id,
            "strategy_consistency": self.strategy_consistency,
            "last_strategy_type": self.last_strategy_type.value if self.last_strategy_type else None,
            "preferred_targets": len(self.preferred_targets),
            "avoidance_list": len(self.avoidance_list),
            "has_directive": self.directive is not None,
            "history_length": len(self.personal_history)
        }