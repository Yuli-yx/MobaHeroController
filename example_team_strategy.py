#!/usr/bin/env python3
"""
基于队伍位置的MOBA系统示例
展示防守方/挑战方机制和策略系统
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.base import GameState, Action, ActionType, Position, Role
from src.skills import SkillSystem
from src.actions.action_executor import ActionExecutor
from src.core.game_mechanics import GameMechanics
from src.strategies.position_strategy import PositionStrategy


def create_game_with_teams():
    """创建包含队伍分配的游戏状态"""
    print("=== 队伍分配和游戏初始化 ===")

    # 创建基础游戏状态
    game_state, team_side = GameMechanics.create_initial_game_state()
    print(f"我方队伍: {team_side}")
    print(f"敌方队伍: {'challenger' if team_side == 'defender' else 'defender'}")

    # 添加防御塔和水晶
    GameMechanics.add_towers_to_game_state(game_state)
    GameMechanics.add_crystals_to_game_state(game_state)

    # 使用SkillSystem创建英雄
    start_pos = GameMechanics.get_start_position(team_side)
    enemy_start_pos = GameMechanics.get_start_position(
        "challenger" if team_side == "defender" else "defender"
    )

    # 创建我方英雄
    mage = SkillSystem.create_hero("mage", "mage_001", "我方法师",
                                 Position(start_pos.x + 1, start_pos.y + 1))
    warrior = SkillSystem.create_hero("warrior", "warrior_001", "我方武士",
                                     Position(start_pos.x + 2, start_pos.y + 1))
    monkey = SkillSystem.create_hero("monkey", "monkey_001", "我方猴子",
                                    Position(start_pos.x + 1, start_pos.y + 2))

    # 创建敌方英雄
    enemy_mage = SkillSystem.create_hero("mage", "enemy_mage_001", "敌方法师",
                                       Position(enemy_start_pos.x - 1, enemy_start_pos.y - 1))
    enemy_warrior = SkillSystem.create_hero("warrior", "enemy_warrior_001", "敌方武士",
                                           Position(enemy_start_pos.x - 2, enemy_start_pos.y - 1))

    # 设置游戏状态
    game_state.roles = {"mage_001": mage, "warrior_001": warrior, "monkey_001": monkey}
    game_state.enemies = {"enemy_mage_001": enemy_mage, "enemy_warrior_001": enemy_warrior}

    # 设置团队钻石数量
    total_diamonds = sum(role.diamonds for role in game_state.roles.values())
    game_state.diamonds_num = total_diamonds

    return game_state, team_side


def demonstrate_team_mechanics():
    """演示队伍机制"""
    print("\n=== 队伍机制演示 ===")

    game_state, team_side = create_game_with_teams()

    print(f"地图大小: {game_state.map_width} x {game_state.map_height}")
    print(f"我方基地位置: {GameMechanics.get_start_position(team_side)}")
    print(f"敌方基地位置: {GameMechanics.get_start_position('challenger' if team_side == 'defender' else 'defender')}")

    print(f"\n防御塔数量: {len(game_state.towers)}")
    print(f"水晶数量: {len(game_state.crystals)}")

    # 显示分路信息
    print(f"\n分路信息:")
    for lane_name, lane_info in game_state.lane_info.items():
        print(f"  {lane_name}: 友方塔 {lane_info['friendly_towers']} 座, 敌方塔 {lane_info['enemy_towers']} 座")

    # 显示英雄信息
    print(f"\n我方英雄:")
    for role in game_state.roles.values():
        print(f"  {role.name}: 位置({role.position.x:.1f}, {role.position.y:.1f}), "
              f"钻石:{role.diamonds}, 技能冷却:{role.skill1_cooldown}/{role.skill2_cooldown}")

    print(f"\n敌方英雄:")
    for enemy in game_state.enemies.values():
        print(f"  {enemy.name}: 位置({enemy.position.x:.1f}, {enemy.position.y:.1f})")

    print(f"\n团队总钻石: {game_state.diamonds_num}")


def demonstrate_position_strategy():
    """演示位置策略"""
    print("\n=== 位置策略演示 ===")

    game_state, team_side = create_game_with_teams()
    strategy = PositionStrategy(game_state)

    print(f"我方队伍: {team_side}")

    for role in game_state.roles.values():
        print(f"\n{role.name} ({role.hero_type}) 策略位置:")

        # 获取不同策略的位置
        positions = GameMechanics.get_strategy_positions(team_side, role.hero_type)
        for strategy_name, position in positions.items():
            distance_to_base = GameMechanics.get_distance_to_base(position, team_side)
            distance_to_enemy = GameMechanics.get_distance_to_enemy_base(position, team_side)
            is_safe = GameMechanics.is_in_safe_zone(position, team_side)

            print(f"  {strategy_name}: ({position.x:.1f}, {position.y:.1f}) "
                  f"距离基地:{distance_to_base:.1f}, 距离敌方:{distance_to_enemy:.1f}, "
                  f"安全区域:{'是' if is_safe else '否'}")


def demonstrate_decision_making():
    """演示决策制定"""
    print("\n=== 决策制定演示 ===")

    game_state, team_side = create_game_with_teams()
    strategy = PositionStrategy(game_state)

    # 移动英雄到战术位置
    mage = game_state.roles["mage_001"]
    warrior = game_state.roles["warrior_001"]

    # 设置法师到分路位置
    mage.position = GameMechanics.get_lane_position(team_side, "bottom", 8.0)
    # 设置武士到前线位置
    warrior.position = GameMechanics.get_lane_position(team_side, "top", 12.0)

    # 添加一些敌方小兵
    game_state.minions = [
        {'id': 'minion1', 'type': 'melee', 'position': {'x': 15.0, 'y': 10.0},
         'health': 30.0, 'max_health': 30.0, 'team': 'enemy'},
        {'id': 'minion2', 'type': 'ranged', 'position': {'x': 18.0, 'y': 4.0},
         'health': 20.0, 'max_health': 20.0, 'team': 'enemy'}
    ]

    print(f"团队整体策略: {strategy.get_team_strategy()}")

    for role in game_state.roles.values():
        print(f"\n{role.name} 决策分析:")

        # 角色策略
        role_strategy = strategy.get_role_strategy(role)
        print(f"  推荐策略: {role_strategy}")

        # 战略位置
        strategic_pos = strategy.get_strategic_position(role, role_strategy)
        print(f"  战略位置: ({strategic_pos.x:.1f}, {strategic_pos.y:.1f})")

        # 技能使用建议
        for skill in role.skills:
            should_use = strategy.should_use_skill(role, skill)
            cooldown = role.get_skill_cooldown(skill)
            print(f"  {skill}: 使用={'是' if should_use else '否'}, 冷却={cooldown}回合")

        # 移动建议
        if role.position.distance_to(strategic_pos) > 1.0:
            print(f"  建议: 移动到战略位置")
        else:
            print(f"  建议: 保持当前位置")

        # 防御/进攻建议
        if role.health_percentage < 0.4:
            defensive_pos = strategy.get_defensive_position(role)
            print(f"  血量较低，建议防御位置: ({defensive_pos.x:.1f}, {defensive_pos.y:.1f})")
        elif strategy.get_team_strategy() == "aggressive":
            aggressive_pos = strategy.get_aggressive_position(role)
            print(f"  团队进攻，建议进攻位置: ({aggressive_pos.x:.1f}, {aggressive_pos.y:.1f})")


def demonstrate_access_patterns():
    """演示访问模式"""
    print("\n=== 访问模式演示 ===")

    game_state, team_side = create_game_with_teams()

    # 从GameState获取信息
    print("从GameState获取信息:")
    print(f"  团队方: {game_state.team_side}")
    print(f"  团队钻石总数: {game_state.diamonds_num}")
    print(f"  当前回合: {game_state.current_turn}")
    print(f"  地图宽度: {game_state.map_width}")

    # 从Role获取信息
    mage = game_state.roles["mage_001"]
    print(f"\n从Role获取信息 ({mage.name}):")
    print(f"  技能1冷却: {mage.skill1_cooldown}")
    print(f"  技能2冷却: {mage.skill2_cooldown}")
    print(f"  钻石数量: {mage.diamonds}")
    print(f"  英雄类型: {mage.hero_type}")
    print(f"  位置: ({mage.position.x}, {mage.position.y})")
    print(f"  血量: {mage.health}/{mage.max_health}")

    # 技能使用模式
    print(f"\n技能使用模式:")
    print(f"  可以使用技能1: {mage.can_use_skill(mage.skills[0])}")
    print(f"  可以使用技能2: {mage.can_use_skill(mage.skills[1])}")
    print(f"  技能1冷却时间: {mage.get_skill_cooldown(mage.skills[0])}")
    print(f"  技能2冷却时间: {mage.get_skill_cooldown(mage.skills[1])}")


def main():
    """主函数"""
    print("=== 基于队伍位置的MOBA系统演示 ===")
    print("特性：防守方/挑战方分配，位置策略，智能决策")
    print("=" * 60)

    demonstrate_team_mechanics()
    demonstrate_position_strategy()
    demonstrate_decision_making()
    demonstrate_access_patterns()

    print("\n" + "=" * 60)
    print("=== 演示完成 ===")
    print("\n系统特性:")
    print("[OK] 随机队伍分配（防守方左下角/挑战方右上角）")
    print("[OK] 基于位置的战略系统")
    print("[OK] 智能决策制定")
    print("[OK] Role类支持skill1_cooldown/skill2_cooldown属性")
    print("[OK] GameState支持team_side/diamonds_num属性")
    print("[OK] 三路地图系统（上/中/下路）")
    print("[OK] 实时策略调整")

    print("\n访问模式:")
    print("- role.skill1_cooldown: 获取技能1冷却")
    print("- role.skill2_cooldown: 获取技能2冷却")
    print("- game_state.team_side: 获取队伍方")
    print("- game_state.diamonds_num: 获取团队钻石总数")
    print("- role.can_use_skill(skill_id): 检查技能是否可用")
    print("- role.get_skill_cooldown(skill_id): 获取技能冷却时间")


if __name__ == "__main__":
    main()