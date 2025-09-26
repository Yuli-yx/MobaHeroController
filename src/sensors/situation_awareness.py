from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math
from ..core.base import GameState, Role, Position


class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BattleSituation:
    """战场态势"""
    threat_level: ThreatLevel
    enemy_count: int
    ally_count: int
    nearest_enemy_distance: float
    nearest_ally_distance: float
    average_enemy_health: float
    average_ally_health: float
    towers_under_attack: int
    team_advantage: float  # 正数表示我方优势，负数表示敌方优势


@dataclass
class RoleStatus:
    """角色状态"""
    health_percentage: float
    mana_percentage: float
    is_low_health: bool
    is_low_mana: bool
    is_in_danger: bool
    can_use_skills: bool
    nearest_enemy: Optional[Role] = None
    nearest_ally: Optional[Role] = None


class SituationAwareness:
    """态势感知系统"""

    def __init__(self, danger_health_threshold: float = 0.3, danger_mana_threshold: float = 0.2):
        self.danger_health_threshold = danger_health_threshold
        self.danger_mana_threshold = danger_mana_threshold
        self.situation_memory: Dict[str, Any] = {}

    def analyze_battle_situation(self, game_state: GameState, role: Role) -> BattleSituation:
        """分析战场态势"""
        # 分析威胁程度
        enemies_nearby = self._get_enemies_in_range(game_state, role, range_limit=500)
        allies_nearby = self._get_allies_in_range(game_state, role, range_limit=500)

        enemy_count = len(enemies_nearby)
        ally_count = len(allies_nearby)

        # 计算最近距离
        nearest_enemy_distance = float('inf')
        nearest_ally_distance = float('inf')

        if enemies_nearby:
            nearest_enemy_distance = min(
                role.position.distance_to(enemy.position) for enemy in enemies_nearby
            )

        if allies_nearby:
            nearest_ally_distance = min(
                role.position.distance_to(ally.position) for ally in allies_nearby
            )

        # 计算平均血量
        average_enemy_health = (
            sum(enemy.health_percentage for enemy in enemies_nearby) / enemy_count
            if enemy_count > 0 else 1.0
        )
        average_ally_health = (
            sum(ally.health_percentage for ally in allies_nearby) / ally_count
            if ally_count > 0 else 1.0
        )

        # 计算团队优势
        team_advantage = self._calculate_team_advantage(game_state, role)

        # 计算威胁等级
        threat_level = self._calculate_threat_level(
            enemy_count, ally_count, nearest_enemy_distance, role.health_percentage
        )

        # 检查被攻击的塔
        towers_under_attack = self._count_towers_under_attack(game_state)

        return BattleSituation(
            threat_level=threat_level,
            enemy_count=enemy_count,
            ally_count=ally_count,
            nearest_enemy_distance=nearest_enemy_distance,
            nearest_ally_distance=nearest_ally_distance,
            average_enemy_health=average_enemy_health,
            average_ally_health=average_ally_health,
            towers_under_attack=towers_under_attack,
            team_advantage=team_advantage
        )

    def analyze_role_status(self, game_state: GameState, role: Role) -> RoleStatus:
        """分析角色状态"""
        is_low_health = role.health_percentage < self.danger_health_threshold
        is_low_mana = role.mana_percentage < self.danger_mana_threshold
        can_use_skills = not is_low_mana and len(role.skills) > 0

        # 判断是否处于危险中
        nearest_enemy = self._find_nearest_enemy(game_state, role)
        nearest_ally = self._find_nearest_ally(game_state, role)

        is_in_danger = False
        if nearest_enemy:
            distance = role.position.distance_to(nearest_enemy.position)
            is_in_danger = distance < 300 and is_low_health

        return RoleStatus(
            health_percentage=role.health_percentage,
            mana_percentage=role.mana_percentage,
            is_low_health=is_low_health,
            is_low_mana=is_low_mana,
            is_in_danger=is_in_danger,
            can_use_skills=can_use_skills,
            nearest_enemy=nearest_enemy,
            nearest_ally=nearest_ally
        )

    def should_retreat(self, game_state: GameState, role: Role) -> bool:
        """判断是否应该撤退"""
        status = self.analyze_role_status(game_state, role)
        situation = self.analyze_battle_situation(game_state, role)

        # 血量过低且周围有敌人
        if status.is_low_health and situation.enemy_count > 0:
            return True

        # 被多个敌人包围
        if situation.enemy_count > situation.ally_count + 1 and status.health_percentage < 0.5:
            return True

        # 威胁等级极高
        if situation.threat_level == ThreatLevel.CRITICAL:
            return True

        return False

    def should_attack(self, game_state: GameState, role: Role) -> bool:
        """判断是否应该进攻"""
        status = self.analyze_role_status(game_state, role)
        situation = self.analyze_battle_situation(game_state, role)

        # 血量充足且有敌人 nearby
        if status.health_percentage > 0.6 and situation.enemy_count > 0:
            return True

        # 团队优势明显
        if situation.team_advantage > 0.3 and situation.enemy_count > 0:
            return True

        return False

    def find_best_target(self, game_state: GameState, role: Role) -> Optional[Role]:
        """寻找最佳目标"""
        if not game_state.enemies:
            return None

        best_target = None
        best_score = float('-inf')

        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue

            score = self._calculate_target_score(game_state, role, enemy)
            if score > best_score:
                best_score = score
                best_target = enemy

        return best_target

    def find_safest_position(self, game_state: GameState, role: Role) -> Position:
        """寻找最安全的位置"""
        # 简单策略：向友方塔或友方角色方向移动
        allies = list(game_state.roles.values())
        if allies:
            # 找到友方角色的中心位置
            center_x = sum(ally.position.x for ally in allies) / len(allies)
            center_y = sum(ally.position.y for ally in allies) / len(allies)
            return Position(center_x, center_y)

        # 如果没有友方角色，向地图中心移动
        return Position(game_state.map_width / 2, game_state.map_height / 2)

    def _get_enemies_in_range(self, game_state: GameState, role: Role, range_limit: float) -> List[Role]:
        """获取指定范围内的敌人"""
        enemies = []
        for enemy in game_state.enemies.values():
            if not enemy.is_alive:
                continue
            distance = role.position.distance_to(enemy.position)
            if distance <= range_limit:
                enemies.append(enemy)
        return enemies

    def _get_allies_in_range(self, game_state: GameState, role: Role, range_limit: float) -> List[Role]:
        """获取指定范围内的友方角色"""
        allies = []
        for ally in game_state.roles.values():
            if ally.id == role.id or not ally.is_alive:
                continue
            distance = role.position.distance_to(ally.position)
            if distance <= range_limit:
                allies.append(ally)
        return allies

    def _calculate_team_advantage(self, game_state: GameState, role: Role) -> float:
        """计算团队优势"""
        team_health = game_state.get_team_health_percentage()
        enemy_health = game_state.get_enemy_team_health_percentage()
        return team_health - enemy_health

    def _calculate_threat_level(self, enemy_count: int, ally_count: int,
                               nearest_enemy_distance: float, health_percentage: float) -> ThreatLevel:
        """计算威胁等级"""
        if enemy_count == 0:
            return ThreatLevel.NONE

        # 基础威胁分数
        threat_score = enemy_count - ally_count

        # 距离因子
        if nearest_enemy_distance < 200:
            threat_score += 2
        elif nearest_enemy_distance < 400:
            threat_score += 1

        # 血量因子
        if health_percentage < 0.3:
            threat_score += 2
        elif health_percentage < 0.5:
            threat_score += 1

        # 转换为威胁等级
        if threat_score >= 4:
            return ThreatLevel.CRITICAL
        elif threat_score >= 2:
            return ThreatLevel.HIGH
        elif threat_score >= 1:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def _count_towers_under_attack(self, game_state: GameState) -> int:
        """计算被攻击的塔数量"""
        # 简化实现，实际游戏中需要检查塔的血量变化
        return 0

    def _find_nearest_enemy(self, game_state: GameState, role: Role) -> Optional[Role]:
        """找到最近的敌人"""
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

    def _find_nearest_ally(self, game_state: GameState, role: Role) -> Optional[Role]:
        """找到最近的友方角色"""
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

    def _calculate_target_score(self, game_state: GameState, role: Role, target: Role) -> float:
        """计算目标得分"""
        score = 0

        # 血量越低得分越高
        score += (1 - target.health_percentage) * 100

        # 距离越近得分越高
        distance = role.position.distance_to(target.position)
        if distance <= role.attack_range:
            score += 50
        else:
            score += max(0, 50 - distance / 10)

        # 威胁程度
        if target.attack_damage > role.attack_damage:
            score -= 20

        return score