from typing import Optional, Dict, List, Any
from ..core.base import Position, GameState, Role
from .base_hero import BaseHero, Buff


class Mage(BaseHero):
    """法师英雄"""

    def get_max_health(self) -> float:
        return 100.0

    def get_max_mana(self) -> float:
        return 100.0

    def get_attack_damage(self) -> float:
        return 8.0

    def get_defense(self) -> float:
        return 5.0

    def get_move_speed(self) -> float:
        return 2.0

    def get_attack_range(self) -> float:
        return 3.0

    def get_vision_range(self) -> float:
        return 4.0

    def get_skill_list(self) -> List[str]:
        return ["heal", "area_control"]

    def use_skill(self, skill_id: str, game_state: GameState, target=None, position: Position = None) -> bool:
        """使用技能"""
        if not self.can_use_skill():
            return False

        if skill_id == "heal":
            return self._use_heal(position)
        elif skill_id == "area_control":
            return self._use_area_control(game_state, position)
        else:
            return False

    def _use_heal(self, position: Position) -> bool:
        """使用技能1：指定位置回100生命值"""
        if self.get_skill_cooldown("heal") > 0:
            return False

        # 检查魔法值
        mana_cost = 30
        if self.mana < mana_cost:
            return False

        # 检查位置是否在技能范围内
        if self.position.distance_to(position) > self.attack_range:
            return False

        # 回复100生命值
        heal_amount = 100.0
        self.health = min(self.max_health, self.health + heal_amount)
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("heal", 3)

        return True

    def _use_area_control(self, game_state: GameState, center_position: Position) -> bool:
        """使用技能2：范围控制，持续两回合，在攻击范围内的所有敌方英雄和小兵无法释放技能，无法移动"""
        if self.get_skill_cooldown("area_control") > 0:
            return False

        # 检查魔法值
        mana_cost = 50
        if self.mana < mana_cost:
            return False

        # 检查目标位置是否在技能范围内
        skill_range = 5.0  # 范围控制技能范围比普通攻击范围大
        if self.position.distance_to(center_position) > skill_range:
            return False

        # 对范围内的所有敌方单位添加控制效果
        control_radius = self.attack_range
        controlled_units = []

        # 检查敌方英雄
        for enemy in game_state.enemies.values():
            if enemy.is_alive and enemy.position.distance_to(center_position) <= control_radius:
                # 如果敌人是英雄，添加控制buff
                if hasattr(enemy, 'add_buff'):
                    immobilize_buff = Buff(
                        name="area_control_immobilize",
                        duration=2,
                        effect_type="immobilize",
                        value=1.0,
                        description="范围控制：无法移动"
                    )
                    silence_buff = Buff(
                        name="area_control_silence",
                        duration=2,
                        effect_type="silence",
                        value=1.0,
                        description="范围控制：无法使用技能"
                    )
                    enemy.add_buff(immobilize_buff)
                    enemy.add_buff(silence_buff)
                    controlled_units.append(enemy.name)

        # 检查敌方小兵
        for minion in game_state.minions:
            if 'position' in minion:
                minion_pos = Position(minion['position']['x'], minion['position']['y'])
                if minion_pos.distance_to(center_position) <= control_radius:
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

        # 消耗魔法值
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("area_control", 5)

        return True

    def get_skill_description(self, skill_id: str) -> str:
        """获取技能描述"""
        if skill_id == "heal":
            return "指定位置回100生命值 (冷却: 3回合, 魔法消耗: 30)"
        elif skill_id == "area_control":
            return "范围控制，持续两回合，范围内所有敌方单位无法移动和使用技能 (冷却: 5回合, 魔法消耗: 50)"
        else:
            return "未知技能"