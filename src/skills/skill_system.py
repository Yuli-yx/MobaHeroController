from typing import Dict, List, Any, Optional, Tuple
from ..core.base import GameState, Role, Position


class SkillSystem:
    """技能系统，处理所有英雄类型的技能"""

    @staticmethod
    def create_hero(hero_type: str, hero_id: str, name: str, position: Position) -> Role:
        """创建英雄"""
        if hero_type == "mage":
            return SkillSystem._create_mage(hero_id, name, position)
        elif hero_type == "warrior":
            return SkillSystem._create_warrior(hero_id, name, position)
        elif hero_type == "monkey":
            return SkillSystem._create_monkey(hero_id, name, position)
        else:
            raise ValueError(f"未知的英雄类型: {hero_type}")

    @staticmethod
    def _create_mage(hero_id: str, name: str, position: Position) -> Role:
        """创建法师英雄"""
        return Role(
            id=hero_id,
            name=name,
            position=position,
            health=100.0,
            max_health=100.0,
            mana=100.0,
            max_mana=100.0,
            attack_damage=8.0,
            defense=5.0,
            move_speed=2.0,
            attack_range=3.0,
            skills=["heal", "area_control"],
            hero_type="mage",
            vision_range=4.0,
            diamonds=100
        )

    @staticmethod
    def _create_warrior(hero_id: str, name: str, position: Position) -> Role:
        """创建武士英雄"""
        return Role(
            id=hero_id,
            name=name,
            position=position,
            health=200.0,
            max_health=200.0,
            mana=50.0,
            max_mana=50.0,
            attack_damage=10.0,
            defense=15.0,
            move_speed=1.5,
            attack_range=1.0,
            skills=["heavy_strike", "iron_defense"],
            hero_type="warrior",
            vision_range=4.0,
            diamonds=100
        )

    @staticmethod
    def _create_monkey(hero_id: str, name: str, position: Position) -> Role:
        """创建猴子英雄"""
        return Role(
            id=hero_id,
            name=name,
            position=position,
            health=150.0,
            max_health=150.0,
            mana=80.0,
            max_mana=80.0,
            attack_damage=15.0,
            defense=8.0,
            move_speed=3.0,
            attack_range=2.0,
            skills=["corrosive_strike", "leap"],
            hero_type="monkey",
            vision_range=4.0,
            diamonds=100
        )

    @staticmethod
    def use_skill(role: Role, skill_id: str, game_state: GameState,
                  target=None, position: Position = None) -> Tuple[bool, str]:
        """使用技能"""
        if not role.can_use_skill(skill_id):
            return False, "技能无法使用"

        # 消耗钻石（所有技能消耗5钻石）
        if not role.use_diamonds(5):
            return False, "钻石不足"

        # 设置冷却时间（所有英雄CD都是10）
        role.set_skill_cooldown(skill_id, 10)

        # 根据英雄类型和技能ID执行相应技能
        if role.hero_type == "mage":
            return SkillSystem._use_mage_skill(role, skill_id, game_state, target, position)
        elif role.hero_type == "warrior":
            return SkillSystem._use_warrior_skill(role, skill_id, game_state, target, position)
        elif role.hero_type == "monkey":
            return SkillSystem._use_monkey_skill(role, skill_id, game_state, target, position)
        else:
            return False, "未知英雄类型"

    @staticmethod
    def _use_mage_skill(role: Role, skill_id: str, game_state: GameState,
                        target=None, position: Position = None) -> Tuple[bool, str]:
        """使用法师技能"""
        if skill_id == "heal":
            return SkillSystem._mage_heal(role, position)
        elif skill_id == "area_control":
            return SkillSystem._mage_area_control(role, game_state, position)
        else:
            return False, "未知技能"

    @staticmethod
    def _use_warrior_skill(role: Role, skill_id: str, game_state: GameState,
                          target=None, position: Position = None) -> Tuple[bool, str]:
        """使用武士技能"""
        if skill_id == "heavy_strike":
            return SkillSystem._warrior_heavy_strike(role, target)
        elif skill_id == "iron_defense":
            return SkillSystem._warrior_iron_defense(role)
        else:
            return False, "未知技能"

    @staticmethod
    def _use_monkey_skill(role: Role, skill_id: str, game_state: GameState,
                         target=None, position: Position = None) -> Tuple[bool, str]:
        """使用猴子技能"""
        if skill_id == "corrosive_strike":
            return SkillSystem._monkey_corrosive_strike(role, target)
        elif skill_id == "leap":
            return SkillSystem._monkey_leap(role, position)
        else:
            return False, "未知技能"

    @staticmethod
    def _mage_heal(role: Role, position: Position) -> Tuple[bool, str]:
        """法师治疗技能：指定位置回100生命值"""
        if position is None:
            return False, "治疗技能需要目标位置"

        # 检查位置是否在技能范围内
        if role.position.distance_to(position) > role.attack_range:
            return False, "目标位置超出技能范围"

        # 回复100生命值
        heal_amount = 100.0
        role.health = min(role.max_health, role.health + heal_amount)

        return True, f"{role.name} 使用治疗技能，恢复 {heal_amount} 点生命值"

    @staticmethod
    def _mage_area_control(role: Role, game_state: GameState, position: Position) -> Tuple[bool, str]:
        """法师范围控制技能：持续两回合，范围内的所有敌方单位无法移动和使用技能"""
        if position is None:
            return False, "范围控制需要目标位置"

        # 检查目标位置是否在技能范围内
        skill_range = 5.0
        if role.position.distance_to(position) > skill_range:
            return False, "目标位置超出技能范围"

        # 对范围内的所有敌方单位添加控制效果
        control_radius = role.attack_range
        controlled_units = []

        # 检查敌方英雄
        for enemy in game_state.enemies.values():
            if enemy.is_alive and enemy.position.distance_to(position) <= control_radius:
                # 添加控制buff
                immobilize_buff = {
                    'name': 'area_control_immobilize',
                    'duration': 2,
                    'effect_type': 'immobilize',
                    'value': 1.0,
                    'description': '范围控制：无法移动'
                }
                silence_buff = {
                    'name': 'area_control_silence',
                    'duration': 2,
                    'effect_type': 'silence',
                    'value': 1.0,
                    'description': '范围控制：无法使用技能'
                }
                enemy.add_buff(immobilize_buff)
                enemy.add_buff(silence_buff)
                controlled_units.append(enemy.name)

        # 检查敌方小兵
        for minion in game_state.minions:
            if 'position' in minion:
                minion_pos = Position(minion['position']['x'], minion['position']['y'])
                if minion_pos.distance_to(position) <= control_radius:
                    # 标记小兵被控制
                    if 'controlled' not in minion:
                        minion['controlled'] = []
                    minion['controlled'].append({
                        'type': 'immobilize',
                        'duration': 2,
                        'source': 'area_control'
                    })
                    minion['controlled'].append({
                        'type': 'silence',
                        'duration': 2,
                        'source': 'area_control'
                    })
                    controlled_units.append(f"小兵@({minion['position']['x']},{minion['position']['y']})")

        return True, f"{role.name} 使用范围控制技能，影响 {len(controlled_units)} 个单位"

    @staticmethod
    def _warrior_heavy_strike(role: Role, target: Role) -> Tuple[bool, str]:
        """武士重击技能：攻击范围内造成50伤害"""
        if target is None:
            return False, "重击技能需要目标"

        # 检查目标是否在攻击范围内
        if target.position.distance_to(role.position) > role.attack_range:
            return False, "目标超出攻击范围"

        # 造成50点伤害
        damage = 50.0
        actual_damage = damage * (1 - target.defense * 0.01)
        target.health = max(0, target.health - actual_damage)

        if target.health == 0:
            target.is_alive = False

        return True, f"{role.name} 使用重击技能，对 {target.name} 造成 {actual_damage:.1f} 点伤害"

    @staticmethod
    def _warrior_iron_defense(role: Role) -> Tuple[bool, str]:
        """武士铁壁防御技能：减少自身70%受到的伤害，持续三回合"""
        # 添加防御buff
        defense_buff = {
            'name': 'iron_defense',
            'duration': 3,
            'effect_type': 'damage_reduction',
            'value': 0.7,
            'description': '铁壁防御：减少70%受到的伤害'
        }
        role.add_buff(defense_buff)

        return True, f"{role.name} 使用铁壁防御技能，减少70%受到的伤害"

    @staticmethod
    def _monkey_corrosive_strike(role: Role, target: Role) -> Tuple[bool, str]:
        """猴子腐蚀打击技能：攻击范围内造成侵蚀伤害，无视50%防御并添加持续伤害"""
        if target is None:
            return False, "腐蚀打击需要目标"

        # 检查目标是否在攻击范围内
        if target.position.distance_to(role.position) > role.attack_range:
            return False, "目标超出攻击范围"

        # 造成侵蚀伤害（无视部分防御）
        base_damage = 20.0
        defense_ignore = 0.5
        effective_defense = target.defense * defense_ignore
        actual_damage = base_damage * (1 - effective_defense * 0.01)

        # 添加腐蚀效果（持续伤害）
        corrosion_buff = {
            'name': 'corrosion',
            'duration': 3,
            'effect_type': 'dot',
            'value': 5.0,
            'description': '腐蚀：每回合受到5点持续伤害'
        }
        target.add_buff(corrosion_buff)

        target.health = max(0, target.health - actual_damage)
        if target.health == 0:
            target.is_alive = False

        return True, f"{role.name} 使用腐蚀打击，对 {target.name} 造成 {actual_damage:.1f} 点伤害并添加腐蚀效果"

    @staticmethod
    def _monkey_leap(role: Role, position: Position) -> Tuple[bool, str]:
        """猴子跳跃技能：向指定位置移动，移动范围是4"""
        if position is None:
            return False, "跳跃技能需要目标位置"

        # 检查目标位置是否在跳跃范围内
        leap_range = 4.0
        if role.position.distance_to(position) > leap_range:
            return False, "目标位置超出跳跃范围"

        # 执行跳跃移动
        old_position = Position(role.position.x, role.position.y)
        role.position = position

        return True, f"{role.name} 使用跳跃技能，从 ({old_position.x:.1f}, {old_position.y:.1f}) 移动到 ({position.x:.1f}, {position.y:.1f})"

    @staticmethod
    def get_skill_description(hero_type: str, skill_id: str) -> str:
        """获取技能描述"""
        descriptions = {
            "mage": {
                "heal": "指定位置回100生命值 (消耗: 5钻石, CD: 10回合)",
                "area_control": "范围控制，持续两回合，范围内所有敌方单位无法移动和使用技能 (消耗: 5钻石, CD: 10回合)"
            },
            "warrior": {
                "heavy_strike": "攻击范围内造成50伤害 (消耗: 5钻石, CD: 10回合)",
                "iron_defense": "减少自身70%受到的伤害，持续三回合 (消耗: 5钻石, CD: 10回合)"
            },
            "monkey": {
                "corrosive_strike": "攻击范围内造成侵蚀伤害，无视50%防御并添加持续伤害 (消耗: 5钻石, CD: 10回合)",
                "leap": "向指定位置移动，移动范围是4 (消耗: 5钻石, CD: 10回合)"
            }
        }

        return descriptions.get(hero_type, {}).get(skill_id, "未知技能")

    @staticmethod
    def update_all_skills(game_state: GameState) -> None:
        """更新所有英雄的技能状态"""
        all_roles = list(game_state.roles.values()) + list(game_state.enemies.values())

        for role in all_roles:
            role.update_cooldowns()
            role.update_buffs()

    @staticmethod
    def process_dot_effects(game_state: GameState) -> None:
        """处理持续伤害效果"""
        all_roles = list(game_state.roles.values()) + list(game_state.enemies.values())

        for role in all_roles:
            damage_to_apply = 0
            buffs_to_remove = []

            for buff in role.buffs:
                if buff.get('effect_type') == 'dot':
                    damage_to_apply += buff.get('value', 0)

            # 应用伤害
            if damage_to_apply > 0:
                role.health = max(0, role.health - damage_to_apply)
                if role.health == 0:
                    role.is_alive = False