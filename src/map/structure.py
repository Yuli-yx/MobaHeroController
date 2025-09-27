from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..core.base import Position


class StructureType(Enum):
    """建筑类型"""
    TOWER = "tower"         # 防御塔
    CRYSTAL = "crystal"     # 水晶
    NEXUS = "nexus"         # 主基地


@dataclass
class Structure:
    """游戏中的建筑结构"""
    id: str
    structure_type: StructureType
    position: Position
    health: float
    max_health: float
    attack_damage: float = 0.0
    attack_range: float = 0.0
    team: str = "neutral"   # "ally", "enemy", "neutral"
    is_alive: bool = True
    attack_cooldown: int = 0
    vision_range: float = 6.0

    def take_damage(self, damage: float) -> float:
        """受到伤害，返回实际伤害值"""
        if not self.is_alive:
            return 0.0

        actual_damage = min(damage, self.health)
        self.health -= actual_damage

        if self.health <= 0:
            self.health = 0
            self.is_alive = False

        return actual_damage

    def can_attack(self) -> bool:
        """检查是否可以攻击"""
        return self.is_alive and self.attack_cooldown <= 0 and self.attack_damage > 0

    def attack(self, target) -> bool:
        """攻击目标"""
        if not self.can_attack():
            return False

        # 计算伤害
        damage = self.attack_damage
        if hasattr(target, 'take_damage'):
            actual_damage = target.take_damage(damage)
        elif hasattr(target, 'health'):
            # 对于简单的目标对象
            actual_damage = min(damage, target.health)
            target.health -= actual_damage
            if target.health <= 0:
                target.health = 0
                if hasattr(target, 'is_alive'):
                    target.is_alive = False
        else:
            return False

        # 设置攻击冷却
        self.attack_cooldown = 2  # 假设建筑每2回合攻击一次

        return True

    def update_cooldown(self) -> None:
        """更新冷却时间"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def get_health_percentage(self) -> float:
        """获取生命值百分比"""
        return self.health / self.max_health if self.max_health > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'type': self.structure_type.value,
            'position': {'x': self.position.x, 'y': self.position.y},
            'health': self.health,
            'max_health': self.max_health,
            'attack_damage': self.attack_damage,
            'attack_range': self.attack_range,
            'team': self.team,
            'is_alive': self.is_alive,
            'vision_range': self.vision_range
        }