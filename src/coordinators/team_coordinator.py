import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from ..core.base import GameState, Role, Action, ActionType, Position
from ..strategies.base_strategy import StrategyType, StrategyManager
from ..sensors import SituationAwareness, BattleSituation
import math


logger = logging.getLogger(__name__)


class TeamObjective(Enum):
    NONE = "none"
    PUSH_TOWER = "push_tower"
    DEFEND_BASE = "defend_base"
    TEAM_FIGHT = "team_fight"
    FARM_JUNGLE = "farm_jungle"
    SPLIT_PUSH = "split_push"
    ASSASSINATE = "assassinate"
    PROTECT_CARRY = "protect_carry"


@dataclass
class TeamPlan:
    """团队作战计划"""
    objective: TeamObjective
    leader_role_id: Optional[str]  # 队长角色ID
    target_position: Optional[Position]
    priority_roles: List[str]  # 优先参与的角色ID列表
    support_roles: List[str]   # 支援角色ID列表
    expected_duration: int     # 预期持续时间（回合数）
    coordination_level: float  # 协同程度 (0-1)


@dataclass
class RoleAssignment:
    """角色分配"""
    role_id: str
    position: Position
    task: str
    priority: int
    target_id: Optional[str] = None


class TeamCoordinator:
    """团队协同管理器"""

    def __init__(self):
        self.situation_awareness = SituationAwareness()
        self.current_plan: Optional[TeamPlan] = None
        self.plan_history: List[Tuple[int, TeamPlan]] = []
        self.role_assignments: Dict[str, RoleAssignment] = {}
        self.team_strategy_manager = StrategyManager()
        self.communication_log: List[Tuple[int, str, str]] = []  # (turn, role_id, message)
        self.minimum_plan_duration = 5  # 最小计划持续时间
        self.last_plan_change = 0

        # 协同参数
        self.coordination_distance = 800  # 协同距离
        self.team_formation_spacing = 150  # 队形间距

    def update_team_strategy(self, game_state: GameState, current_turn: int) -> None:
        """更新团队策略"""
        if self.current_plan:
            # 检查是否需要更新计划
            if current_turn - self.last_plan_change < self.minimum_plan_duration:
                return

        # 分析战场态势
        battle_situation = self.situation_awareness.analyze_battle_situation(
            game_state, list(game_state.roles.values())[0] if game_state.roles else None
        )

        # 制定新的团队计划
        new_plan = self._formulate_team_plan(game_state, battle_situation, current_turn)

        if new_plan and new_plan != self.current_plan:
            self.current_plan = new_plan
            self.last_plan_change = current_turn
            self.plan_history.append((current_turn, new_plan))
            logger.info(f"团队计划更新: {new_plan.objective.value}")

            # 分配角色任务
            self._assign_role_tasks(game_state)

    def get_role_action(self, game_state: GameState, role: Role,
                       current_turn: int) -> Optional[Action]:
        """获取角色的协同动作"""
        if not self.current_plan:
            return None

        # 获取角色分配
        assignment = self.role_assignments.get(role.id)
        if not assignment:
            return None

        # 根据分配的任务生成动作
        action = self._generate_action_for_assignment(game_state, role, assignment)

        # 记录协同信息
        if action:
            self._log_coordination(current_turn, role.id, f"执行{assignment.task}任务")

        return action

    def should_coordinate_attack(self, game_state: GameState, target_id: str) -> List[str]:
        """判断是否应该协同攻击，返回参与攻击的角色ID列表"""
        target = game_state.enemies.get(target_id)
        if not target or not target.is_alive:
            return []

        participants = []
        target_position = target.position

        for role_id, role in game_state.roles.items():
            if not role.is_alive:
                continue

            distance = role.position.distance_to(target_position)
            if distance <= role.attack_range + 200:  # 稍微放大范围
                participants.append(role_id)

        # 至少需要2个角色才能形成协同攻击
        return participants if len(participants) >= 2 else []

    def should_coordinate_defense(self, game_state: GameState) -> Dict[str, Position]:
        """判断是否应该协同防守，返回角色ID和防守位置"""
        defense_positions = {}

        # 寻找需要防守的关键位置
        critical_positions = self._identify_critical_positions(game_state)

        for role_id, role in game_state.roles.items():
            if not role.is_alive:
                continue

            # 为每个角色分配最近的防守位置
            best_position = None
            min_distance = float('inf')

            for pos in critical_positions:
                distance = role.position.distance_to(pos)
                if distance < min_distance:
                    min_distance = distance
                    best_position = pos

            if best_position and min_distance < 1000:  # 在合理范围内
                defense_positions[role_id] = best_position

        return defense_positions

    def coordinate_team_movement(self, game_state: GameState, target_position: Position,
                               formation: str = "line") -> Dict[str, Position]:
        """协同团队移动，返回每个角色的目标位置"""
        movement_positions = {}

        # 获取存活的队友
        alive_roles = [role for role in game_state.roles.values() if role.is_alive]
        if not alive_roles:
            return movement_positions

        if formation == "line":
            movement_positions = self._calculate_line_formation(alive_roles, target_position)
        elif formation == "circle":
            movement_positions = self._calculate_circle_formation(alive_roles, target_position)
        elif formation == "wedge":
            movement_positions = self._calculate_wedge_formation(alive_roles, target_position)
        else:
            # 默认：简单聚集
            movement_positions = self._calculate_gather_formation(alive_roles, target_position)

        return movement_positions

    def get_team_status(self, game_state: GameState) -> Dict[str, Any]:
        """获取团队状态"""
        if not game_state.roles:
            return {"team_size": 0}

        total_health = sum(role.health for role in game_state.roles.values() if role.is_alive)
        max_total_health = sum(role.max_health for role in game_state.roles.values())
        health_percentage = total_health / max_total_health if max_total_health > 0 else 0

        total_mana = sum(role.mana for role in game_state.roles.values() if role.is_alive)
        max_total_mana = sum(role.max_mana for role in game_state.roles.values())
        mana_percentage = total_mana / max_total_mana if max_total_mana > 0 else 0

        # 计算团队聚集程度
        positions = [role.position for role in game_state.roles.values() if role.is_alive]
        cohesion = self._calculate_team_cohesion(positions) if len(positions) > 1 else 1.0

        return {
            "team_size": len([r for r in game_state.roles.values() if r.is_alive]),
            "total_health": total_health,
            "health_percentage": health_percentage,
            "total_mana": total_mana,
            "mana_percentage": mana_percentage,
            "team_cohesion": cohesion,
            "current_objective": self.current_plan.objective.value if self.current_plan else "none",
            "coordination_level": self.current_plan.coordination_level if self.current_plan else 0.0
        }

    def _formulate_team_plan(self, game_state: GameState, battle_situation: BattleSituation,
                           current_turn: int) -> Optional[TeamPlan]:
        """制定团队计划"""
        if not game_state.roles:
            return None

        # 分析形势
        team_advantage = battle_situation.team_advantage
        threat_level = battle_situation.threat_level

        # 根据形势选择目标
        if team_advantage > 0.3 and threat_level.value <= 2:
            # 优势明显，推进
            objective = TeamObjective.PUSH_TOWER
            target_position = self._find_push_target(game_state)
            priority_roles = list(game_state.roles.keys())
        elif threat_level.value >= 3:
            # 威胁高，防守
            objective = TeamObjective.DEFEND_BASE
            target_position = self._find_defense_position(game_state)
            priority_roles = list(game_state.roles.keys())
        elif battle_situation.enemy_count >= 4:
            # 敌人较多，准备团战
            objective = TeamObjective.TEAM_FIGHT
            target_position = self._find_team_fight_position(game_state)
            priority_roles = list(game_state.roles.keys())
        else:
            # 默认：发育
            objective = TeamObjective.FARM_JUNGLE
            target_position = Position(game_state.map_width / 2, game_state.map_height / 2)
            priority_roles = list(game_state.roles.keys())

        # 选择队长（血量最多、攻击力最高的角色）
        leader_id = self._select_team_leader(game_state)

        return TeamPlan(
            objective=objective,
            leader_role_id=leader_id,
            target_position=target_position,
            priority_roles=priority_roles,
            support_roles=[],  # 简化处理
            expected_duration=10,
            coordination_level=min(1.0, len(game_state.roles) / 5.0)
        )

    def _assign_role_tasks(self, game_state: GameState) -> None:
        """分配角色任务"""
        if not self.current_plan:
            return

        self.role_assignments.clear()

        objective = self.current_plan.objective
        target_position = self.current_plan.target_position

        for i, (role_id, role) in enumerate(game_state.roles.items()):
            if not role.is_alive:
                continue

            if objective == TeamObjective.PUSH_TOWER:
                assignment = self._create_push_assignment(role_id, role, target_position, i)
            elif objective == TeamObjective.DEFEND_BASE:
                assignment = self._create_defend_assignment(role_id, role, target_position, i)
            elif objective == TeamObjective.TEAM_FIGHT:
                assignment = self._create_team_fight_assignment(role_id, role, target_position, i)
            elif objective == TeamObjective.FARM_JUNGLE:
                assignment = self._create_farm_assignment(role_id, role, target_position, i)
            else:
                assignment = self._create_general_assignment(role_id, role, target_position, i)

            self.role_assignments[role_id] = assignment

    def _generate_action_for_assignment(self, game_state: GameState, role: Role,
                                      assignment: RoleAssignment) -> Action:
        """根据任务分配生成动作"""
        task = assignment.task
        target_position = assignment.position
        target_id = assignment.target_id

        if task == "attack":
            # 攻击任务
            if target_id and target_id in game_state.enemies:
                target = game_state.enemies[target_id]
                distance = role.position.distance_to(target.position)
                if distance <= role.attack_range:
                    return Action(
                        action_type=ActionType.ATTACK,
                        target_id=target_id,
                        priority=assignment.priority
                    )
                else:
                    return Action(
                        action_type=ActionType.MOVE,
                        position=target.position,
                        priority=assignment.priority
                    )

        elif task == "move_to_position":
            # 移动到指定位置
            distance = role.position.distance_to(target_position)
            if distance > 50:  # 还没到达
                return Action(
                    action_type=ActionType.MOVE,
                    position=target_position,
                    priority=assignment.priority
                )

        elif task == "defend":
            # 防守任务
            # 寻找附近的敌人进行防守
            nearest_enemy = self._find_nearest_enemy(game_state, role)
            if nearest_enemy:
                distance = role.position.distance_to(nearest_enemy.position)
                if distance <= role.attack_range:
                    return Action(
                        action_type=ActionType.ATTACK,
                        target_id=nearest_enemy.id,
                        priority=assignment.priority
                    )

        elif task == "support":
            # 支援任务
            # 寻找需要帮助的队友
            ally_in_need = self._find_ally_in_need(game_state, role)
            if ally_in_need:
                return Action(
                    action_type=ActionType.MOVE,
                    position=ally_in_need.position,
                    priority=assignment.priority
                )

        # 默认动作：向目标位置移动
        return Action(
            action_type=ActionType.MOVE,
            position=target_position,
            priority=assignment.priority
        )

    def _create_push_assignment(self, role_id: str, role: Role,
                               target_position: Position, index: int) -> RoleAssignment:
        """创建推进任务分配"""
        task = "move_to_position"
        if index == 0:  # 第一个角色作为先锋
            task = "attack"

        return RoleAssignment(
            role_id=role_id,
            position=self._calculate_formation_position(target_position, index, "line"),
            task=task,
            priority=3 - index // 2,
            target_id=self._find_target_for_role(role_id, "push")
        )

    def _create_defend_assignment(self, role_id: str, role: Role,
                                target_position: Position, index: int) -> RoleAssignment:
        """创建防守任务分配"""
        return RoleAssignment(
            role_id=role_id,
            position=self._calculate_formation_position(target_position, index, "line"),
            task="defend",
            priority=4 - index,
            target_id=self._find_target_for_role(role_id, "defend")
        )

    def _create_team_fight_assignment(self, role_id: str, role: Role,
                                    target_position: Position, index: int) -> RoleAssignment:
        """创建团战任务分配"""
        task = "move_to_position"
        if index == 0:
            task = "attack"  # 主力输出
        elif index >= len(self.role_assignments) - 1:
            task = "support"  # 后排支援

        return RoleAssignment(
            role_id=role_id,
            position=self._calculate_formation_position(target_position, index, "wedge"),
            task=task,
            priority=5 - index,
            target_id=self._find_target_for_role(role_id, "fight")
        )

    def _create_farm_assignment(self, role_id: str, role: Role,
                              target_position: Position, index: int) -> RoleAssignment:
        """创建发育任务分配"""
        return RoleAssignment(
            role_id=role_id,
            position=self._calculate_formation_position(target_position, index, "circle"),
            task="move_to_position",
            priority=2,
            target_id=None
        )

    def _create_general_assignment(self, role_id: str, role: Role,
                                 target_position: Position, index: int) -> RoleAssignment:
        """创建通用任务分配"""
        return RoleAssignment(
            role_id=role_id,
            position=self._calculate_formation_position(target_position, index, "line"),
            task="move_to_position",
            priority=3,
            target_id=None
        )

    def _calculate_formation_position(self, center: Position, index: int,
                                    formation: str) -> Position:
        """计算队形中的位置"""
        if formation == "line":
            # 线性队形
            offset_x = (index % 3 - 1) * self.team_formation_spacing
            offset_y = (index // 3) * self.team_formation_spacing
            return Position(center.x + offset_x, center.y + offset_y)

        elif formation == "circle":
            # 圆形队形
            angle = (index / max(1, index + 1)) * 2 * math.pi
            radius = self.team_formation_spacing * (1 + index // 4)
            return Position(
                center.x + radius * math.cos(angle),
                center.y + radius * math.sin(angle)
            )

        elif formation == "wedge":
            # 楔形队形
            row = index // 2
            col = index % 2
            offset_x = (col - 0.5) * self.team_formation_spacing * (row + 1)
            offset_y = -row * self.team_formation_spacing
            return Position(center.x + offset_x, center.y + offset_y)

        else:
            # 默认聚集
            return center

    def _find_push_target(self, game_state: GameState) -> Position:
        """寻找推进目标"""
        # 简化：向敌方基地推进
        return Position(game_state.map_width * 0.8, game_state.map_height * 0.8)

    def _find_defense_position(self, game_state: GameState) -> Position:
        """寻找防守位置"""
        # 简化：防守我方基地
        return Position(game_state.map_width * 0.2, game_state.map_height * 0.2)

    def _find_team_fight_position(self, game_state: GameState) -> Position:
        """寻找团战位置"""
        # 简化：在地图中心
        return Position(game_state.map_width / 2, game_state.map_height / 2)

    def _select_team_leader(self, game_state: GameState) -> Optional[str]:
        """选择团队队长"""
        best_leader = None
        best_score = -1

        for role_id, role in game_state.roles.items():
            if not role.is_alive:
                continue

            # 综合考虑血量、攻击力和生存能力
            score = role.health_percentage * 100 + role.attack_damage * 2 + role.defense * 1.5

            if score > best_score:
                best_score = score
                best_leader = role_id

        return best_leader

    def _find_target_for_role(self, role_id: str, context: str) -> Optional[str]:
        """为角色寻找目标"""
        # 简化实现，实际应该根据具体情境寻找目标
        return None

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

    def _find_ally_in_need(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找需要帮助的队友"""
        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue

            if ally.health_percentage < 0.4:  # 血量低于40%需要帮助
                return ally

        return None

    def _identify_critical_positions(self, game_state: GameState) -> List[Position]:
        """识别关键防守位置"""
        positions = []

        # 我方基地附近
        positions.append(Position(game_state.map_width * 0.1, game_state.map_height * 0.5))

        # 重要塔防位置（简化）
        positions.append(Position(game_state.map_width * 0.3, game_state.map_height * 0.3))
        positions.append(Position(game_state.map_width * 0.3, game_state.map_height * 0.7))

        return positions

    def _calculate_line_formation(self, roles: List[Role], target: Position) -> Dict[str, Position]:
        """计算线性队形"""
        positions = {}
        for i, role in enumerate(roles):
            offset_x = (i % 3 - 1) * self.team_formation_spacing
            offset_y = (i // 3) * self.team_formation_spacing
            positions[role.id] = Position(target.x + offset_x, target.y + offset_y)
        return positions

    def _calculate_circle_formation(self, roles: List[Role], target: Position) -> Dict[str, Position]:
        """计算圆形队形"""
        positions = {}
        for i, role in enumerate(roles):
            angle = (i / len(roles)) * 2 * math.pi
            radius = self.team_formation_spacing * 2
            positions[role.id] = Position(
                target.x + radius * math.cos(angle),
                target.y + radius * math.sin(angle)
            )
        return positions

    def _calculate_wedge_formation(self, roles: List[Role], target: Position) -> Dict[str, Position]:
        """计算楔形队形"""
        positions = {}
        for i, role in enumerate(roles):
            row = i // 2
            col = i % 2
            offset_x = (col - 0.5) * self.team_formation_spacing * (row + 1)
            offset_y = -row * self.team_formation_spacing
            positions[role.id] = Position(target.x + offset_x, target.y + offset_y)
        return positions

    def _calculate_gather_formation(self, roles: List[Role], target: Position) -> Dict[str, Position]:
        """计算聚集队形"""
        positions = {}
        for role in roles:
            positions[role.id] = target
        return positions

    def _calculate_team_cohesion(self, positions: List[Position]) -> float:
        """计算团队聚集程度"""
        if len(positions) < 2:
            return 1.0

        # 计算平均距离
        total_distance = 0
        count = 0

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = positions[i].distance_to(positions[j])
                total_distance += distance
                count += 1

        if count == 0:
            return 1.0

        avg_distance = total_distance / count

        # 距离越近，聚集程度越高
        return max(0, 1 - avg_distance / 1000)

    def _log_coordination(self, turn: int, role_id: str, message: str) -> None:
        """记录协同信息"""
        self.communication_log.append((turn, role_id, message))

        # 限制日志长度
        if len(self.communication_log) > 100:
            self.communication_log = self.communication_log[-50:]

    def get_coordination_log(self, limit: int = 20) -> List[Tuple[int, str, str]]:
        """获取协同日志"""
        return self.communication_log[-limit:]

    def clear_coordination_log(self) -> None:
        """清空协同日志"""
        self.communication_log.clear()