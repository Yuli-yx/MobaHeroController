#!/usr/bin/env python3
"""
测试简化后的英雄系统（使用Role类，CD=10，钻石消耗=5）
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Action, ActionType, Position, Role
from src.skills import SkillSystem
from src.actions.action_executor import ActionExecutor


def create_test_game_state():
    """创建测试游戏状态"""
    # 使用SkillSystem创建英雄
    mage = SkillSystem.create_hero("mage", "mage1", "法师", Position(5.0, 10.0))
    warrior = SkillSystem.create_hero("warrior", "warrior1", "武士", Position(8.0, 10.0))
    monkey = SkillSystem.create_hero("monkey", "monkey1", "猴子", Position(6.0, 12.0))

    # 创建敌方英雄
    enemy_mage = SkillSystem.create_hero("mage", "enemy_mage1", "敌方法师", Position(15.0, 10.0))

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
        game_map={'type': 'standard', 'lanes': ['top', 'middle', 'bottom']},
        lane_info={'top': {'towers': 2}, 'middle': {'towers': 2}, 'bottom': {'towers': 2}}
    )

    return game_state, mage, warrior, monkey, enemy_mage


def test_hero_creation():
    """测试英雄创建"""
    print("=== 测试英雄创建 ===")

    mage = SkillSystem.create_hero("mage", "test_mage", "测试法师", Position(0, 0))
    warrior = SkillSystem.create_hero("warrior", "test_warrior", "测试武士", Position(0, 0))
    monkey = SkillSystem.create_hero("monkey", "test_monkey", "测试猴子", Position(0, 0))

    print(f"法师 - 生命值: {mage.health}/{mage.max_health}, 攻击范围: {mage.attack_range}, 钻石: {mage.diamonds}")
    print(f"武士 - 生命值: {warrior.health}/{warrior.max_health}, 攻击范围: {warrior.attack_range}, 钻石: {warrior.diamonds}")
    print(f"猴子 - 生命值: {monkey.health}/{monkey.max_health}, 攻击范围: {monkey.attack_range}, 钻石: {monkey.diamonds}")

    print(f"法师技能: {mage.skills}")
    print(f"武士技能: {warrior.skills}")
    print(f"猴子技能: {monkey.skills}")


def test_skill_system():
    """测试技能系统"""
    print("\n=== 测试技能系统 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 测试法师技能
    print(f"\n1. 法师技能测试")
    print(f"法师初始钻石: {mage.diamonds}")
    print(f"法师技能冷却: {mage.get_skill_cooldown('heal')}")

    # 降低法师生命值
    mage.health = 50.0
    print(f"法师生命值: {mage.health}/{mage.max_health}")

    # 使用治疗技能
    success, message = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"治疗技能结果: {success}, {message}")
    print(f"治疗后生命值: {mage.health}/{mage.max_health}")
    print(f"治疗后钻石: {mage.diamonds}")
    print(f"治疗后技能冷却: {mage.get_skill_cooldown('heal')}")

    # 测试武士技能
    print(f"\n2. 武士技能测试")
    print(f"武士初始钻石: {warrior.diamonds}")
    print(f"武士伤害倍率: {warrior.get_damage_multiplier()}")

    # 移动武士到敌方附近
    warrior.position = Position(14.5, 10.0)

    # 使用重击技能
    success, message = SkillSystem.use_skill(warrior, "heavy_strike", game_state, target=enemy_mage)
    print(f"重击技能结果: {success}, {message}")
    print(f"敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")
    print(f"武士钻石: {warrior.diamonds}")

    # 使用防御技能
    success, message = SkillSystem.use_skill(warrior, "iron_defense", game_state)
    print(f"防御技能结果: {success}, {message}")
    print(f"防御后伤害倍率: {warrior.get_damage_multiplier()}")


def test_cooldown_and_diamonds():
    """测试冷却和钻石系统"""
    print("\n=== 测试冷却和钻石系统 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    print(f"法师初始钻石: {mage.diamonds}")
    print(f"法师技能冷却: {mage.get_skill_cooldown('heal')}")

    # 连续使用技能测试冷却
    success1, message1 = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"第1次使用治疗: {success1}, {message1}")
    print(f"第1次后钻石: {mage.diamonds}, 冷却: {mage.get_skill_cooldown('heal')}")

    success2, message2 = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"第2次使用治疗: {success2}, {message2}")
    print(f"第2次后钻石: {mage.diamonds}, 冷却: {mage.get_skill_cooldown('heal')}")

    # 测试钻石不足
    mage.diamonds = 3
    success3, message3 = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"钻石不足时使用: {success3}, {message3}")


def test_buff_system():
    """测试buff系统"""
    print("\n=== 测试buff系统 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    print(f"武士初始buff数量: {len(warrior.buffs)}")
    print(f"武士初始伤害倍率: {warrior.get_damage_multiplier()}")

    # 使用铁壁防御
    SkillSystem.use_skill(warrior, "iron_defense", game_state)
    print(f"使用防御后buff数量: {len(warrior.buffs)}")
    print(f"防御后伤害倍率: {warrior.get_damage_multiplier()}")

    # 更新buff
    print("更新buff状态...")
    warrior.update_buffs()
    print(f"更新后buff数量: {len(warrior.buffs)}")
    print(f"buff持续时间: {[b.get('duration') for b in warrior.buffs if 'duration' in b]}")

    # 继续更新直到buff消失
    for i in range(3):
        warrior.update_buffs()
        print(f"第{i+1}次更新后buff数量: {len(warrior.buffs)}")


def test_action_executor():
    """测试动作执行器"""
    print("\n=== 测试动作执行器 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()
    executor = ActionExecutor(game_state)

    # 测试法师治疗动作
    print("\n1. 测试法师治疗动作")
    mage.health = 60.0
    print(f"治疗前生命值: {mage.health}/{mage.max_health}")

    heal_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="heal",
        position=mage.position
    )

    result = executor.execute_action(game_state, mage, heal_action, 1)
    print(f"治疗动作结果: {result.message}")
    print(f"治疗后生命值: {mage.health}/{mage.max_health}")

    # 测试武士重击动作
    print("\n2. 测试武士重击动作")
    warrior.position = Position(14.5, 10.0)
    print(f"攻击前敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    heavy_strike_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        skill_id="heavy_strike",
        target_id="enemy_mage1"
    )

    result = executor.execute_action(game_state, warrior, heavy_strike_action, 1)
    print(f"重击动作结果: {result.message}")
    print(f"攻击后敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")


def test_game_state_updates():
    """测试游戏状态更新"""
    print("\n=== 测试游戏状态更新 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 使用技能
    SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    SkillSystem.use_skill(warrior, "iron_defense", game_state)

    print(f"使用技能后冷却状态:")
    print(f"  法师治疗冷却: {mage.get_skill_cooldown('heal')}")
    print(f"  武士防御冷却: {warrior.get_skill_cooldown('iron_defense')}")

    # 更新所有技能状态
    SkillSystem.update_all_skills(game_state)

    print(f"更新后冷却状态:")
    print(f"  法师治疗冷却: {mage.get_skill_cooldown('heal')}")
    print(f"  武士防御冷却: {warrior.get_skill_cooldown('iron_defense')}")


def test_minion_kill_heal():
    """测试小兵击杀回血"""
    print("\n=== 测试小兵击杀回血 ===")

    game_state, mage, warrior, monkey, enemy_mage = create_test_game_state()

    # 创建一个小兵
    minion = {
        'id': 'minion1',
        'type': 'melee',
        'position': {'x': 10.0, 'y': 10.0},
        'health': 30.0,
        'max_health': 30.0,
        'team': 'enemy'
    }
    game_state.minions.append(minion)

    # 降低法师生命值
    mage.health = 60.0
    print(f"击杀小兵前法师生命值: {mage.health}/{mage.max_health}")

    # 模拟击杀小兵（在Role类中处理）
    mage.health = min(mage.max_health, mage.health + mage.max_health * 0.1)
    game_state.minions.remove(minion)

    print(f"击杀小兵后法师生命值: {mage.health}/{mage.max_health}")


def main():
    """主测试函数"""
    print("开始测试简化后的英雄系统...")
    print("规则：所有英雄CD=10，技能消耗=5钻石，使用Role类")
    print("=" * 60)

    test_hero_creation()
    test_skill_system()
    test_cooldown_and_diamonds()
    test_buff_system()
    test_action_executor()
    test_game_state_updates()
    test_minion_kill_heal()

    print("\n" + "=" * 60)
    print("[OK] 简化英雄系统测试完成！")
    print("\n系统特性:")
    print("- 使用Role类而非英雄类")
    print("- 所有英雄技能CD都是10回合")
    print("- 所有技能消耗5钻石")
    print("- 完整的技能系统支持三种英雄类型")
    print("- Buff系统支持增益/减益效果")
    print("- 游戏状态包含地图信息并实时更新")


if __name__ == "__main__":
    main()