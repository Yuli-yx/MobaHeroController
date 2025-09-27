import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from ..core.base import GameState, Role, Action, ActionType, Position
from ..strategies.base_strategy import StrategyResult
from ..pathfinding import PathFinder


logger = logging.getLogger(__name__)


class ExecutionResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    INVALID_TARGET = "invalid_target"
    OUT_OF_RANGE = "out_of_range"
    INSUFFICIENT_MANA = "insufficient_mana"
    COOLDOWN = "cooldown"
    INVALID_POSITION = "invalid_position"


@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    result_type: ExecutionResult
    message: str
    actual_action: Optional[Action] = None
    damage_dealt: float = 0
    mana_cost: float = 0
    cooldown_remaining: int = 0


class ActionValidator:
    """动作验证器"""

    @staticmethod
    def validate_action(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证动作是否有效"""
        if not role.is_alive:
            return False, "角色已死亡"

        if action.action_type == ActionType.ATTACK:
            return ActionValidator._validate_attack(game_state, role, action)
        elif action.action_type == ActionType.MOVE:
            return ActionValidator._validate_move(game_state, role, action)
        elif action.action_type == ActionType.SKILL_ATTACK:
            return ActionValidator._validate_skill_attack(game_state, role, action)
        elif action.action_type == ActionType.SKILL_SUPPORT:
            return ActionValidator._validate_skill_support(game_state, role, action)
        elif action.action_type == ActionType.SKILL_MOVE:
            return ActionValidator._validate_skill_move(game_state, role, action)
        elif action.action_type == ActionType.SKILL_POSITION:
            return ActionValidator._validate_skill_position(game_state, role, action)
        else:
            return False, f"未知的动作类型: {action.action_type}"

    @staticmethod
    def _check_attack_path_obstacles(game_state: GameState, role: Role, target: Role) -> Tuple[bool, str]:
        """检查攻击路径上是否有障碍物"""
        try:
            # 创建寻路器实例
            from ..pathfinding import PathFinder
            path_finder = PathFinder(game_state)

            # 获取可能的障碍物位置（塔、水晶、小兵等）
            obstacles = []

            # 添加塔作为障碍物
            for tower in game_state.towers:
                if 'position' in tower:
                    tower_pos = Position(tower['position']['x'], tower['position']['y'])
                    obstacles.append(tower_pos)

            # 添加水晶作为障碍物
            for crystal in game_state.crystals:
                if 'position' in crystal:
                    crystal_pos = Position(crystal['position']['x'], crystal['position']['y'])
                    obstacles.append(crystal_pos)

            # 添加小兵作为障碍物（排除目标本身）
            for minion in game_state.minions:
                if 'position' in minion:
                    minion_pos = Position(minion['position']['x'], minion['position']['y'])
                    # 排除与目标位置重叠的小兵
                    if (abs(minion_pos.x - target.position.x) > 1.0 or
                        abs(minion_pos.y - target.position.y) > 1.0):
                        obstacles.append(minion_pos)

            # 检查从攻击者到目标是否有直线路径
            # 使用简化的直线路径检查，采样路径上的几个点
            distance = role.position.distance_to(target.position)
            if distance > 0:
                # 每隔一定距离检查一个点
                check_interval = min(2.0, distance / 10)  # 最小间隔2.0，最多检查10个点
                num_checks = max(3, int(distance / check_interval))

                for i in range(1, num_checks):
                    # 计算检查点的位置
                    ratio = i / num_checks
                    check_x = role.position.x + (target.position.x - role.position.x) * ratio
                    check_y = role.position.y + (target.position.y - role.position.y) * ratio
                    check_pos = Position(check_x, check_y)

                    # 跳过太接近攻击者或目标的检查点
                    dist_to_attacker = check_pos.distance_to(role.position)
                    dist_to_target = check_pos.distance_to(target.position)
                    if dist_to_attacker < 1.5 or dist_to_target < 1.5:
                        continue

                    # 检查该位置是否有障碍物（排除攻击者和目标）
                    if path_finder.is_position_blocked(check_pos, obstacles, role):
                        return False, f"攻击路径被阻挡 (位置: ({check_x:.1f}, {check_y:.1f}))"

            return True, "攻击路径畅通"

        except Exception as e:
            # 如果检查过程中出现错误，默认认为路径通畅（避免阻塞所有攻击）
            logger.warning(f"检查攻击路径障碍物时发生错误: {e}")
            return True, "路径检查默认通过"

    @staticmethod
    def _validate_attack(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证攻击动作"""
        if not action.target_id:
            return False, "攻击动作需要目标ID"

        if action.target_id not in game_state.enemies:
            return False, f"目标 {action.target_id} 不存在或不是敌人"

        target = game_state.enemies[action.target_id]
        if not target.is_alive:
            return False, f"目标 {target.name} 已死亡"

        distance = role.position.distance_to(target.position)
        if distance > role.attack_range:
            return False, f"目标超出攻击范围 (距离: {distance:.1f}, 范围: {role.attack_range})"

        # 检查攻击路径上是否有障碍物
        path_clear, path_message = ActionValidator._check_attack_path_obstacles(game_state, role, target)
        if not path_clear:
            return False, path_message

        return True, "验证通过"

    @staticmethod
    def _validate_move(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证移动动作"""
        if not action.position:
            return False, "移动动作需要目标位置"

        # 检查位置是否在地图范围内
        if (action.position.x < 0 or action.position.x > game_state.map_width or
            action.position.y < 0 or action.position.y > game_state.map_height):
            return False, f"目标位置超出地图范围"

        return True, "验证通过"

    @staticmethod
    def _validate_skill_attack(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证技能攻击动作"""
        if not action.target_id:
            return False, "技能攻击需要目标ID"

        if not action.skill_id:
            return False, "技能攻击需要技能ID"

        if action.skill_id not in role.skills:
            return False, f"角色没有技能 {action.skill_id}"

        target = game_state.enemies.get(action.target_id)
        if not target or not target.is_alive:
            return False, "技能攻击目标无效"

        # 检查魔法值（简化处理）
        if role.mana < 20:  # 假设技能需要20魔法值
            return False, "魔法值不足"

        # 检查技能攻击路径上是否有障碍物（技能通常也需要视线）
        path_clear, path_message = ActionValidator._check_attack_path_obstacles(game_state, role, target)
        if not path_clear:
            return False, f"技能{path_message}"

        return True, "验证通过"

    @staticmethod
    def _validate_skill_support(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证辅助技能动作"""
        if not action.target_id:
            return False, "辅助技能需要目标ID"

        if not action.skill_id:
            return False, "辅助技能需要技能ID"

        if action.skill_id not in role.skills:
            return False, f"角色没有技能 {action.skill_id}"

        target = game_state.roles.get(action.target_id)
        if not target or not target.is_alive:
            return False, "辅助技能目标无效"

        # 检查魔法值
        if role.mana < 30:  # 假设辅助技能需要30魔法值
            return False, "魔法值不足"

        return True, "验证通过"

    @staticmethod
    def _validate_skill_move(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证移动技能动作"""
        if not action.position:
            return False, "移动技能需要目标位置"

        if not action.skill_id:
            return False, "移动技能需要技能ID"

        if action.skill_id not in role.skills:
            return False, f"角色没有技能 {action.skill_id}"

        # 检查魔法值
        if role.mana < 40:  # 假设移动技能需要40魔法值
            return False, "魔法值不足"

        return True, "验证通过"

    @staticmethod
    def _validate_skill_position(game_state: GameState, role: Role, action: Action) -> Tuple[bool, str]:
        """验证位置技能动作"""
        if not action.position:
            return False, "位置技能需要目标位置"

        if not action.skill_id:
            return False, "位置技能需要技能ID"

        if action.skill_id not in role.skills:
            return False, f"角色没有技能 {action.skill_id}"

        # 检查是否可以使用技能（钻石和冷却）
        if not role.can_use_skill(action.skill_id):
            # 检查具体原因
            if role.get_skill_cooldown(action.skill_id) > 0:
                return False, f"技能冷却中，剩余 {role.get_skill_cooldown(action.skill_id)} 回合"
            elif role.diamonds < 5:
                return False, "钻石不足，需要5钻石"
            else:
                return False, "技能无法使用"

        return True, "验证通过"


class ActionExecutor:
    """动作执行器"""

    def __init__(self, game_state: GameState):
        self.validator = ActionValidator()
        self.execution_history: List[Tuple[int, str, ActionResult]] = []
        self.skill_cooldowns: Dict[str, Dict[str, int]] = {}  # role_id -> skill_id -> cooldown
        self.path_finder = PathFinder(game_state)

    def execute_action(self, game_state: GameState, role: Role, action: Action,
                      current_turn: int) -> ActionResult:
        """执行动作"""
        # 验证动作
        is_valid, message = self.validator.validate_action(game_state, role, action)
        if not is_valid:
            result = ActionResult(
                success=False,
                result_type=ExecutionResult.INVALID_TARGET if "目标" in message else ExecutionResult.FAILED,
                message=message
            )
            self.execution_history.append((current_turn, role.id, result))
            return result

        # 检查技能冷却
        if action.action_type in [ActionType.SKILL_ATTACK, ActionType.SKILL_SUPPORT, ActionType.SKILL_MOVE]:
            cooldown_result = self._check_skill_cooldown(role, action.skill_id)
            if cooldown_result:
                result = ActionResult(
                    success=False,
                    result_type=ExecutionResult.COOLDOWN,
                    message=cooldown_result,
                    cooldown_remaining=self.skill_cooldowns.get(role.id, {}).get(action.skill_id, 0)
                )
                self.execution_history.append((current_turn, role.id, result))
                return result

        # 执行具体动作
        try:
            if action.action_type == ActionType.ATTACK:
                result = self._execute_attack(game_state, role, action)
            elif action.action_type == ActionType.MOVE:
                result = self._execute_move(game_state, role, action)
            elif action.action_type == ActionType.SKILL_ATTACK:
                result = self._execute_skill_attack(game_state, role, action)
            elif action.action_type == ActionType.SKILL_SUPPORT:
                result = self._execute_skill_support(game_state, role, action)
            elif action.action_type == ActionType.SKILL_MOVE:
                result = self._execute_skill_move(game_state, role, action)
            elif action.action_type == ActionType.SKILL_POSITION:
                result = self._execute_skill_position(game_state, role, action)
            else:
                result = ActionResult(
                    success=False,
                    result_type=ExecutionResult.FAILED,
                    message=f"不支持的动作类型: {action.action_type}"
                )
        except Exception as e:
            logger.error(f"执行动作时发生错误: {e}")
            result = ActionResult(
                success=False,
                result_type=ExecutionResult.FAILED,
                message=f"执行错误: {str(e)}"
            )

        self.execution_history.append((current_turn, role.id, result))
        return result

    def _execute_attack(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行攻击动作"""
        target = game_state.enemies[action.target_id]

        # 计算伤害
        base_damage = role.attack_damage
        # 简化的伤害计算（不考虑护甲等）
        actual_damage = base_damage * (1 - target.defense * 0.01)

        # 更新目标血量
        target.health = max(0, target.health - actual_damage)
        if target.health == 0:
            target.is_alive = False

        return ActionResult(
            success=True,
            result_type=ExecutionResult.SUCCESS,
            message=f"{role.name} 攻击 {target.name}, 造成 {actual_damage:.1f} 点伤害",
            actual_action=action,
            damage_dealt=actual_damage
        )

    def _execute_move(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行移动动作，使用A*算法和切比雪夫距离"""
        # 更新路径查找器的游戏状态
        self.path_finder.game_state = game_state

        # 获取在移动距离内的下一个位置
        max_move_distance = role.move_speed
        new_position = self.path_finder.get_next_move_position(
            role, action.position, max_move_distance
        )

        # 检查是否实际移动了
        if new_position.distance_to(role.position) < 0.1:
            return ActionResult(
                success=True,
                result_type=ExecutionResult.SUCCESS,
                message=f"{role.name} 无法移动到目标位置或已在目标位置 (目标:{action.position.x:.1f},{action.position.y:.1f})",
                actual_action=action
            )

        # 更新角色位置
        old_position = role.position
        role.position = new_position

        return ActionResult(
            success=True,
            result_type=ExecutionResult.SUCCESS,
            message=f"{role.name} 使用A*算法移动到位置 ({new_position.x:.1f}, {new_position.y:.1f})",
            actual_action=action
        )

    def _execute_skill_attack(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行技能攻击"""
        target = game_state.enemies[action.target_id]

        # 使用技能系统
        from ..skills import SkillSystem
        success, message = SkillSystem.use_skill(role, action.skill_id, game_state, target=target)

        if success:
            return ActionResult(
                success=True,
                result_type=ExecutionResult.SUCCESS,
                message=message,
                actual_action=action
            )
        else:
            return ActionResult(
                success=False,
                result_type=ExecutionResult.FAILED,
                message=message,
                actual_action=action
            )

    def _execute_skill_support(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行辅助技能"""
        target = game_state.roles[action.target_id]

        # 计算治疗效果
        heal_amount = role.attack_damage * 1.5  # 治疗量基于攻击力

        # 消耗魔法值
        mana_cost = 30
        role.mana = max(0, role.mana - mana_cost)

        # 更新目标血量
        target.health = min(target.max_health, target.health + heal_amount)

        # 设置技能冷却
        self._set_skill_cooldown(role.id, action.skill_id, 5)

        return ActionResult(
            success=True,
            result_type=ExecutionResult.SUCCESS,
            message=f"{role.name} 使用技能 {action.skill_id} 治疗 {target.name}, 恢复 {heal_amount:.1f} 点生命",
            actual_action=action,
            mana_cost=mana_cost,
            cooldown_remaining=5
        )

    def _execute_skill_move(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行移动技能"""
        # 移动技能通常可以移动更远的距离
        distance = role.position.distance_to(action.position)
        max_skill_move_distance = role.move_speed * 2.5  # 技能移动距离是普通移动的2.5倍

        if distance <= max_skill_move_distance:
            new_position = action.position
        else:
            ratio = max_skill_move_distance / distance
            new_x = role.position.x + (action.position.x - role.position.x) * ratio
            new_y = role.position.y + (action.position.y - role.position.y) * ratio
            new_position = Position(new_x, new_y)

        # 更新角色位置
        role.position = new_position

        # 消耗魔法值
        mana_cost = 40
        role.mana = max(0, role.mana - mana_cost)

        # 设置技能冷却
        self._set_skill_cooldown(role.id, action.skill_id, 4)

        return ActionResult(
            success=True,
            result_type=ExecutionResult.SUCCESS,
            message=f"{role.name} 使用技能 {action.skill_id} 位移到位置 ({new_position.x:.1f}, {new_position.y:.1f})",
            actual_action=action,
            mana_cost=mana_cost,
            cooldown_remaining=4
        )

    def _execute_skill_position(self, game_state: GameState, role: Role, action: Action) -> ActionResult:
        """执行位置技能"""
        # 使用技能系统
        from ..skills import SkillSystem
        success, message = SkillSystem.use_skill(role, action.skill_id, game_state, position=action.position)

        if success:
            return ActionResult(
                success=True,
                result_type=ExecutionResult.SUCCESS,
                message=message,
                actual_action=action
            )
        else:
            return ActionResult(
                success=False,
                result_type=ExecutionResult.FAILED,
                message=message,
                actual_action=action
            )

    def _check_skill_cooldown(self, role: Role, skill_id: str) -> Optional[str]:
        """检查技能冷却"""
        if role.id not in self.skill_cooldowns:
            return None

        cooldown = self.skill_cooldowns[role.id].get(skill_id, 0)
        if cooldown > 0:
            return f"技能 {skill_id} 冷却中，剩余 {cooldown} 回合"

        return None

    def _set_skill_cooldown(self, role_id: str, skill_id: str, cooldown: int) -> None:
        """设置技能冷却"""
        if role_id not in self.skill_cooldowns:
            self.skill_cooldowns[role_id] = {}

        self.skill_cooldowns[role_id][skill_id] = cooldown

    def update_cooldowns(self) -> None:
        """更新所有技能冷却"""
        for role_cooldowns in self.skill_cooldowns.values():
            for skill_id in list(role_cooldowns.keys()):
                if role_cooldowns[skill_id] > 0:
                    role_cooldowns[skill_id] -= 1

    def get_execution_history(self, role_id: Optional[str] = None,
                             turn_limit: int = 10) -> List[Tuple[int, str, ActionResult]]:
        """获取执行历史"""
        history = self.execution_history
        if role_id:
            history = [entry for entry in history if entry[1] == role_id]

        return history[-turn_limit:]

    def get_skill_cooldowns(self, role_id: str) -> Dict[str, int]:
        """获取角色技能冷却"""
        return self.skill_cooldowns.get(role_id, {}).copy()

    def clear_history(self) -> None:
        """清空执行历史"""
        self.execution_history.clear()