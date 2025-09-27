from typing import Optional, Dict, List, Any
from ..core.base import Position, GameState, Role
from .base_hero import BaseHero, Buff


class Monkey(BaseHero):
    """猴子英雄"""

    def get_max_health(self) -> float:
        return 150.0

    def get_max_mana(self) -> float:
        return 80.0

    def get_attack_damage(self) -> float:
        return 15.0

    def get_defense(self) -> float:
        return 8.0

    def get_move_speed(self) -> float:
        return 3.0

    def get_attack_range(self) -> float:
        return 2.0

    def get_vision_range(self) -> float:
        return 4.0

    def get_skill_list(self) -> List[str]:
        return ["corrosive_strike", "leap"]

    def use_skill(self, skill_id: str, game_state: GameState, target=None, position: Position = None) -> bool:
        """使用技能"""
        if not self.can_use_skill():
            return False

        if skill_id == "corrosive_strike":
            return self._use_corrosive_strike(game_state, target)
        elif skill_id == "leap":
            return self._use_leap(position)
        else:
            return False

    def _use_corrosive_strike(self, game_state: GameState, target: Role) -> bool:
        """使用技能1：攻击范围内造成侵蚀伤害"""
        if self.get_skill_cooldown("corrosive_strike") > 0:
            return False

        # 检查魔法值
        mana_cost = 25
        if self.mana < mana_cost:
            return False

        # 检查目标是否在攻击范围内
        if target.position.distance_to(self.position) > self.attack_range:
            return False

        # 造成侵蚀伤害（无视部分防御）
        base_damage = 20.0  # 侵蚀伤害基础值
        # 侵蚀伤害无视50%防御
        defense_ignore = 0.5
        effective_defense = target.defense * defense_ignore
        actual_damage = base_damage * (1 - effective_defense * 0.01)

        # 添加腐蚀效果（持续伤害）
        corrosion_buff = Buff(
            name="corrosion",
            duration=3,
            effect_type="dot",
            value=5.0,  # 每回合5点伤害
            description="腐蚀：每回合受到5点持续伤害"
        )
        target.add_buff(corrosion_buff)

        target.health = max(0, target.health - actual_damage)
        if target.health == 0:
            target.is_alive = False

        # 消耗魔法值
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("corrosive_strike", 3)

        return True

    def _use_leap(self, target_position: Position) -> bool:
        """使用技能2：向指定位置移动，移动范围是2"""
        if self.get_skill_cooldown("leap") > 0:
            return False

        # 检查魔法值
        mana_cost = 35
        if self.mana < mana_cost:
            return False

        # 检查目标位置是否在跳跃范围内
        leap_range = 4.0  # 跳跃范围应该更大一些
        if self.position.distance_to(target_position) > leap_range:
            return False

        # 执行跳跃移动
        self.position = target_position

        # 消耗魔法值
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("leap", 2)

        return True

    def get_skill_description(self, skill_id: str) -> str:
        """获取技能描述"""
        if skill_id == "corrosive_strike":
            return "攻击范围内造成侵蚀伤害，无视50%防御并添加持续伤害效果 (冷却: 3回合, 魔法消耗: 25)"
        elif skill_id == "leap":
            return "向指定位置移动，移动范围是2 (冷却: 2回合, 魔法消耗: 35)"
        else:
            return "未知技能"