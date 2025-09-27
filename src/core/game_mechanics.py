import random
from typing import Dict, List, Any, Optional, Tuple
from ..core.base import GameState, Role, Position


class GameMechanics:
    """游戏机制处理类，处理队伍分配、位置策略等"""

    # 地图配置
    MAP_WIDTH = 30.0
    MAP_HEIGHT = 20.0

    # 队伍起始位置
    DEFENDER_START = Position(2.0, 2.0)  # 左下角
    CHALLENGER_START = Position(28.0, 18.0)  # 右上角

    # 分路配置
    LANES = {
        'top': {'start': (2, 16), 'end': (28, 16), 'y': 16.0},
        'middle': {'start': (2, 10), 'end': (28, 10), 'y': 10.0},
        'bottom': {'start': (2, 4), 'end': (28, 4), 'y': 4.0}
    }

    @staticmethod
    def assign_team_side() -> str:
        """随机分配队伍方"""
        return random.choice(["defender", "challenger"])

    @staticmethod
    def get_start_position(team_side: str) -> Position:
        """获取队伍起始位置"""
        if team_side == "defender":
            return GameMechanics.DEFENDER_START
        else:  # challenger
            return GameMechanics.CHALLENGER_START

    @staticmethod
    def get_lane_position(team_side: str, lane: str, distance_from_base: float = 5.0) -> Position:
        """获取分路上的位置"""
        if lane not in GameMechanics.LANES:
            raise ValueError(f"未知的分路: {lane}")

        lane_config = GameMechanics.LANES[lane]

        if team_side == "defender":
            # 防守方从左向右
            x = min(lane_config['start'][0] + distance_from_base, lane_config['end'][0])
        else:  # challenger
            # 挑战方从右向左
            x = max(lane_config['end'][0] - distance_from_base, lane_config['start'][0])

        return Position(x, lane_config['y'])

    @staticmethod
    def create_initial_game_state() -> Tuple[GameState, str]:
        """创建初始游戏状态"""
        # 随机分配队伍
        team_side = GameMechanics.assign_team_side()
        enemy_side = "challenger" if team_side == "defender" else "defender"

        # 获取起始位置
        start_pos = GameMechanics.get_start_position(team_side)
        enemy_start_pos = GameMechanics.get_start_position(enemy_side)

        # 创建基础地图信息
        game_map = {
            'type': 'three_lane',
            'width': GameMechanics.MAP_WIDTH,
            'height': GameMechanics.MAP_HEIGHT,
            'lanes': GameMechanics.LANES
        }

        # 创建分路信息
        lane_info = {}
        for lane_name, lane_config in GameMechanics.LANES.items():
            lane_info[lane_name] = {
                'friendly_towers': 2 if team_side == "defender" else 0,
                'enemy_towers': 0 if team_side == "defender" else 2,
                'friendly_crystal': 1 if team_side == "defender" else 0,
                'enemy_crystal': 0 if team_side == "defender" else 1
            }

        # 创建游戏状态（暂时不包含英雄，将在后续添加）
        game_state = GameState(
            roles={},
            enemies={},
            towers=[],
            crystals=[],
            minions=[],
            current_turn=1,
            map_width=GameMechanics.MAP_WIDTH,
            map_height=GameMechanics.MAP_HEIGHT,
            game_map=game_map,
            lane_info=lane_info,
            team_side=team_side,
            diamonds_num=1000
        )

        return game_state, team_side

    @staticmethod
    def add_towers_to_game_state(game_state: GameState) -> None:
        """为游戏状态添加防御塔"""
        towers = []

        # 根据队伍方添加防御塔
        if game_state.team_side == "defender":
            # 防守方塔在左侧
            defender_towers = [
                {'id': 'defender_top_1', 'position': {'x': 8, 'y': 16}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_top_2', 'position': {'x': 15, 'y': 16}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_mid_1', 'position': {'x': 8, 'y': 10}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_mid_2', 'position': {'x': 15, 'y': 10}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_bot_1', 'position': {'x': 8, 'y': 4}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_bot_2', 'position': {'x': 15, 'y': 4}, 'health': 200, 'team': 'defender'},
            ]
            challenger_towers = [
                {'id': 'challenger_top_1', 'position': {'x': 22, 'y': 16}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_top_2', 'position': {'x': 26, 'y': 16}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_mid_1', 'position': {'x': 22, 'y': 10}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_mid_2', 'position': {'x': 26, 'y': 10}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_bot_1', 'position': {'x': 22, 'y': 4}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_bot_2', 'position': {'x': 26, 'y': 4}, 'health': 200, 'team': 'challenger'},
            ]
        else:
            # 挑战方塔在右侧
            defender_towers = [
                {'id': 'defender_top_1', 'position': {'x': 4, 'y': 16}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_top_2', 'position': {'x': 8, 'y': 16}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_mid_1', 'position': {'x': 4, 'y': 10}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_mid_2', 'position': {'x': 8, 'y': 10}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_bot_1', 'position': {'x': 4, 'y': 4}, 'health': 200, 'team': 'defender'},
                {'id': 'defender_bot_2', 'position': {'x': 8, 'y': 4}, 'health': 200, 'team': 'defender'},
            ]
            challenger_towers = [
                {'id': 'challenger_top_1', 'position': {'x': 22, 'y': 16}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_top_2', 'position': {'x': 26, 'y': 16}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_mid_1', 'position': {'x': 22, 'y': 10}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_mid_2', 'position': {'x': 26, 'y': 10}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_bot_1', 'position': {'x': 22, 'y': 4}, 'health': 200, 'team': 'challenger'},
                {'id': 'challenger_bot_2', 'position': {'x': 26, 'y': 4}, 'health': 200, 'team': 'challenger'},
            ]

        towers.extend(defender_towers)
        towers.extend(challenger_towers)
        game_state.towers = towers

    @staticmethod
    def add_crystals_to_game_state(game_state: GameState) -> None:
        """为游戏状态添加水晶"""
        crystals = []

        if game_state.team_side == "defender":
            # 防守方水晶在左下角
            crystals.extend([
                {'id': 'defender_crystal', 'position': {'x': 2, 'y': 2}, 'health': 500, 'team': 'defender'},
                {'id': 'challenger_crystal', 'position': {'x': 28, 'y': 18}, 'health': 500, 'team': 'challenger'}
            ])
        else:
            # 挑战方水晶在右上角
            crystals.extend([
                {'id': 'defender_crystal', 'position': {'x': 2, 'y': 2}, 'health': 500, 'team': 'defender'},
                {'id': 'challenger_crystal', 'position': {'x': 28, 'y': 18}, 'health': 500, 'team': 'challenger'}
            ])

        game_state.crystals = crystals

    @staticmethod
    def get_strategy_positions(team_side: str, hero_type: str) -> Dict[str, Position]:
        """根据队伍方和英雄类型获取策略位置"""
        strategies = {
            "defender": {
                "mage": {
                    "safe": GameMechanics.get_lane_position("defender", "bottom", 3.0),
                    "aggressive": GameMechanics.get_lane_position("defender", "middle", 8.0),
                    "support": GameMechanics.get_lane_position("defender", "bottom", 5.0)
                },
                "warrior": {
                    "tank": GameMechanics.get_lane_position("defender", "top", 6.0),
                    "push": GameMechanics.get_lane_position("defender", "middle", 10.0),
                    "defend": GameMechanics.get_lane_position("defender", "bottom", 4.0)
                },
                "monkey": {
                    "gank": GameMechanics.get_lane_position("defender", "middle", 7.0),
                    "roam": GameMechanics.get_lane_position("defender", "top", 8.0),
                    "split": GameMechanics.get_lane_position("defender", "bottom", 12.0)
                }
            },
            "challenger": {
                "mage": {
                    "safe": GameMechanics.get_lane_position("challenger", "top", 3.0),
                    "aggressive": GameMechanics.get_lane_position("challenger", "middle", 8.0),
                    "support": GameMechanics.get_lane_position("challenger", "top", 5.0)
                },
                "warrior": {
                    "tank": GameMechanics.get_lane_position("challenger", "bottom", 6.0),
                    "push": GameMechanics.get_lane_position("challenger", "middle", 10.0),
                    "defend": GameMechanics.get_lane_position("challenger", "top", 4.0)
                },
                "monkey": {
                    "gank": GameMechanics.get_lane_position("challenger", "middle", 7.0),
                    "roam": GameMechanics.get_lane_position("challenger", "bottom", 8.0),
                    "split": GameMechanics.get_lane_position("challenger", "top", 12.0)
                }
            }
        }

        return strategies.get(team_side, {}).get(hero_type, {})

    @staticmethod
    def get_distance_to_base(position: Position, team_side: str) -> float:
        """计算位置到己方基地的距离"""
        base_pos = GameMechanics.get_start_position(team_side)
        return position.distance_to(base_pos)

    @staticmethod
    def get_distance_to_enemy_base(position: Position, team_side: str) -> float:
        """计算位置到敌方基地的距离"""
        enemy_side = "challenger" if team_side == "defender" else "defender"
        enemy_base = GameMechanics.get_start_position(enemy_side)
        return position.distance_to(enemy_base)

    @staticmethod
    def is_in_safe_zone(position: Position, team_side: str) -> bool:
        """检查位置是否在安全区域"""
        safe_distance = 8.0
        distance_to_base = GameMechanics.get_distance_to_base(position, team_side)
        return distance_to_base <= safe_distance

    @staticmethod
    def get_lane_from_position(position: Position) -> Optional[str]:
        """根据位置获取所在分路"""
        for lane_name, lane_config in GameMechanics.LANES.items():
            if abs(position.y - lane_config['y']) <= 2.0:
                return lane_name
        return None