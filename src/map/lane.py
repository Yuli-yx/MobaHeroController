from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..core.base import Position


class LaneType(Enum):
    """分路类型"""
    TOP = "top"        # 上路
    MIDDLE = "middle"  # 中路
    BOTTOM = "bottom"  # 下路


@dataclass
class Lane:
    """分路"""
    lane_type: LaneType
    name: str
    start_position: Position
    end_position: Position
    width: float
    towers: List[Dict[str, Any]]
    crystal: Optional[Dict[str, Any]] = None
    minions: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.minions is None:
            self.minions = []

    def get_center_position(self) -> Position:
        """获取分路中心位置"""
        center_x = (self.start_position.x + self.end_position.x) / 2
        center_y = (self.start_position.y + self.end_position.y) / 2
        return Position(center_x, center_y)

    def is_position_in_lane(self, position: Position, tolerance: float = 2.0) -> bool:
        """检查位置是否在分路范围内"""
        # 简化的线段距离检查
        lane_length = self.start_position.distance_to(self.end_position)

        # 计算点到线段的距离
        if lane_length == 0:
            return position.distance_to(self.start_position) <= tolerance

        # 向量计算
        dx = self.end_position.x - self.start_position.x
        dy = self.end_position.y - self.start_position.y

        # 计算投影比例
        t = ((position.x - self.start_position.x) * dx +
             (position.y - self.start_position.y) * dy) / (lane_length ** 2)

        t = max(0, min(1, t))  # 限制在0-1之间

        # 计算最近点
        closest_x = self.start_position.x + t * dx
        closest_y = self.start_position.y + t * dy
        closest_pos = Position(closest_x, closest_y)

        return position.distance_to(closest_pos) <= self.width / 2 + tolerance

    def get_tower_positions(self) -> List[Position]:
        """获取防御塔位置列表"""
        positions = []
        for tower in self.towers:
            if 'position' in tower:
                pos_data = tower['position']
                positions.append(Position(pos_data['x'], pos_data['y']))
        return positions

    def get_crystal_position(self) -> Optional[Position]:
        """获取水晶位置"""
        if self.crystal and 'position' in self.crystal:
            pos_data = self.crystal['position']
            return Position(pos_data['x'], pos_data['y'])
        return None