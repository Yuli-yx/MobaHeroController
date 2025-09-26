from typing import List, Dict, Optional, Tuple
from ..core.base import GameState, Role, Action, ActionType, Position
from ..strategies.base_strategy import StrategyResult
from .action_executor import ActionValidator
import logging


logger = logging.getLogger(__name__)


class ActionOptimizer:
    """动作优化器 - 负责优化和选择最佳动作"""

    def __init__(self):
        self.validator = ActionValidator()

    def optimize_action(self, game_state: GameState, role: Role,
                       strategy_result: StrategyResult) -> Action:
        """优化策略给出的动作"""
        if not strategy_result.action:
            # 如果没有动作，生成一个默认的防守动作
            return self._generate_default_action(game_state, role)

        original_action = strategy_result.action

        # 根据置信度决定是否优化
        if strategy_result.confidence < 0.5:
            # 低置信度时进行保守优化
            return self._conservative_optimization(game_state, role, original_action)

        # 高置信度时进行积极优化
        return self._aggressive_optimization(game_state, role, original_action)

    def optimize_multiple_actions(self, game_state: GameState, role: Role,
                                 action_candidates: List[Action]) -> Action:
        """从多个候选动作中选择最优动作"""
        if not action_candidates:
            return self._generate_default_action(game_state, role)

        best_action = None
        best_score = float('-inf')

        for action in action_candidates:
            score = self._evaluate_action_score(game_state, role, action)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action or action_candidates[0]

    def _generate_default_action(self, game_state: GameState, role: Role) -> Action:
        """生成默认动作"""
        # 寻找最近的敌人
        nearest_enemy = None
        min_distance = float('inf')

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue
            distance = role.position.distance_to(enemy.position)
            if distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy

        if nearest_enemy and min_distance < 600:
            # 敌人在附近，准备防守或攻击
            if min_distance <= role.attack_range:
                return Action(
                    action_type=ActionType.ATTACK,
                    target_id=nearest_enemy.id,
                    priority=1
                )
            else:
                # 保持距离
                safe_position = self._calculate_safe_position(game_state, role, nearest_enemy)
                return Action(
                    action_type=ActionType.MOVE,
                    position=safe_position,
                    priority=1
                )
        else:
            # 没有敌人 nearby，向地图中心移动
            center_position = Position(game_state.map_width / 2, game_state.map_height / 2)
            return Action(
                action_type=ActionType.MOVE,
                position=center_position,
                priority=1
            )

    def _conservative_optimization(self, game_state: GameState, role: Role,
                                 original_action: Action) -> Action:
        """保守优化 - 注重安全性"""
        if original_action.action_type == ActionType.ATTACK:
            # 检查攻击是否安全
            target = game_state.enemies.get(original_action.target_id)
            if target and self._is_attack_safe(game_state, role, target):
                return original_action
            else:
                # 不安全，改为移动到安全位置
                safe_position = self._find_safe_retreat_position(game_state, role)
                return Action(
                    action_type=ActionType.MOVE,
                    position=safe_position,
                    priority=original_action.priority + 1
                )

        elif original_action.action_type == ActionType.MOVE:
            # 检查移动目标是否安全
            if self._is_position_safe(game_state, role, original_action.position):
                return original_action
            else:
                # 寻找更安全的替代位置
                safe_position = self._find_safe_retreat_position(game_state, role)
                return Action(
                    action_type=ActionType.MOVE,
                    position=safe_position,
                    priority=original_action.priority + 1
                )

        # 技能动作的保守优化
        elif original_action.action_type in [ActionType.SKILL_ATTACK, ActionType.SKILL_SUPPORT]:
            # 检查是否有足够的魔法值和安全的施法位置
            if role.mana_percentage < 0.5:
                # 魔法值不足，改为普通攻击或移动
                return self._generate_default_action(game_state, role)
            else:
                # 降低技能使用优先级
                optimized_action = Action(**original_action.__dict__)
                optimized_action.priority = max(1, original_action.priority - 1)
                return optimized_action

        return original_action

    def _aggressive_optimization(self, game_state: GameState, role: Role,
                                original_action: Action) -> Action:
        """积极优化 - 追求最大收益"""
        if original_action.action_type == ActionType.ATTACK:
            # 优化攻击目标选择
            best_target = self._find_best_attack_target(game_state, role)
            if best_target and best_target.id != original_action.target_id:
                return Action(
                    action_type=ActionType.ATTACK,
                    target_id=best_target.id,
                    priority=original_action.priority + 1
                )

        elif original_action.action_type == ActionType.MOVE:
            # 优化移动路径
            optimized_position = self._optimize_move_position(game_state, role, original_action.position)
            if optimized_position != original_action.position:
                return Action(
                    action_type=ActionType.MOVE,
                    position=optimized_position,
                    priority=original_action.priority
                )

        elif original_action.action_type == ActionType.SKILL_ATTACK:
            # 检查是否可以使用更强大的技能或找到更好的目标
            if role.mana_percentage > 0.7:
                # 魔法值充足，可以更积极地使用技能
                optimized_action = Action(**original_action.__dict__)
                optimized_action.priority = original_action.priority + 1
                return optimized_action

        return original_action

    def _evaluate_action_score(self, game_state: GameState, role: Role, action: Action) -> float:
        """评估动作得分"""
        score = 0.0

        # 验证动作有效性
        is_valid, _ = self.validator.validate_action(game_state, role, action)
        if not is_valid:
            return -1000  # 无效动作得极低分

        if action.action_type == ActionType.ATTACK:
            score += self._evaluate_attack_score(game_state, role, action)
        elif action.action_type == ActionType.MOVE:
            score += self._evaluate_move_score(game_state, role, action)
        elif action.action_type == ActionType.SKILL_ATTACK:
            score += self._evaluate_skill_attack_score(game_state, role, action)
        elif action.action_type == ActionType.SKILL_SUPPORT:
            score += self._evaluate_skill_support_score(game_state, role, action)

        # 考虑优先级
        score += action.priority * 10

        return score

    def _evaluate_attack_score(self, game_state: GameState, role: Role, action: Action) -> float:
        """评估攻击动作得分"""
        target = game_state.enemies.get(action.target_id)
        if not target:
            return 0

        score = 50  # 基础分数

        # 目标血量越低得分越高
        score += (1 - target.health_percentage) * 100

        # 目标威胁越高得分越高
        score += target.attack_damage * 2

        # 自身安全考虑
        danger_level = self._calculate_position_danger(game_state, role.position)
        score -= danger_level * 50

        return score

    def _evaluate_move_score(self, game_state: GameState, role: Role, action: Action) -> float:
        """评估移动动作得分"""
        score = 30  # 基础分数

        # 安全性得分
        safety_score = self._evaluate_position_safety(game_state, action.position)
        score += safety_score * 100

        # 战术价值得分
        tactical_value = self._evaluate_position_tactical_value(game_state, role, action.position)
        score += tactical_value * 50

        return score

    def _evaluate_skill_attack_score(self, game_state: GameState, role: Role, action: Action) -> float:
        """评估技能攻击得分"""
        score = self._evaluate_attack_score(game_state, role, action) * 1.5  # 技能攻击基础得分更高

        # 考虑魔法消耗
        mana_cost = 20
        mana_ratio = mana_cost / role.max_mana if role.max_mana > 0 else 1
        score -= mana_ratio * 30

        return score

    def _evaluate_skill_support_score(self, game_state: GameState, role: Role, action: Action) -> float:
        """评估辅助技能得分"""
        target = game_state.roles.get(action.target_id)
        if not target:
            return 0

        score = 60  # 基础分数

        # 目标血量越低得分越高
        score += (1 - target.health_percentage) * 150

        # 考虑魔法消耗
        mana_cost = 30
        mana_ratio = mana_cost / role.max_mana if role.max_mana > 0 else 1
        score -= mana_ratio * 20

        return score

    def _is_attack_safe(self, game_state: GameState, role: Role, target: Role) -> bool:
        """检查攻击是否安全"""
        # 计算攻击后可能受到的反击
        nearby_enemies = [
            enemy for enemy in game_state.enemies.values()
            if enemy.is_alive and enemy.position.distance_to(role.position) <= enemy.attack_range
        ]

        if len(nearby_enemies) > 2:
            return False  # 被多个敌人包围不安全

        if role.health_percentage < 0.3 and len(nearby_enemies) > 0:
            return False  # 血量低时有敌人 nearby 不安全

        return True

    def _is_position_safe(self, game_state: GameState, role: Role, position: Position) -> bool:
        """检查位置是否安全"""
        # 计算位置的危险程度
        danger_enemies = [
            enemy for enemy in game_state.enemies.values()
            if enemy.is_alive and enemy.position.distance_to(position) <= enemy.attack_range + 100
        ]

        return len(danger_enemies) == 0

    def _calculate_safe_position(self, game_state: GameState, role: Role, enemy: Role) -> Position:
        """计算安全位置"""
        # 远离敌人的方向
        dx = role.position.x - enemy.position.x
        dy = role.position.y - enemy.position.y
        distance = (dx**2 + dy**2)**0.5

        if distance > 0:
            # 保持400-500的安全距离
            safe_distance = 450
            scale = safe_distance / distance
            new_x = role.position.x + dx * scale * 0.3
            new_y = role.position.y + dy * scale * 0.3

            # 确保不超出地图边界
            new_x = max(0, min(game_state.map_width, new_x))
            new_y = max(0, min(game_state.map_height, new_y))

            return Position(new_x, new_y)

        return role.position

    def _find_safe_retreat_position(self, game_state: GameState, role: Role) -> Position:
        """寻找安全的撤退位置"""
        # 向友方塔或基地方向撤退
        retreat_x = max(0, role.position.x - 200)
        retreat_y = max(0, role.position.y - 200)

        return Position(retreat_x, retreat_y)

    def _find_best_attack_target(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找最佳攻击目标"""
        best_target = None
        best_score = -1

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            distance = role.position.distance_to(enemy.position)
            if distance > role.attack_range * 1.5:  # 不考虑过远的目标
                continue

            score = 0
            # 血量权重
            score += (1 - enemy.health_percentage) * 100

            # 威胁权重
            score += enemy.attack_damage * 2

            # 距离权重
            score += max(0, 50 - distance / 10)

            # 击杀奖励
            if enemy.health_percentage < 0.3:
                score += 50

            if score > best_score:
                best_score = score
                best_target = enemy

        return best_target

    def _optimize_move_position(self, game_state: GameState, role: Role,
                               target_position: Position) -> Position:
        """优化移动位置"""
        # 简化实现：考虑避开危险区域
        optimized_x = target_position.x
        optimized_y = target_position.y

        # 检查是否有敌人 nearby
        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            distance_to_enemy = ((target_position.x - enemy.position.x)**2 +
                               (target_position.y - enemy.position.y)**2)**0.5

            if distance_to_enemy < enemy.attack_range:
                # 太靠近敌人，调整位置
                avoid_range = enemy.attack_range + 50
                dx = target_position.x - enemy.position.x
                dy = target_position.y - enemy.position.y

                if distance_to_enemy > 0:
                    scale = avoid_range / distance_to_enemy
                    optimized_x = enemy.position.x + dx * scale
                    optimized_y = enemy.position.y + dy * scale

        # 确保不超出地图边界
        optimized_x = max(0, min(game_state.map_width, optimized_x))
        optimized_y = max(0, min(game_state.map_height, optimized_y))

        return Position(optimized_x, optimized_y)

    def _evaluate_position_safety(self, game_state: GameState, position: Position) -> float:
        """评估位置安全性 (0-1)"""
        danger_score = 0

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            distance = ((position.x - enemy.position.x)**2 + (position.y - enemy.position.y)**2)**0.5
            if distance <= enemy.attack_range:
                danger_score += enemy.attack_damage / max(distance, 1)

        # 归一化到0-1范围
        return max(0, 1 - danger_score / 100)

    def _evaluate_position_tactical_value(self, game_state: GameState, role: Role,
                                         position: Position) -> float:
        """评估位置战术价值 (0-1)"""
        value = 0

        # 靠近队友增加价值
        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            distance = ((position.x - ally.position.x)**2 + (position.y - ally.position.y)**2)**0.5
            if distance < 300:
                value += 0.2

        # 靠近地图中心增加价值
        center_x, center_y = game_state.map_width / 2, game_state.map_height / 2
        distance_to_center = ((position.x - center_x)**2 + (position.y - center_y)**2)**0.5
        if distance_to_center < 500:
            value += 0.3

        return min(1, value)

    def _calculate_position_danger(self, game_state: GameState, position: Position) -> float:
        """计算位置危险程度"""
        danger = 0

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            distance = ((position.x - enemy.position.x)**2 + (position.y - enemy.position.y)**2)**0.5
            if distance <= enemy.attack_range:
                danger += enemy.attack_damage / max(distance, 1)

        return danger