import heapq
from typing import List, Tuple, Optional, Set, Dict
from ..core.base import Position, GameState, Role


class AStarNode:
    """A*算法节点"""

    def __init__(self, position: Position, g_cost: float, h_cost: float, parent=None):
        self.position = position
        self.g_cost = g_cost  # 从起点到当前节点的实际成本
        self.h_cost = h_cost  # 从当前节点到终点的启发式估计成本
        self.f_cost = g_cost + h_cost  # 总成本
        self.parent = parent

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class PathFinder:
    """路径查找器，使用A*算法和切比雪夫距离"""

    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.grid_size = 1.0  # 网格大小，用于离散化位置

    def chebyshev_distance(self, pos1: Position, pos2: Position) -> float:
        """
        计算切比雪夫距离
        切比雪夫距离 = max(|x1-x2|, |y1-y2|)
        适用于可以沿对角线移动的情况
        """
        return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))

    def get_neighbors(self, position: Position) -> List[Position]:
        """获取相邻位置（8个方向）"""
        neighbors = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        for dx, dy in directions:
            new_x = position.x + dx * self.grid_size
            new_y = position.y + dy * self.grid_size
            new_pos = Position(new_x, new_y)

            # 检查是否在地图范围内
            if (0 <= new_x <= self.game_state.map_width and
                0 <= new_y <= self.game_state.map_height):
                neighbors.append(new_pos)

        return neighbors

    def get_straight_line_neighbors(self, position: Position) -> List[Position]:
        """获取直线方向的相邻位置（4个方向）"""
        neighbors = []
        directions = [
            (-1, 0),  # 左
            (1, 0),   # 右
            (0, -1),  # 上
            (0, 1)    # 下
        ]

        for dx, dy in directions:
            new_x = position.x + dx * self.grid_size
            new_y = position.y + dy * self.grid_size
            new_pos = Position(new_x, new_y)

            # 检查是否在地图范围内
            if (0 <= new_x <= self.game_state.map_width and
                0 <= new_y <= self.game_state.map_height):
                neighbors.append(new_pos)

        return neighbors

    def is_position_blocked(self, position: Position, obstacles: Optional[List[Position]] = None,
                           moving_role: Optional[Role] = None) -> bool:
        """检查位置是否被阻挡"""
        if obstacles is None:
            obstacles = []

        # 检查是否与障碍物重叠
        for obstacle in obstacles:
            if (abs(position.x - obstacle.x) < self.grid_size and
                abs(position.y - obstacle.y) < self.grid_size):
                return True

        # 检查是否与其他角色重叠（排除正在移动的角色）
        for role in self.game_state.roles.values():
            if role.is_alive and role != moving_role:
                if (abs(position.x - role.position.x) < self.grid_size and
                    abs(position.y - role.position.y) < self.grid_size):
                    return True

        for enemy in self.game_state.enemies.values():
            if enemy.is_alive:
                if (abs(position.x - enemy.position.x) < self.grid_size and
                    abs(position.y - enemy.position.y) < self.grid_size):
                    return True

        return False

    def find_nearest_traversable_position(self, position: Position,
                                         obstacles: Optional[List[Position]] = None,
                                         moving_role: Optional[Role] = None,
                                         max_distance: int = 10) -> Optional[Position]:
        """
        使用BFS算法查找最近的可通行位置
        返回最近的可通行位置，如果找不到返回None
        """
        from collections import deque

        if obstacles is None:
            obstacles = []

        # 首先检查当前位置本身是否可通行
        if not self.is_position_blocked(position, obstacles, moving_role):
            return position

        # BFS搜索
        queue = deque([(position.x, position.y, 0)])  # (x, y, distance)
        visited = set()
        visited.add((position.x, position.y))

        # 8个方向
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        while queue:
            x, y, distance = queue.popleft()

            # 如果超出最大搜索距离，跳过
            if distance > max_distance:
                continue

            # 检查当前位置
            current_pos = Position(x, y)

            # 检查是否在地图范围内
            if (0 <= x <= self.game_state.map_width and
                0 <= y <= self.game_state.map_height):

                # 检查是否可通行
                if not self.is_position_blocked(current_pos, obstacles, moving_role):
                    return current_pos

                # 搜索相邻位置
                for dx, dy in directions:
                    new_x = x + dx * self.grid_size
                    new_y = y + dy * self.grid_size

                    if (new_x, new_y) not in visited:
                        visited.add((new_x, new_y))
                        queue.append((new_x, new_y, distance + 1))

        # 没有找到可通行位置
        return None

    def find_path_simple(self, start: Position, goal: Position,
                        obstacles: Optional[List[Position]] = None,
                        moving_role: Optional[Role] = None) -> List[Position]:
        """简单的直线路径查找"""
        if obstacles is None:
            obstacles = []

        # 检查起点和终点是否被阻挡
        if self.is_position_blocked(start, obstacles, moving_role):
            traversable_start = self.find_nearest_traversable_position(
                start, obstacles, moving_role
            )
            if traversable_start:
                start = traversable_start
            else:
                return []

        if self.is_position_blocked(goal, obstacles, moving_role):
            traversable_goal = self.find_nearest_traversable_position(
                goal, obstacles, moving_role
            )
            if traversable_goal:
                goal = traversable_goal
            else:
                return []

        # 对于简单的直线移动，直接返回起点和终点
        return [start, goal]

    def find_path(self, start: Position, goal: Position,
                  obstacles: Optional[List[Position]] = None,
                  moving_role: Optional[Role] = None,
                  max_iterations: int = 1000) -> List[Position]:
        """
        使用A*算法寻找路径
        返回从起点到终点的路径（包括起点和终点）
        如果起点或终点被阻挡，使用BFS查找最近的可通行位置
        """
        if obstacles is None:
            obstacles = []

        # 检查起点是否被阻挡，如果被阻挡则查找最近的可通行位置
        if self.is_position_blocked(start, obstacles, moving_role):
            traversable_start = self.find_nearest_traversable_position(
                start, obstacles, moving_role
            )
            if traversable_start:
                start = traversable_start
            else:
                return []

        # 检查终点是否被阻挡，如果被阻挡则查找最近的可通行位置
        if self.is_position_blocked(goal, obstacles, moving_role):
            traversable_goal = self.find_nearest_traversable_position(
                goal, obstacles, moving_role
            )
            if traversable_goal:
                goal = traversable_goal
            else:
                return []

        # 对于直线移动的特殊情况，使用简化算法
        if start.x == goal.x or start.y == goal.y:
            return self.find_path_simple(start, goal, obstacles, moving_role)

        # 初始化开放列表和关闭列表
        open_list = []
        closed_set: Set[Tuple[float, float]] = set()

        # 将起点加入开放列表
        start_node = AStarNode(start, 0, self.chebyshev_distance(start, goal))
        heapq.heappush(open_list, start_node)

        iterations = 0
        while open_list and iterations < max_iterations:
            iterations += 1

            # 获取f_cost最小的节点
            current_node = heapq.heappop(open_list)

            # 检查是否到达终点
            distance_to_goal = current_node.position.distance_to(goal)
            if distance_to_goal < self.grid_size * 2:
                return self._reconstruct_path(current_node)

            # 将当前节点加入关闭列表
            closed_set.add((current_node.position.x, current_node.position.y))

            # 检查所有相邻节点
            for neighbor_pos in self.get_neighbors(current_node.position):
                # 如果在关闭列表中，跳过
                if (neighbor_pos.x, neighbor_pos.y) in closed_set:
                    continue

                # 如果被阻挡，跳过
                if self.is_position_blocked(neighbor_pos, obstacles, moving_role):
                    continue

                # 计算移动成本（所有方向移动成本相同）
                move_cost = 1.0

                g_cost = current_node.g_cost + move_cost
                h_cost = self.chebyshev_distance(neighbor_pos, goal)

                # 检查是否已经在开放列表中
                existing_node = None
                for node in open_list:
                    if (abs(node.position.x - neighbor_pos.x) < self.grid_size and
                        abs(node.position.y - neighbor_pos.y) < self.grid_size):
                        existing_node = node
                        break

                if existing_node:
                    # 如果找到更好的路径，更新节点
                    if g_cost < existing_node.g_cost:
                        existing_node.g_cost = g_cost
                        existing_node.f_cost = g_cost + existing_node.h_cost
                        existing_node.parent = current_node
                else:
                    # 添加新节点到开放列表
                    new_node = AStarNode(neighbor_pos, g_cost, h_cost, current_node)
                    heapq.heappush(open_list, new_node)

        # 没有找到路径
        return []

    def _reconstruct_path(self, goal_node: AStarNode) -> List[Position]:
        """重建路径"""
        path = []
        current = goal_node

        while current:
            path.append(current.position)
            current = current.parent

        # 反转路径，使其从起点到终点
        path.reverse()
        return path

    def get_next_move_position(self, role: Role, target: Position,
                              move_distance: float,
                              obstacles: Optional[List[Position]] = None) -> Position:
        """
        获取下一个移动位置
        使用A*算法找到路径，然后返回在移动距离内的下一个位置
        """
        path = self.find_path(role.position, target, obstacles, role)

        if not path:
            # 如果找不到路径，返回原始位置
            return role.position

        if len(path) <= 1:
            # 已经在目标位置
            return role.position

        # 检查路径上的每个点，找到在移动距离内的最远点
        accumulated_distance = 0.0
        for i in range(1, len(path)):
            segment_distance = path[i-1].distance_to(path[i])

            if accumulated_distance + segment_distance <= move_distance:
                accumulated_distance += segment_distance
            else:
                # 这个点超出了移动距离
                if i == 1:
                    # 第一个移动就超出了距离，进行插值
                    ratio = move_distance / segment_distance
                    new_x = path[0].x + (path[1].x - path[0].x) * ratio
                    new_y = path[0].y + (path[1].y - path[0].y) * ratio
                    return Position(new_x, new_y)
                else:
                    # 返回前一个点
                    return path[i-1]

        # 可以到达路径的最后一个点
        return path[-1]