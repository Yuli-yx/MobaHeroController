#!/usr/bin/env python3
"""
测试攻击障碍物检查功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Role, Action, ActionType, Position
from src.actions.action_executor import ActionValidator


def create_test_game_state_with_obstacles():
    """创建一个包含障碍物的测试游戏状态"""

    # 创建角色
    attacker = Role(
        id="hero1",
        name="攻击英雄",
        position=Position(5.0, 5.0),
        health=100.0,
        max_health=100.0,
        mana=50.0,
        max_mana=50.0,
        attack_damage=20.0,
        defense=10.0,
        move_speed=3.0,
        attack_range=12.0,
        skills=["fireball"],
        is_alive=True
    )

    target = Role(
        id="enemy1",
        name="敌方英雄",
        position=Position(15.0, 5.0),
        health=80.0,
        max_health=100.0,
        mana=40.0,
        max_mana=50.0,
        attack_damage=15.0,
        defense=8.0,
        move_speed=2.5,
        attack_range=6.0,
        skills=["icebolt"],
        is_alive=True
    )

    # 创建障碍物（塔）
    tower_obstacle = {
        'position': {'x': 10.0, 'y': 5.0},
        'type': 'defense_tower',
        'health': 200.0
    }

    # 创建游戏状态
    game_state = GameState(
        roles={"hero1": attacker},
        enemies={"enemy1": target},
        towers=[tower_obstacle],
        crystals=[],
        minions=[],
        current_turn=1,
        map_width=20.0,
        map_height=10.0
    )

    return game_state, attacker, target


def create_test_game_state_clear_path():
    """创建一个没有障碍物的测试游戏状态（路径畅通）"""

    # 创建角色
    attacker = Role(
        id="hero1",
        name="攻击英雄",
        position=Position(5.0, 5.0),
        health=100.0,
        max_health=100.0,
        mana=50.0,
        max_mana=50.0,
        attack_damage=20.0,
        defense=10.0,
        move_speed=3.0,
        attack_range=12.0,
        skills=["fireball"],
        is_alive=True
    )

    target = Role(
        id="enemy1",
        name="敌方英雄",
        position=Position(12.0, 5.0),
        health=80.0,
        max_health=100.0,
        mana=40.0,
        max_mana=50.0,
        attack_damage=15.0,
        defense=8.0,
        move_speed=2.5,
        attack_range=6.0,
        skills=["icebolt"],
        is_alive=True
    )

    # 创建游戏状态（没有障碍物）
    game_state = GameState(
        roles={"hero1": attacker},
        enemies={"enemy1": target},
        towers=[],
        crystals=[],
        minions=[],
        current_turn=1,
        map_width=20.0,
        map_height=10.0
    )

    return game_state, attacker, target


def test_attack_with_obstacle():
    """测试有障碍物时的攻击验证"""
    print("=== 测试1：有障碍物的攻击 ===")

    game_state, attacker, target = create_test_game_state_with_obstacles()

    # 创建攻击动作
    attack_action = Action(
        action_type=ActionType.ATTACK,
        target_id="enemy1"
    )

    # 验证攻击动作
    is_valid, message = ActionValidator.validate_action(game_state, attacker, attack_action)

    print(f"攻击者位置: ({attacker.position.x}, {attacker.position.y})")
    print(f"目标位置: ({target.position.x}, {target.position.y})")
    print(f"攻击距离: {attacker.position.distance_to(target.position):.1f}")
    print(f"攻击范围: {attacker.attack_range}")
    print(f"障碍物位置: ({game_state.towers[0]['position']['x']}, {game_state.towers[0]['position']['y']})")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"消息: {message}")
    print()

    return is_valid


def test_attack_clear_path():
    """测试无障碍物时的攻击验证"""
    print("=== 测试2：无障碍物的攻击 ===")

    game_state, attacker, target = create_test_game_state_clear_path()

    # 创建攻击动作
    attack_action = Action(
        action_type=ActionType.ATTACK,
        target_id="enemy1"
    )

    # 验证攻击动作
    is_valid, message = ActionValidator.validate_action(game_state, attacker, attack_action)

    print(f"攻击者位置: ({attacker.position.x}, {attacker.position.y})")
    print(f"目标位置: ({target.position.x}, {target.position.y})")
    print(f"攻击距离: {attacker.position.distance_to(target.position):.1f}")
    print(f"攻击范围: {attacker.attack_range}")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"消息: {message}")
    print()

    return is_valid


def test_skill_attack_with_obstacle():
    """测试有障碍物时的技能攻击验证"""
    print("=== 测试3：有障碍物的技能攻击 ===")

    game_state, attacker, target = create_test_game_state_with_obstacles()

    # 创建技能攻击动作
    skill_attack_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        target_id="enemy1",
        skill_id="fireball"
    )

    # 验证技能攻击动作
    is_valid, message = ActionValidator.validate_action(game_state, attacker, skill_attack_action)

    print(f"攻击者位置: ({attacker.position.x}, {attacker.position.y})")
    print(f"目标位置: ({target.position.x}, {target.position.y})")
    print(f"技能: {skill_attack_action.skill_id}")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"消息: {message}")
    print()

    return is_valid


def main():
    """主测试函数"""
    print("开始测试攻击障碍物检查功能...")
    print("=" * 50)
    print()

    # 运行测试
    test1_result = test_attack_with_obstacle()
    test2_result = test_attack_clear_path()
    test3_result = test_skill_attack_with_obstacle()

    # 总结结果
    print("=== 测试结果总结 ===")
    print(f"测试1（有障碍物攻击）: {'预期失败' if not test1_result else '意外通过'}")
    print(f"测试2（无障碍物攻击）: {'预期通过' if test2_result else '意外失败'}")
    print(f"测试3（有障碍物技能攻击）: {'预期失败' if not test3_result else '意外通过'}")

    if not test1_result and test2_result and not test3_result:
        print("\n[OK] 所有测试都按预期通过！障碍物检查功能正常工作。")
    else:
        print("\n[ERROR] 某些测试结果与预期不符，需要检查实现。")


if __name__ == "__main__":
    main()