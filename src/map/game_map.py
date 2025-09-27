from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .lane import Lane, LaneType
from .structure import Structure, StructureType
from ..core.base import Position


@dataclass
class GameMap:
    """游戏地图"""
    width: float
    height: float
    lanes: Dict[LaneType, Lane]
    structures: List[Structure]
    obstacles: List[Position] = None

    def __post_init__(self):
        if self.obstacles is None:
            self.obstacles = []

    def get_lane_by_type(self, lane_type: LaneType) -> Optional[Lane]:
        """根据类型获取分路"""
        return self.lanes.get(lane_type)

    def get_lane_by_position(self, position: Position, tolerance: float = 2.0) -> Optional[Lane]:
        """根据位置获取分路"""
        for lane in self.lanes.values():
            if lane.is_position_in_lane(position, tolerance):
                return lane
        return None

    def get_all_structures(self) -> List[Structure]:
        """获取所有建筑"""
        return self.structures

    def get_structures_by_type(self, structure_type: StructureType) -> List[Structure]:
        """根据类型获取建筑"""
        return [s for s in self.structures if s.structure_type == structure_type]

    def get_structures_by_team(self, team: str) -> List[Structure]:
        """根据队伍获取建筑"""
        return [s for s in self.structures if s.team == team]

    def get_alive_structures(self) -> List[Structure]:
        """获取存活建筑"""
        return [s for s in self.structures if s.is_alive]

    def add_structure(self, structure: Structure) -> None:
        """添加建筑"""
        self.structures.append(structure)

    def remove_structure(self, structure_id: str) -> bool:
        """移除建筑"""
        for i, structure in enumerate(self.structures):
            if structure.id == structure_id:
                self.structures.pop(i)
                return True
        return False

    def update_structures(self) -> None:
        """更新所有建筑状态"""
        for structure in self.structures:
            structure.update_cooldown()

    def is_position_valid(self, position: Position) -> bool:
        """检查位置是否有效（在地图范围内）"""
        return (0 <= position.x <= self.width and
                0 <= position.y <= self.height)

    def get_defense_map(self) -> Dict[str, Any]:
        """获取防御地图信息"""
        defense_info = {
            'lanes': {},
            'structures': [],
            'total_towers': 0,
            'total_crystals': 0
        }

        for lane_type, lane in self.lanes.items():
            defense_info['lanes'][lane_type.value] = {
                'towers': len(lane.towers),
                'has_crystal': lane.crystal is not None,
                'tower_positions': [
                    {'x': tower['position']['x'], 'y': tower['position']['y']}
                    for tower in lane.towers
                ]
            }
            defense_info['total_towers'] += len(lane.towers)
            if lane.crystal:
                defense_info['total_crystals'] += 1

        # 添加建筑信息
        for structure in self.structures:
            defense_info['structures'].append(structure.to_dict())

        return defense_info

    def get_path_obstacles(self) -> List[Position]:
        """获取路径障碍物列表"""
        obstacles = []

        # 添加建筑作为障碍物
        for structure in self.get_alive_structures():
            obstacles.append(structure.position)

        # 添加其他障碍物
        obstacles.extend(self.obstacles)

        return obstacles

    def find_nearest_lane_position(self, position: Position) -> Optional[Position]:
        """找到最近分路上的位置"""
        nearest_position = None
        min_distance = float('inf')

        for lane in self.lanes.values():
            # 检查分路上的多个点
            num_points = 10
            for i in range(num_points + 1):
                ratio = i / num_points
                x = lane.start_position.x + ratio * (lane.end_position.x - lane.start_position.x)
                y = lane.start_position.y + ratio * (lane.end_position.y - lane.start_position.y)
                lane_pos = Position(x, y)

                distance = position.distance_to(lane_pos)
                if distance < min_distance:
                    min_distance = distance
                    nearest_position = lane_pos

        return nearest_position

    @classmethod
    def create_standard_map(cls, width: float = 30.0, height: float = 20.0) -> 'GameMap':
        """创建标准的三分路地图"""
        lanes = {}
        structures = []

        # 创建三条分路
        # 上路
        top_lane = Lane(
            lane_type=LaneType.TOP,
            name="上路",
            start_position=Position(2.0, 16.0),
            end_position=Position(28.0, 16.0),
            width=3.0,
            towers=[]
        )
        lanes[LaneType.TOP] = top_lane

        # 中路
        middle_lane = Lane(
            lane_type=LaneType.MIDDLE,
            name="中路",
            start_position=Position(2.0, 10.0),
            end_position=Position(28.0, 10.0),
            width=3.0,
            towers=[]
        )
        lanes[LaneType.MIDDLE] = middle_lane

        # 下路
        bottom_lane = Lane(
            lane_type=LaneType.BOTTOM,
            name="下路",
            start_position=Position(2.0, 4.0),
            end_position=Position(28.0, 4.0),
            width=3.0,
            towers=[]
        )
        lanes[LaneType.BOTTOM] = bottom_lane

        # 创建防御塔
        # 上路防御塔
        top_tower1 = Structure(
            id="top_tower_1",
            structure_type=StructureType.TOWER,
            position=Position(8.0, 16.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )
        top_tower2 = Structure(
            id="top_tower_2",
            structure_type=StructureType.TOWER,
            position=Position(22.0, 16.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )

        # 中路防御塔
        middle_tower1 = Structure(
            id="middle_tower_1",
            structure_type=StructureType.TOWER,
            position=Position(8.0, 10.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )
        middle_tower2 = Structure(
            id="middle_tower_2",
            structure_type=StructureType.TOWER,
            position=Position(22.0, 10.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )

        # 下路防御塔
        bottom_tower1 = Structure(
            id="bottom_tower_1",
            structure_type=StructureType.TOWER,
            position=Position(8.0, 4.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )
        bottom_tower2 = Structure(
            id="bottom_tower_2",
            structure_type=StructureType.TOWER,
            position=Position(22.0, 4.0),
            health=300.0,
            max_health=300.0,
            attack_damage=25.0,
            attack_range=5.0,
            team="enemy"
        )

        # 添加防御塔到结构和分路
        for tower in [top_tower1, top_tower2]:
            structures.append(tower)
            top_lane.towers.append(tower.to_dict())

        for tower in [middle_tower1, middle_tower2]:
            structures.append(tower)
            middle_lane.towers.append(tower.to_dict())

        for tower in [bottom_tower1, bottom_tower2]:
            structures.append(tower)
            bottom_lane.towers.append(tower.to_dict())

        return cls(width=width, height=height, lanes=lanes, structures=structures)