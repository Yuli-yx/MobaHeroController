from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from ..core.base import Role, Position, GameState


@dataclass
class Buff:
    """增益/减益效果"""
    name: str
    duration: int  # 持续回合数
    effect_type: str  # 效果类型
    value: float  # 效果值
    description: str = ""


class BaseHero(Role, ABC):
    """英雄基类"""

    def __init__(self, id: str, name: str, position: Position):
        # 调用父类构造函数，技能列表在子类中定义
        super().__init__(
            id=id,
            name=name,
            position=position,
            health=self.get_max_health(),
            max_health=self.get_max_health(),
            mana=self.get_max_mana(),
            max_mana=self.get_max_mana(),
            attack_damage=self.get_attack_damage(),
            defense=self.get_defense(),
            move_speed=self.get_move_speed(),
            attack_range=self.get_attack_range(),
            skills=self.get_skill_list(),
            is_alive=True
        )

        # 英雄特有属性
        self.vision_range = self.get_vision_range()
        self.buffs: List[Buff] = []
        self.skill_cooldowns: Dict[str, int] = {}
        self.minion_kills = 0

    @abstractmethod
    def get_max_health(self) -> float:
        """获取最大生命值"""
        pass

    @abstractmethod
    def get_max_mana(self) -> float:
        """获取最大魔法值"""
        pass

    @abstractmethod
    def get_attack_damage(self) -> float:
        """获取攻击伤害"""
        pass

    @abstractmethod
    def get_defense(self) -> float:
        """获取防御力"""
        pass

    @abstractmethod
    def get_move_speed(self) -> float:
        """获取移动速度"""
        pass

    @abstractmethod
    def get_attack_range(self) -> float:
        """获取攻击范围"""
        pass

    @abstractmethod
    def get_vision_range(self) -> float:
        """获取视野范围"""
        pass

    @abstractmethod
    def get_skill_list(self) -> List[str]:
        """获取技能列表"""
        pass

    @abstractmethod
    def use_skill(self, skill_id: str, game_state: GameState, target=None, position: Position = None) -> bool:
        """使用技能"""
        pass

    def update_buffs(self) -> None:
        """更新增益/减益效果"""
        # 减少所有buff的持续时间
        for buff in self.buffs[:]:
            buff.duration -= 1
            if buff.duration <= 0:
                self.buffs.remove(buff)

    def get_damage_multiplier(self) -> float:
        """获取伤害倍率（考虑buff影响）"""
        multiplier = 1.0
        for buff in self.buffs:
            if buff.effect_type == "damage_reduction":
                multiplier *= (1 - buff.value)
        return multiplier

    def get_defense_multiplier(self) -> float:
        """获取防御倍率（考虑buff影响）"""
        multiplier = 1.0
        for buff in self.buffs:
            if buff.effect_type == "defense_boost":
                multiplier *= (1 + buff.value)
        return multiplier

    def can_move(self) -> bool:
        """检查是否可以移动"""
        for buff in self.buffs:
            if buff.effect_type == "immobilize":
                return False
        return True

    def can_use_skill(self) -> bool:
        """检查是否可以使用技能"""
        for buff in self.buffs:
            if buff.effect_type == "silence":
                return False
        return True

    def add_buff(self, buff: Buff) -> None:
        """添加增益/减益效果"""
        self.buffs.append(buff)

    def remove_buff(self, buff_name: str) -> None:
        """移除指定名称的增益/减益效果"""
        self.buffs = [buff for buff in self.buffs if buff.name != buff_name]

    def has_buff(self, buff_name: str) -> bool:
        """检查是否拥有指定增益/减益效果"""
        return any(buff.name == buff_name for buff in self.buffs)

    def get_skill_cooldown(self, skill_id: str) -> int:
        """获取技能冷却时间"""
        return self.skill_cooldowns.get(skill_id, 0)

    def set_skill_cooldown(self, skill_id: str, cooldown: int) -> None:
        """设置技能冷却时间"""
        self.skill_cooldowns[skill_id] = cooldown

    def update_cooldowns(self) -> None:
        """更新技能冷却时间"""
        for skill_id in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[skill_id] > 0:
                self.skill_cooldowns[skill_id] -= 1

    def heal_minion_kill(self) -> None:
        """击杀小兵后回血"""
        heal_amount = self.max_health * 0.1  # 回复10%血量
        self.health = min(self.max_health, self.health + heal_amount)
        self.minion_kills += 1

    def is_in_vision_range(self, target_position: Position) -> bool:
        """检查目标位置是否在视野范围内"""
        return self.position.distance_to(target_position) <= self.vision_range