from typing import Optional, Dict, List, Any
from ..core.base import Position, GameState, Role
from .base_hero import BaseHero, Buff


class Warrior(BaseHero):
    """武士英雄"""

    def get_max_health(self) -> float:
        return 200.0

    def get_max_mana(self) -> float:
        return 50.0

    def get_attack_damage(self) -> float:
        return 10.0

    def get_defense(self) -> float:
        return 15.0

    def get_move_speed(self) -> float:
        return 1.5

    def get_attack_range(self) -> float:
        return 1.0

    def get_vision_range(self) -> float:
        return 4.0

    def get_skill_list(self) -> List[str]:
        return ["heavy_strike", "iron_defense"]

    def use_skill(self, skill_id: str, game_state: GameState, target=None, position: Position = None) -> bool:
        """使用技能"""
        if not self.can_use_skill():
            return False

        if skill_id == "heavy_strike":
            return self._use_heavy_strike(game_state, target)
        elif skill_id == "iron_defense":
            return self._use_iron_defense()
        else:
            return False

    def _use_heavy_strike(self, game_state: GameState, target: Role) -> bool:
        """使用技能1：攻击范围内造成50伤害"""
        if self.get_skill_cooldown("heavy_strike") > 0:
            return False

        # 检查魔法值
        mana_cost = 20
        if self.mana < mana_cost:
            return False

        # 检查目标是否在攻击范围内
        if target.position.distance_to(self.position) > self.attack_range:
            return False

        # 造成50点伤害
        damage = 50.0
        actual_damage = damage * (1 - target.defense * 0.01)
        target.health = max(0, target.health - actual_damage)

        if target.health == 0:
            target.is_alive = False

        # 消耗魔法值
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("heavy_strike", 4)

        return True

    def _use_iron_defense(self) -> bool:
        """使用技能2：减少自身70%受到的伤害，持续三回合"""
        if self.get_skill_cooldown("iron_defense") > 0:
            return False

        # 检查魔法值
        mana_cost = 30
        if self.mana < mana_cost:
            return False

        # 添加防御buff
        defense_buff = Buff(
            name="iron_defense",
            duration=3,
            effect_type="damage_reduction",
            value=0.7,  # 减少70%伤害
            description="铁壁防御：减少70%受到的伤害"
        )
        self.add_buff(defense_buff)

        # 消耗魔法值
        self.mana -= mana_cost

        # 设置冷却时间
        self.set_skill_cooldown("iron_defense", 6)

        return True

    def get_skill_description(self, skill_id: str) -> str:
        """获取技能描述"""
        if skill_id == "heavy_strike":
            return "攻击范围内造成50伤害 (冷却: 4回合, 魔法消耗: 20)"
        elif skill_id == "iron_defense":
            return "减少自身70%受到的伤害，持续三回合 (冷却: 6回合, 魔法消耗: 30)"
        else:
            return "未知技能"