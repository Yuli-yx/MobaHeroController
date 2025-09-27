#!/usr/bin/env python3
"""
英雄系统使用示例
演示如何创建和使用三种不同的英雄
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Action, ActionType, Position
from src.heroes import Mage, Warrior, Monkey
from src.actions.action_executor import ActionExecutor
from src.map.game_map import GameMap


def main():
    """主函数演示英雄系统"""
    print("=== MOBA英雄系统演示 ===")
    print()

    # 1. 创建英雄
    print("1. 创建英雄")
    mage = Mage("mage_001", "火焰法师", Position(5.0, 10.0))
    warrior = Warrior("warrior_001", "钢铁武士", Position(8.0, 10.0))
    monkey = Monkey("monkey_001", "灵猴", Position(6.0, 12.0))

    print(f"创建法师: {mage.name} - 生命值:{mage.health}/{mage.max_health}, 攻击范围:{mage.attack_range}")
    print(f"创建武士: {warrior.name} - 生命值:{warrior.health}/{warrior.max_health}, 攻击范围:{warrior.attack_range}")
    print(f"创建猴子: {monkey.name} - 生命值:{monkey.health}/{monkey.max_health}, 攻击范围:{monkey.attack_range}")
    print()

    # 2. 显示英雄技能
    print("2. 英雄技能列表")
    for hero in [mage, warrior, monkey]:
        print(f"\n{hero.name}的技能:")
        for skill in hero.skills:
            if hasattr(hero, 'get_skill_description'):
                print(f"  - {skill}: {hero.get_skill_description(skill)}")
            else:
                print(f"  - {skill}")
    print()

    # 3. 创建游戏状态
    print("3. 创建游戏环境")
    game_map = GameMap.create_standard_map()

    # 创建敌方英雄
    enemy_mage = Mage("enemy_mage_001", "敌方法师", Position(15.0, 10.0))
    enemy_warrior = Warrior("enemy_warrior_001", "敌方武士", Position(18.0, 10.0))

    game_state = GameState(
        roles={"mage_001": mage, "warrior_001": warrior, "monkey_001": monkey},
        enemies={"enemy_mage_001": enemy_mage, "enemy_warrior_001": enemy_warrior},
        towers=[],
        crystals=[],
        minions=[],
        current_turn=1,
        map_width=30.0,
        map_height=20.0,
        game_map=game_map
    )

    print(f"地图大小: {game_state.map_width} x {game_state.map_height}")
    print(f"我方英雄数量: {len(game_state.roles)}")
    print(f"敌方英雄数量: {len(game_state.enemies)}")
    print()

    # 4. 演示战斗场景
    print("4. 演示战斗场景")
    executor = ActionExecutor(game_state)

    # 4.1 法师治疗演示
    print("\n4.1 法师治疗演示")
    mage.health = 40.0  # 降低法师生命值
    print(f"法师受伤后生命值: {mage.health}/{mage.max_health}")

    heal_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="heal",
        position=mage.position
    )

    result = executor.execute_action(game_state, mage, heal_action, 1)
    print(f"治疗结果: {result.message}")
    print(f"治疗后生命值: {mage.health}/{mage.max_health}")

    # 4.2 武士防御演示
    print("\n4.2 武士防御演示")
    print(f"武士当前伤害倍率: {warrior.get_damage_multiplier()}")

    defense_action = Action(
        action_type=ActionType.SKILL_SUPPORT,
        skill_id="iron_defense",
        target_id="warrior_001"
    )

    result = executor.execute_action(game_state, warrior, defense_action, 1)
    print(f"防御结果: {result.message}")
    print(f"防御后伤害倍率: {warrior.get_damage_multiplier()}")

    # 4.3 猴子移动演示
    print("\n4.3 猴子跳跃移动演示")
    old_pos = Position(monkey.position.x, monkey.position.y)
    target_pos = Position(10.0, 8.0)

    print(f"跳跃前位置: ({old_pos.x}, {old_pos.y})")

    leap_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="leap",
        position=target_pos
    )

    result = executor.execute_action(game_state, monkey, leap_action, 1)
    print(f"跳跃结果: {result.message}")
    print(f"跳跃后位置: ({monkey.position.x}, {monkey.position.y})")

    # 4.4 战斗演示
    print("\n4.4 技能战斗演示")

    # 移动武士到敌方附近
    warrior.position = Position(16.5, 10.0)
    print(f"武士移动到位置: ({warrior.position.x}, {warrior.position.y})")

    # 武士使用重击
    heavy_strike_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        skill_id="heavy_strike",
        target_id="enemy_mage_001"
    )

    result = executor.execute_action(game_state, warrior, heavy_strike_action, 1)
    print(f"重击结果: {result.message}")
    print(f"敌方法师剩余生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 5. 状态更新演示
    print("\n5. 状态更新演示")
    print("更新前:")
    print(f"  法师技能冷却: {mage.get_skill_cooldown('heal')}")
    print(f"  武士技能冷却: {warrior.get_skill_cooldown('iron_defense')}")
    print(f"  猴子技能冷却: {monkey.get_skill_cooldown('leap')}")

    # 更新游戏状态
    game_state.update_all_heroes()

    print("更新后:")
    print(f"  法师技能冷却: {mage.get_skill_cooldown('heal')}")
    print(f"  武士技能冷却: {warrior.get_skill_cooldown('iron_defense')}")
    print(f"  猴子技能冷却: {monkey.get_skill_cooldown('leap')}")

    # 6. 小兵击杀回血演示
    print("\n6. 小兵击杀回血演示")

    # 创建一个小兵
    minion = {
        'id': 'minion_001',
        'type': 'melee',
        'position': {'x': 12.0, 'y': 10.0},
        'health': 30.0,
        'max_health': 30.0,
        'team': 'enemy'
    }
    game_state.minions.append(minion)

    # 降低法师生命值
    mage.health = 60.0
    print(f"击杀小兵前法师生命值: {mage.health}/{mage.max_health}")

    # 模拟法师击杀小兵
    game_state.process_minion_kill("mage_001", minion)

    print(f"击杀小兵后法师生命值: {mage.health}/{mage.max_health}")
    print(f"法师击杀小兵数量: {mage.minion_kills}")

    # 7. 地图系统演示
    print("\n7. 地图系统演示")
    if game_state.game_map:
        defense_info = game_state.game_map.get_defense_map()
        print(f"地图防御信息:")
        print(f"  总防御塔数量: {defense_info['total_towers']}")
        print(f"  总水晶数量: {defense_info['total_crystals']}")

        for lane_name, lane_info in defense_info['lanes'].items():
            print(f"  {lane_name}: {lane_info['towers']}座防御塔")

    print("\n=== 演示完成 ===")
    print("\n这个演示展示了:")
    print("- 三种不同英雄的创建和属性")
    print("- 各自独特的技能系统")
    print("- 技能的执行和效果")
    print("- 状态更新和冷却系统")
    print("- 小兵击杀回血机制")
    print("- 地图和防御系统")


if __name__ == "__main__":
    main()