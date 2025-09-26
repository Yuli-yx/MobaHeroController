#!/usr/bin/env python3
"""
A*算法测试脚本，包括BFS+A*组合功能测试
"""

from src.core.base import GameState, Role, Position
from src.pathfinding import PathFinder

def test_astar():
    """测试A*算法"""
    print("=== A*算法测试 ===")

    # 创建简单的游戏状态
    roles = {
        "test_role": Role(
            id="test_role",
            name="测试角色",
            position=Position(500, 500),  # 放在远离测试区域的位置
            health=100,
            max_health=100,
            mana=100,
            max_mana=100,
            attack_damage=10,
            defense=10,
            move_speed=50,
            attack_range=100,
            skills=[],
            is_alive=True
        )
    }

    enemies = {}

    game_state = GameState(
        roles=roles,
        enemies=enemies,
        towers=[],
        crystals=[],
        minions=[],
        current_turn=0,
        map_width=1000,
        map_height=1000
    )

    # 创建路径查找器
    path_finder = PathFinder(game_state)

    # 测试1: 简单直线移动
    print("\n--- 测试1: 简单直线移动 ---")
    start = Position(100, 100)
    goal = Position(200, 100)

    print(f"起点是否被阻挡: {path_finder.is_position_blocked(start)}")
    print(f"终点是否被阻挡: {path_finder.is_position_blocked(goal)}")
    print(f"切比雪夫距离: {path_finder.chebyshev_distance(start, goal)}")

    # 测试邻居节点获取
    print("起点邻居节点:")
    neighbors = path_finder.get_neighbors(start)
    for i, neighbor in enumerate(neighbors[:5]):  # 只显示前5个
        print(f"  邻居{i}: ({neighbor.x}, {neighbor.y}), 被阻挡: {path_finder.is_position_blocked(neighbor)}")

    path = path_finder.find_path(start, goal)
    print(f"起点: ({start.x}, {start.y})")
    print(f"终点: ({goal.x}, {goal.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"路径: {[(p.x, p.y) for p in path]}")
    else:
        print("未找到路径")

    # 测试2: 对角线移动
    print("\n--- 测试2: 对角线移动 ---")
    goal = Position(150, 150)
    path = path_finder.find_path(start, goal)
    print(f"起点: ({start.x}, {start.y})")
    print(f"终点: ({goal.x}, {goal.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"路径: {[(p.x, p.y) for p in path]}")
    else:
        print("未找到路径")

    # 测试3: 测试切比雪夫距离
    print("\n--- 测试3: 切比雪夫距离 ---")
    pos1 = Position(100, 100)
    pos2 = Position(150, 120)
    chebyshev_dist = path_finder.chebyshev_distance(pos1, pos2)
    euclidean_dist = pos1.distance_to(pos2)
    print(f"位置1: ({pos1.x}, {pos1.y})")
    print(f"位置2: ({pos2.x}, {pos2.y})")
    print(f"切比雪夫距离: {chebyshev_dist}")
    print(f"欧几里得距离: {euclidean_dist}")

    # 测试4: 获取下一个移动位置
    print("\n--- 测试4: 获取下一个移动位置 ---")
    role = roles["test_role"]
    target = Position(300, 300)
    move_distance = 50

    next_pos = path_finder.get_next_move_position(role, target, move_distance)
    print(f"角色当前位置: ({role.position.x}, {role.position.y})")
    print(f"目标位置: ({target.x}, {target.y})")
    print(f"移动距离: {move_distance}")
    print(f"下一个位置: ({next_pos.x}, {next_pos.y})")
    print(f"实际移动距离: {role.position.distance_to(next_pos)}")

def test_bfs_astar_combined():
    """测试BFS+A*组合功能"""
    print("\n=== BFS+A*组合功能测试 ===")

    # 创建有角色的游戏状态来模拟阻挡
    roles = {
        "test_role": Role(
            id="test_role",
            name="测试角色",
            position=Position(100, 100),
            health=100,
            max_health=100,
            mana=100,
            max_mana=100,
            attack_damage=10,
            defense=10,
            move_speed=50,
            attack_range=100,
            skills=[],
            is_alive=True
        ),
        "blocking_role": Role(
            id="blocking_role",
            name="阻挡角色",
            position=Position(200, 200),  # 阻挡目标位置
            health=100,
            max_health=100,
            mana=100,
            max_mana=100,
            attack_damage=10,
            defense=10,
            move_speed=50,
            attack_range=100,
            skills=[],
            is_alive=True
        )
    }

    enemies = {}

    game_state = GameState(
        roles=roles,
        enemies=enemies,
        towers=[],
        crystals=[],
        minions=[],
        current_turn=0,
        map_width=1000,
        map_height=1000
    )

    # 创建路径查找器
    path_finder = PathFinder(game_state)

    # 测试1: BFS查找最近的可通行位置
    print("\n--- 测试1: BFS查找最近的可通行位置 ---")
    blocked_pos = Position(200, 200)  # 被阻挡的位置

    print(f"位置 ({blocked_pos.x}, {blocked_pos.y}) 是否被阻挡: {path_finder.is_position_blocked(blocked_pos)}")

    nearest_traversable = path_finder.find_nearest_traversable_position(blocked_pos)
    if nearest_traversable:
        print(f"最近的可通行位置: ({nearest_traversable.x}, {nearest_traversable.y})")
        print(f"距离: {blocked_pos.distance_to(nearest_traversable):.2f}")
    else:
        print("未找到可通行位置")

    # 测试2: 起点被阻挡的情况
    print("\n--- 测试2: 起点被阻挡的情况 ---")
    start = Position(200, 200)  # 被阻挡的起点
    goal = Position(300, 300)   # 正常的终点

    path = path_finder.find_path(start, goal)
    print(f"起点: ({start.x}, {start.y})")
    print(f"终点: ({goal.x}, {goal.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"实际起点: ({path[0].x}, {path[0].y})")
        print(f"路径: {[(p.x, p.y) for p in path]}")
    else:
        print("未找到路径")

    # 测试3: 终点被阻挡的情况
    print("\n--- 测试3: 终点被阻挡的情况 ---")
    start = Position(300, 300)  # 正常的起点
    goal = Position(200, 200)   # 被阻挡的终点

    path = path_finder.find_path(start, goal)
    print(f"起点: ({start.x}, {start.y})")
    print(f"终点: ({goal.x}, {goal.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"实际终点: ({path[-1].x}, {path[-1].y})")
        print(f"路径: {[(p.x, p.y) for p in path]}")
    else:
        print("未找到路径")

    # 测试4: 起点和终点都被阻挡的情况
    print("\n--- 测试4: 起点和终点都被阻挡的情况 ---")
    start = Position(200, 200)  # 被阻挡的起点
    goal = Position(300, 100)   # 在阻挡角色附近的位置

    path = path_finder.find_path(start, goal)
    print(f"起点: ({start.x}, {start.y})")
    print(f"终点: ({goal.x}, {goal.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"实际起点: ({path[0].x}, {path[0].y})")
        print(f"实际终点: ({path[-1].x}, {path[-1].y})")
        print(f"路径: {[(p.x, p.y) for p in path]}")
    else:
        print("未找到路径")

    # 测试5: 在角色移动中使用BFS+A*组合
    print("\n--- 测试5: 在角色移动中使用BFS+A*组合 ---")
    role = roles["test_role"]
    target = Position(200, 200)  # 被阻挡的目标位置
    move_distance = 50

    next_pos = path_finder.get_next_move_position(role, target, move_distance)
    print(f"角色当前位置: ({role.position.x}, {role.position.y})")
    print(f"目标位置: ({target.x}, {target.y})")
    print(f"移动距离: {move_distance}")
    print(f"下一个位置: ({next_pos.x}, {next_pos.y})")
    print(f"实际移动距离: {role.position.distance_to(next_pos)}")

def test_complex_scenario():
    """测试复杂场景"""
    print("\n=== 复杂场景测试 ===")

    # 创建多个角色形成阻挡区域
    roles = {
        "mover": Role(
            id="mover",
            name="移动者",
            position=Position(100, 100),
            health=100,
            max_health=100,
            mana=100,
            max_mana=100,
            attack_damage=10,
            defense=10,
            move_speed=50,
            attack_range=100,
            skills=[],
            is_alive=True
        )
    }

    # 创建阻挡角色形成"墙"
    for i in range(5):
        roles[f"blocker_{i}"] = Role(
            id=f"blocker_{i}",
            name=f"阻挡者{i}",
            position=Position(200 + i * 10, 150),
            health=100,
            max_health=100,
            mana=100,
            max_mana=100,
            attack_damage=10,
            defense=10,
            move_speed=50,
            attack_range=100,
            skills=[],
            is_alive=True
        )

    enemies = {}

    game_state = GameState(
        roles=roles,
        enemies=enemies,
        towers=[],
        crystals=[],
        minions=[],
        current_turn=0,
        map_width=1000,
        map_height=1000
    )

    path_finder = PathFinder(game_state)

    # 测试绕过阻挡墙
    print("\n--- 测试绕过阻挡墙 ---")
    mover = roles["mover"]
    target = Position(300, 200)  # 目标在阻挡墙后面

    path = path_finder.find_path(mover.position, target, moving_role=mover)
    print(f"起点: ({mover.position.x}, {mover.position.y})")
    print(f"终点: ({target.x}, {target.y})")
    print(f"路径长度: {len(path)}")
    if path:
        print(f"路径: {[(p.x, p.y) for p in path]}")

        # 测试移动
        move_distance = 30
        next_pos = path_finder.get_next_move_position(mover, target, move_distance)
        print(f"下一个移动位置: ({next_pos.x}, {next_pos.y})")
        print(f"移动距离: {mover.position.distance_to(next_pos):.2f}")
    else:
        print("未找到路径")

if __name__ == "__main__":
    test_astar()
    test_bfs_astar_combined()
    test_complex_scenario()