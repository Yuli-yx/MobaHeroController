#!/usr/bin/env python3
"""
简化后的MOBA系统使用示例
使用Role类，CD=10，钻石消耗=5
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Action, ActionType, Position, Role
from src.skills import SkillSystem
from src.actions.action_executor import ActionExecutor


def create_game_with_heroes():
    """创建包含英雄的游戏状态"""
    print("=== 创建英雄 ===")

    # 使用SkillSystem创建三种英雄
    mage = SkillSystem.create_hero("mage", "mage_001", "火焰法师", Position(5.0, 10.0))
    warrior = SkillSystem.create_hero("warrior", "warrior_001", "钢铁武士", Position(8.0, 10.0))
    monkey = SkillSystem.create_hero("monkey", "monkey_001", "灵猴", Position(6.0, 12.0))

    # 创建敌方英雄
    enemy_mage = SkillSystem.create_hero("mage", "enemy_mage_001", "敌方法师", Position(20.0, 10.0))
    enemy_warrior = SkillSystem.create_hero("warrior", "enemy_warrior_001", "敌方武士", Position(22.0, 10.0))

    # 显示英雄信息
    print(f"法师: {mage.name} - HP:{mage.health}/{mage.max_health} 范围:{mage.attack_range} 钻石:{mage.diamonds}")
    print(f"武士: {warrior.name} - HP:{warrior.health}/{warrior.max_health} 范围:{warrior.attack_range} 钻石:{warrior.diamonds}")
    print(f"猴子: {monkey.name} - HP:{monkey.health}/{monkey.max_health} 范围:{monkey.attack_range} 钻石:{monkey.diamonds}")

    # 创建游戏状态
    game_state = GameState(
        roles={"mage_001": mage, "warrior_001": warrior, "monkey_001": monkey},
        enemies={"enemy_mage_001": enemy_mage, "enemy_warrior_001": enemy_warrior},
        towers=[],
        crystals=[],
        minions=[],
        current_turn=1,
        map_width=30.0,
        map_height=20.0,
        game_map={
            'type': 'three_lane',
            'width': 30,
            'height': 20,
            'lanes': {
                'top': {'start': (2, 16), 'end': (28, 16), 'towers': 2},
                'middle': {'start': (2, 10), 'end': (28, 10), 'towers': 2},
                'bottom': {'start': (2, 4), 'end': (28, 4), 'towers': 2}
            }
        },
        lane_info={
            'top': {'friendly_towers': 0, 'enemy_towers': 2},
            'middle': {'friendly_towers': 0, 'enemy_towers': 2},
            'bottom': {'friendly_towers': 0, 'enemy_towers': 2}
        }
    )

    return game_state


def demonstrate_skills():
    """演示技能使用"""
    print("\n=== 技能演示 ===")

    game_state = create_game_with_heroes()
    mage = game_state.roles["mage_001"]
    warrior = game_state.roles["warrior_001"]
    monkey = game_state.roles["monkey_001"]
    enemy_mage = game_state.enemies["enemy_mage_001"]

    # 显示技能列表
    print("英雄技能:")
    for hero in [mage, warrior, monkey]:
        print(f"{hero.name}: {hero.skills}")
        for skill in hero.skills:
            print(f"  - {skill}: {SkillSystem.get_skill_description(hero.hero_type, skill)}")

    # 演法师技能
    print(f"\n法师技能演示:")
    print(f"初始钻石: {mage.diamonds}")

    # 治疗技能
    mage.health = 50.0
    print(f"受伤后生命值: {mage.health}/{mage.max_health}")
    success, message = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"治疗结果: {message}")
    print(f"治疗后生命值: {mage.health}/{mage.max_health}")
    print(f"剩余钻石: {mage.diamonds}")
    print(f"技能冷却: {mage.get_skill_cooldown('heal')}回合")

    # 演武士技能
    print(f"\n武士技能演示:")
    warrior.position = Position(19.0, 10.0)  # 移动到敌方附近
    print(f"敌方生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 重击技能
    success, message = SkillSystem.use_skill(warrior, "heavy_strike", game_state, target=enemy_mage)
    print(f"重击结果: {message}")
    print(f"敌方剩余生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    # 防御技能
    success, message = SkillSystem.use_skill(warrior, "iron_defense", game_state)
    print(f"防御结果: {message}")
    print(f"伤害倍率: {warrior.get_damage_multiplier()}")

    # 演猴子技能
    print(f"\n猴子技能演示:")
    old_pos = Position(monkey.position.x, monkey.position.y)
    target_pos = Position(15.0, 8.0)

    print(f"当前位置: ({old_pos.x}, {old_pos.y})")

    # 跳跃技能
    success, message = SkillSystem.use_skill(monkey, "leap", game_state, position=target_pos)
    print(f"跳跃结果: {message}")
    print(f"新位置: ({monkey.position.x}, {monkey.position.y})")


def demonstrate_cooldown_and_diamonds():
    """演示冷却和钻石系统"""
    print("\n=== 冷却和钻石系统演示 ===")

    game_state = create_game_with_heroes()
    mage = game_state.roles["mage_001"]

    print(f"法师初始钻石: {mage.diamonds}")

    # 使用技能
    SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"使用1次技能后:")
    print(f"  剩余钻石: {mage.diamonds}")
    print(f"  技能冷却: {mage.get_skill_cooldown('heal')}回合")

    # 尝试连续使用（应该失败）
    success, message = SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    print(f"第2次使用: {success} - {message}")

    # 钻石不足测试
    mage.diamonds = 3
    print(f"设置钻石为: {mage.diamonds}")
    success, message = SkillSystem.use_skill(mage, "area_control", game_state, position=mage.position)
    print(f"钻石不足时使用: {success} - {message}")


def demonstrate_buff_system():
    """演示buff系统"""
    print("\n=== Buff系统演示 ===")

    game_state = create_game_with_heroes()
    warrior = game_state.roles["warrior_001"]
    enemy_mage = game_state.enemies["enemy_mage_001"]

    print(f"武士初始状态:")
    print(f"  伤害倍率: {warrior.get_damage_multiplier()}")
    print(f"  Buff数量: {len(warrior.buffs)}")

    # 使用铁壁防御
    SkillSystem.use_skill(warrior, "iron_defense", game_state)
    print(f"使用防御后:")
    print(f"  伤害倍率: {warrior.get_damage_multiplier()}")
    print(f"  Buff数量: {len(warrior.buffs)}")
    for buff in warrior.buffs:
        print(f"    - {buff.get('name', 'unknown')}: {buff.get('description', 'no description')}")

    # 更新buff
    print("更新buff状态...")
    for i in range(4):
        warrior.update_buffs()
        print(f"  第{i+1}次更新后buff数量: {len(warrior.buffs)}")

    # 演示腐蚀buff
    print(f"\n腐蚀效果演示:")
    monkey = game_state.roles["monkey_001"]
    monkey.position = Position(19.0, 10.0)

    print(f"敌方法师生命值: {enemy_mage.health}/{enemy_mage.max_health}")
    SkillSystem.use_skill(monkey, "corrosive_strike", game_state, target=enemy_mage)
    print(f"腐蚀打击后生命值: {enemy_mage.health}/{enemy_mage.max_health}")

    for buff in enemy_mage.buffs:
        if buff.get('name') == 'corrosion':
            print(f"腐蚀buff: 持续{buff.get('duration')}回合, 每回合{buff.get('value')}点伤害")


def demonstrate_action_executor():
    """演示动作执行器"""
    print("\n=== 动作执行器演示 ===")

    game_state = create_game_with_heroes()
    executor = ActionExecutor(game_state)

    mage = game_state.roles["mage_001"]
    warrior = game_state.roles["warrior_001"]
    enemy_mage = game_state.enemies["enemy_mage_001"]

    # 演法师治疗动作
    print("法师治疗动作:")
    mage.health = 60.0
    print(f"治疗前: {mage.health}/{mage.max_health}")

    heal_action = Action(
        action_type=ActionType.SKILL_POSITION,
        skill_id="heal",
        position=mage.position
    )

    result = executor.execute_action(game_state, mage, heal_action, 1)
    print(f"执行结果: {result.message}")
    print(f"治疗后: {mage.health}/{mage.max_health}")

    # 演武士攻击动作
    print("\n武士重击动作:")
    warrior.position = Position(19.0, 10.0)
    print(f"攻击前敌方: {enemy_mage.health}/{enemy_mage.max_health}")

    attack_action = Action(
        action_type=ActionType.SKILL_ATTACK,
        skill_id="heavy_strike",
        target_id="enemy_mage_001"
    )

    result = executor.execute_action(game_state, warrior, attack_action, 1)
    print(f"执行结果: {result.message}")
    print(f"攻击后敌方: {enemy_mage.health}/{enemy_mage.max_health}")


def demonstrate_game_state_updates():
    """演示游戏状态更新"""
    print("\n=== 游戏状态更新演示 ===")

    game_state = create_game_with_heroes()

    # 使用一些技能
    mage = game_state.roles["mage_001"]
    warrior = game_state.roles["warrior_001"]

    SkillSystem.use_skill(mage, "heal", game_state, position=mage.position)
    SkillSystem.use_skill(warrior, "iron_defense", game_state)

    print(f"使用技能后冷却状态:")
    print(f"  法师治疗: {mage.get_skill_cooldown('heal')}回合")
    print(f"  武士防御: {warrior.get_skill_cooldown('iron_defense')}回合")

    # 更新游戏状态
    print("\n更新游戏状态...")
    SkillSystem.update_all_skills(game_state)

    print(f"更新后冷却状态:")
    print(f"  法师治疗: {mage.get_skill_cooldown('heal')}回合")
    print(f"  武士防御: {warrior.get_skill_cooldown('iron_defense')}回合")

    # 显示地图信息
    print(f"\n游戏地图信息:")
    if game_state.game_map:
        print(f"  地图类型: {game_state.game_map.get('type', 'unknown')}")
        print(f"  地图大小: {game_state.map_width} x {game_state.map_height}")
        if 'lanes' in game_state.game_map:
            print(f"  分路数量: {len(game_state.game_map['lanes'])}")
            for lane_name, lane_info in game_state.game_map['lanes'].items():
                print(f"    {lane_name}: {lane_info.get('towers', 0)}座塔")


def main():
    """主函数"""
    print("=== 简化后的MOBA系统演示 ===")
    print("新规则：所有英雄CD=10，技能消耗=5钻石，使用Role类")
    print("=" * 60)

    demonstrate_skills()
    demonstrate_cooldown_and_diamonds()
    demonstrate_buff_system()
    demonstrate_action_executor()
    demonstrate_game_state_updates()

    print("\n" + "=" * 60)
    print("=== 演示完成 ===")
    print("\n简化后的系统特点:")
    print("[OK] 使用Role类替代英雄类，架构更简单")
    print("[OK] 所有英雄技能CD统一为10回合")
    print("[OK] 所有技能消耗统一为5钻石")
    print("[OK] 完整的技能系统支持三种英雄类型")
    print("[OK] Buff系统支持各种增益/减益效果")
    print("[OK] 游戏状态包含实时地图信息")
    print("[OK] 动作执行器完全兼容新系统")

    print("\n英雄技能总结:")
    print("法师(100HP/3范围): 治疗+范围控制")
    print("武士(200HP/1范围): 重击+防御")
    print("猴子(150HP/2范围): 腐蚀+跳跃")


if __name__ == "__main__":
    main()