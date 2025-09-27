#!/usr/bin/env python3
"""
测试英雄系统功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Action, ActionType, Position
from src.heroes import Mage, Warrior, Monkey
from src.actions.action_executor import ActionExecutor
from src.map.game_map import GameMap


def create_test_game_state():
    """创建测试游戏状态"""
    # 创建英雄
    mage = Mage("mage1", "法师", Position(5.0, 10.0))
    warrior = Warrior("warrior1", "武士", Position(8.0, 10.0))
    monkey = Monkey("monkey1", "猴子", Position(6.0, 12.0))

    # 创建敌方英雄
    enemy_mage = Mage("enemy_mage1", "敌方法师", Position(15.0, 10.0))

    # 创建游戏地图
    game_map = GameMap.create_standard_map()

    # 创建游戏状态
    game_state = GameState(
        roles={"mage1": mage, "warrior1": warrior, "monkey1": monkey},
        enemies={"enemy_mage1": enemy_mage},
        towers=[],
        crystals=[],
        minions=[],
        current_turn=1,
        map_width=30.0,
        map_height=20.0,
        game_map=game_map
    )

    return game_state, mage, warrior, monkey, enemy_mage


def test_mage_skills():
    """测试法师技能"""
    print("=== 测试法师技能 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()
    executor = ActionExecutor(game_state)

    # 测试治疗技能
    print("\n1. 测试治疗技能")
    print(f"治疗前生命值: {mage.health}/{mage.max_health}")

    # 降低法师生命值
    mage.health = 50.0
    print(f"降低后生命值: {mage.health}/{mage.max_health}")

    # 使用治疗技能
    heal_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="heal",
        position=mage.position
    )

    result = executor.execute_action(game_state, mage, heal_action, 1)
    print(f"治疗结果: {result.message}")
    print(f"治疗后生命值: {mage.health}/{mage.max_health}")

    # 测试范围控制技能
    print("\n2. 测试范围控制技能")
    area_control_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="area_control",
        position=enemy_mage.position
    )

    result = executor.execute_action(game_state, mage, area_control_action, 1)
    print(f"范围控制结果: {result.message}")

    # 检查敌方是否被控制
    if hasattr(enemy_mage, 'can_move'):
        print(f"敌方法师是否可以移动: {enemy_mage.can_move()}")
        print(f"敌方法师是否可以使用技能: {enemy_mage.can_use_skill()}")


def test_warrior_skills():
    """测试武士技能"""
    print("\n=== 测试武士技能 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()
    executor = ActionExecutor(game_state)

    # 测试重击技能
    print("\n1. 测试重击技能")
    print(f"敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 移动武士到攻击范围
    warrior.position = Position(14.5, 10.0)  # 在攻击范围内

    heavy_strike_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        skill_id="heavy_strike",
        target_id="enemy_mage1"
    )

    result = executor.execute_action(game_state, warrior, heavy_strike_action, 1)
    print(f"重击结果: {result.message}")
    print(f"敌方剩余生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 测试铁壁防御技能
    print("\n2. 测试铁壁防御技能")
    print(f"武士防御倍率: {warrior.get_damage_multiplier()}")

    iron_defense_action = Action(
        action_type=ActionType.SKILL_SUPPORT,
        skill_id="iron_defense",
        target_id="warrior1"
    )

    result = executor.execute_action(game_state, warrior, iron_defense_action, 1)
    print(f"铁壁防御结果: {result.message}")
    print(f"防御后伤害倍率: {warrior.get_damage_multiplier()}")
    print(f"防御buff持续时间: {[b.duration for b in warrior.buffs if b.name == 'iron_defense']}")


def test_monkey_skills():
    """测试猴子技能"""
    print("\n=== 测试猴子技能 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()
    executor = ActionExecutor(game_state)

    # 测试腐蚀打击技能
    print("\n1. 测试腐蚀打击技能")
    print(f"敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 移动猴子到攻击范围
    monkey.position = Position(13.0, 10.0)

    corrosive_strike_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        skill_id="corrosive_strike",
        target_id="enemy_mage1"
    )

    result = executor.execute_action(game_state, monkey, corrosive_strike_action, 1)
    print(f"腐蚀打击结果: {result.message}")
    print(f"敌方剩余生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 检查腐蚀效果
    corrosion_buffs = [b for b in enemy_mage.buffs if b.name == 'corrosion']
    if corrosion_buffs:
        print(f"腐蚀buff持续时间: {corrosion_buffs[0].duration}")
        print(f"腐蚀伤害值: {corrosion_buffs[0].value}")

    # 测试跳跃技能
    print("\n2. 测试跳跃技能")
    old_position = Position(monkey.position.x, monkey.position.y)
    target_position = Position(10.0, 8.0)

    print(f"跳跃前位置: ({old_position.x}, {old_position.y})")

    leap_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="leap",
        position=target_position
    )

    result = executor.execute_action(game_state, monkey, leap_action, 1)
    print(f"跳跃结果: {result.message}")
    print(f"跳跃后位置: ({monkey.position.x}, {monkey.position.y})")


def test_vision_system():
    """测试视野系统"""
    print("\n=== 测试视野系统 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 测试法师视野
    visible_enemies = game_state.get_visible_enemies("mage1")
    print(f"法师可见的敌方单位数量: {len(visible_enemies)}")

    # 将敌方移出视野范围
    enemy_mage.position = Position(20.0, 10.0)
    visible_enemies = game_state.get_visible_enemies("mage1")
    print(f"敌方移出视野后可见数量: {len(visible_enemies)}")

    # 测试视野范围检查
    in_range = mage.is_in_vision_range(Position(7.0, 10.0))
    out_range = mage.is_in_vision_range(Position(20.0, 10.0))
    print(f"位置(7,10)在视野范围内: {in_range}")
    print(f"位置(20,10)在视野范围内: {out_range}")


def test_minion_kill_heal():
    """测试小兵击杀回血机制"""
    print("\n=== 测试小兵击杀回血机制 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 创建一个小兵
    minion = {
        'id': 'minion1',
        'type': 'melee',
        'position': {'x': 10.0, 'y': 10.0},
        'health': 50.0,
        'max_health': 50.0,
        'team': 'enemy'
    }
    game_state.minions.append(minion)

    # 降低法师生命值
    mage.health = 30.0
    print(f"击杀小兵前法师生命值: {mage.health}/{mage.max_health}")

    # 模拟击杀小兵
    game_state.process_minion_kill("mage1", minion)

    print(f"击杀小兵后法师生命值: {mage.health}/{mage.max_health}")
    print(f"法师击杀小兵数量: {mage.minion_kills}")


def test_buff_system():
    """测试buff系统"""
    print("\n=== 测试buff系统 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 给武士添加铁壁防御buff
    from src.heroes.base_hero import Buff
    defense_buff = Buff(
        name="test_defense",
        duration=3,
        effect_type="damage_reduction",
        value=0.5,
        description="测试防御buff"
    )
    warrior.add_buff(defense_buff)

    print(f"添加buff后伤害倍率: {warrior.get_damage_multiplier()}")
    print(f"buff持续时间: {defense_buff.duration}")

    # 更新buff
    warrior.update_buffs()
    print(f"更新后buff持续时间: {defense_buff.duration}")

    # 继续更新直到buff消失
    for i in range(3):
        warrior.update_buffs()
        print(f"第{i+1}次更新后持续时间: {defense_buff.duration if defense_buff in warrior.buffs else 0}")


def main():
    """主测试函数"""
    print("开始测试英雄系统...")
    print("=" * 50)

    # 运行所有测试
    test_mage_skills()
    test_warrior_skills()
    test_monkey_skills()
    test_vision_system()
    test_minion_kill_heal()
    test_buff_system()

    print("\n" + "=" * 50)
    print("[OK] 英雄系统测试完成！")


if __name__ == "__main__":
    main()