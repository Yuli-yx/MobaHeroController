from typing import Dict, List, Optional, Any, Tuple
from ..core.base import GameState, Role, Action, ActionType, Position
from ..core.game_mechanics import GameMechanics


class PositionStrategy:
    """基于队伍位置的游戏策略系统"""

    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.team_side = game_state.team_side
        self.enemy_side = "challenger" if self.team_side == "defender" else "defender"

    def get_strategic_position(self, role: Role, strategy_type: str = "balanced") -> Position:
        """根据英雄类型和策略获取战略位置"""
        hero_strategies = GameMechanics.get_strategy_positions(self.team_side, role.hero_type)

        if strategy_type in hero_strategies:
            return hero_strategies[strategy_type]
        else:
            # 默认策略：根据英雄类型选择位置
            return self._get_default_position(role)

    def _get_default_position(self, role: Role) -> Position:
        """获取默认战略位置"""
        if self.team_side == "defender":
            if role.hero_type == "mage":
                return GameMechanics.get_lane_position("defender", "bottom", 5.0)
            elif role.hero_type == "warrior":
                return GameMechanics.get_lane_position("defender", "top", 6.0)
            else:  # monkey
                return GameMechanics.get_lane_position("defender", "middle", 7.0)
        else:  # challenger
            if role.hero_type == "mage":
                return GameMechanics.get_lane_position("challenger", "top", 5.0)
            elif role.hero_type == "warrior":
                return GameMechanics.get_lane_position("challenger", "bottom", 6.0)
            else:  # monkey
                return GameMechanics.get_lane_position("challenger", "middle", 7.0)

    def should_attack(self, role: Role, target: Role) -> bool:
        """判断是否应该攻击目标"""
        if not target.is_alive:
            return False

        distance = role.position.distance_to(target.position)
        if distance > role.attack_range:
            return False

        # 检查攻击路径是否有障碍
        from ..actions.action_executor import ActionValidator
        path_clear, _ = ActionValidator._check_attack_path_obstacles(self.game_state, role, target)
        return path_clear

    def should_use_skill(self, role: Role, skill_id: str) -> bool:
        """判断是否应该使用技能"""
        # 检查技能冷却
        if role.get_skill_cooldown(skill_id) > 0:
            return False

        # 检查钻石
        if role.diamonds < 5:
            return False

        # 根据技能类型判断使用时机
        if role.hero_type == "mage":
            return self._should_use_mage_skill(role, skill_id)
        elif role.hero_type == "warrior":
            return self._should_use_warrior_skill(role, skill_id)
        elif role.hero_type == "monkey":
            return self._should_use_monkey_skill(role, skill_id)

        return False

    def _should_use_mage_skill(self, role: Role, skill_id: str) -> bool:
        """法师技能使用判断"""
        if skill_id == "heal":
            # 血量低于50%时使用治疗
            return role.health_percentage < 0.5
        elif skill_id == "area_control":
            # 周围有多个敌人时使用范围控制
            enemies_in_range = self._get_enemies_in_range(role.position, 5.0)
            return len(enemies_in_range) >= 2
        return False

    def _should_use_warrior_skill(self, role: Role, skill_id: str) -> bool:
        """武士技能使用判断"""
        if skill_id == "heavy_strike":
            # 有攻击目标时使用重击
            return self._has_attack_target(role)
        elif skill_id == "iron_defense":
            # 血量低于40%或周围有多个敌人时使用防御
            return role.health_percentage < 0.4 or len(self._get_enemies_in_range(role.position, 3.0)) >= 2
        return False

    def _should_use_monkey_skill(self, role: Role, skill_id: str) -> bool:
        """猴子技能使用判断"""
        if skill_id == "corrosive_strike":
            # 有攻击目标时使用腐蚀打击
            return self._has_attack_target(role)
        elif skill_id == "leap":
            # 需要追击或逃跑时使用跳跃
            return self._should_leap(role)
        return False

    def _get_enemies_in_range(self, position: Position, range: float) -> List[Role]:
        """获取指定范围内的敌人"""
        enemies_in_range = []
        for enemy in self.game_state.enemies.values():
            if enemy.is_alive and position.distance_to(enemy.position) <= range:
                enemies_in_range.append(enemy)
        return enemies_in_range

    def _has_attack_target(self, role: Role) -> bool:
        """检查是否有攻击目标"""
        for enemy in self.game_state.enemies.values():
            if enemy.is_alive and role.position.distance_to(enemy.position) <= role.attack_range:
                return True
        return False

    def _should_leap(self, role: Role) -> bool:
        """判断是否应该使用跳跃技能"""
        # 血量低于30%时逃跑
        if role.health_percentage < 0.3:
            # 跳向基地方向
            base_pos = GameMechanics.get_start_position(self.team_side)
            return role.position.distance_to(base_pos) > 8.0

        # 追击低血量敌人
        for enemy in self.game_state.enemies.values():
            if enemy.is_alive and enemy.health_percentage < 0.4:
                distance = role.position.distance_to(enemy.position)
                if 4.0 < distance <= 8.0:  # 跳跃范围内
                    return True

        return False

    def get_defensive_position(self, role: Role) -> Position:
        """获取防御位置"""
        current_lane = GameMechanics.get_lane_from_position(role.position)
        if not current_lane:
            return role.position

        # 找到最近的防御塔
        nearest_tower = self._get_nearest_friendly_tower(role.position)
        if nearest_tower:
            tower_pos = Position(nearest_tower['position']['x'], nearest_tower['position']['y'])
            # 在塔附近2个单位范围内
            if role.position.distance_to(tower_pos) > 3.0:
                direction_x = tower_pos.x - role.position.x
                direction_y = tower_pos.y - role.position.y
                distance = (direction_x**2 + direction_y**2)**0.5
                if distance > 0:
                    move_x = role.position.x + (direction_x / distance) * 2.0
                    move_y = role.position.y + (direction_y / distance) * 2.0
                    return Position(move_x, move_y)

        return role.position

    def get_aggressive_position(self, role: Role) -> Position:
        """获取进攻位置"""
        current_lane = GameMechanics.get_lane_from_position(role.position)
        if current_lane:
            # 向敌方基地推进
            if self.team_side == "defender":
                target_x = min(role.position.x + 3.0, GameMechanics.LANES[current_lane]['end'][0])
            else:
                target_x = max(role.position.x - 3.0, GameMechanics.LANES[current_lane]['start'][0])

            return Position(target_x, role.position.y)

        return role.position

    def get_farm_position(self, role: Role) -> Position:
        """获取打钱位置"""
        # 找到有敌方小兵的位置
        for minion in self.game_state.minions:
            if minion.get('team') == 'enemy' and 'position' in minion:
                minion_pos = Position(minion['position']['x'], minion['position']['y'])
                if role.position.distance_to(minion_pos) <= 8.0:
                    return minion_pos

        # 没有小兵时返回分路位置
        return self.get_strategic_position(role, "balanced")

    def _get_nearest_friendly_tower(self, position: Position) -> Optional[Dict[str, Any]]:
        """获取最近的友方防御塔"""
        nearest_tower = None
        min_distance = float('inf')

        for tower in self.game_state.towers:
            if tower.get('team') == self.team_side and 'position' in tower:
                tower_pos = Position(tower['position']['x'], tower['position']['y'])
                distance = position.distance_to(tower_pos)
                if distance < min_distance:
                    min_distance = distance
                    nearest_tower = tower

        return nearest_tower

    def get_team_strategy(self) -> str:
        """获取团队整体策略"""
        # 计算团队经济优势
        team_diamonds = sum(role.diamonds for role in self.game_state.roles.values())
        enemy_diamonds = sum(role.diamonds for role in self.game_state.enemies.values())

        # 计算团队血量优势
        team_health = sum(role.health_percentage for role in self.game_state.roles.values())
        enemy_health = sum(role.health_percentage for role in self.game_state.enemies.values())

        if team_diamonds > enemy_diamonds * 1.2 and team_health > enemy_health * 1.1:
            return "aggressive"  # 经济和血量优势，进攻
        elif team_health < enemy_health * 0.8:
            return "defensive"  # 血量劣势，防守
        else:
            return "balanced"  # 均势，平衡发展

    def get_role_strategy(self, role: Role) -> str:
        """获取单个英雄的策略"""
        team_strategy = self.get_team_strategy()

        if role.hero_type == "mage":
            if team_strategy == "aggressive":
                return "aggressive"
            else:
                return "safe"
        elif role.hero_type == "warrior":
            if team_strategy == "defensive":
                return "defend"
            else:
                return "push"
        elif role.hero_type == "monkey":
            if team_strategy == "aggressive":
                return "gank"
            else:
                return "roam"

        return "balanced"