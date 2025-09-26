#!/usr/bin/env python3
"""
MOBA游戏地图可视化系统

用于生成50x50地图，包含上中下三路和防御塔的可视化模拟。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random
from src.core import Position, Role, ActionType, Action

class LaneType(Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"

class Team(Enum):
    ALLY = "ally"
    ENEMY = "enemy"

@dataclass
class Tower:
    id: str
    position: Position
    health: float
    max_health: float
    team: Team
    lane: LaneType
    attack_range: float = 200
    attack_damage: float = 100

@dataclass
class MapCell:
    x: int
    y: int
    cell_type: str  # "path", "grass", "tower", "base"
    walkable: bool = True
    tower: Optional[Tower] = None

class MOBAMap:
    """MOBA游戏地图类"""

    def __init__(self, width: int = 50, height: int = 50):
        self.width = width
        self.height = height
        self.grid = np.full((height, width), "grass", dtype=object)
        self.walkable = np.ones((height, width), dtype=bool)
        self.towers: Dict[str, Tower] = {}
        self.heroes: Dict[str, Role] = {}
        self.lanes = {
            LaneType.TOP: [],
            LaneType.MIDDLE: [],
            LaneType.BOTTOM: []
        }

        self._create_map_layout()
        self._place_towers()

    def _create_map_layout(self):
        """创建地图布局，包含三路"""
        # 创建三条主要路径
        # 上路 (顶部横向)
        for y in range(8, 12):
            for x in range(self.width):
                self.grid[y, x] = "path"

        # 中路 (对角线)
        for i in range(self.width):
            y = int(self.height // 2 + (i - self.width // 2) * 0.3)
            if 0 <= y < self.height:
                self.grid[y, i] = "path"
                self.lanes[LaneType.MIDDLE].append((i, y))

        # 下路 (底部横向)
        for y in range(self.height - 12, self.height - 8):
            for x in range(self.width):
                self.grid[y, x] = "path"

        # 创建基地区域
        # 我方基地 (左侧)
        for y in range(self.height):
            for x in range(8):
                self.grid[y, x] = "base"

        # 敌方基地 (右侧)
        for y in range(self.height):
            for x in range(self.width - 8, self.width):
                self.grid[y, x] = "enemy_base"

    def _place_towers(self):
        """放置防御塔"""
        # 上路塔
        self._add_tower(Tower(
            id="top_ally_1",
            position=Position(5, 10),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.TOP
        ))

        self._add_tower(Tower(
            id="top_ally_2",
            position=Position(20, 10),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.TOP
        ))

        self._add_tower(Tower(
            id="top_enemy_1",
            position=Position(45, 10),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.TOP
        ))

        self._add_tower(Tower(
            id="top_enemy_2",
            position=Position(30, 10),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.TOP
        ))

        # 中路塔
        self._add_tower(Tower(
            id="mid_ally_1",
            position=Position(8, 25),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.MIDDLE
        ))

        self._add_tower(Tower(
            id="mid_ally_2",
            position=Position(20, 25),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.MIDDLE
        ))

        self._add_tower(Tower(
            id="mid_enemy_1",
            position=Position(42, 25),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.MIDDLE
        ))

        self._add_tower(Tower(
            id="mid_enemy_2",
            position=Position(30, 25),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.MIDDLE
        ))

        # 下路塔
        self._add_tower(Tower(
            id="bot_ally_1",
            position=Position(5, 40),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.BOTTOM
        ))

        self._add_tower(Tower(
            id="bot_ally_2",
            position=Position(20, 40),
            health=2000,
            max_health=2000,
            team=Team.ALLY,
            lane=LaneType.BOTTOM
        ))

        self._add_tower(Tower(
            id="bot_enemy_1",
            position=Position(45, 40),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.BOTTOM
        ))

        self._add_tower(Tower(
            id="bot_enemy_2",
            position=Position(30, 40),
            health=2000,
            max_health=2000,
            team=Team.ENEMY,
            lane=LaneType.BOTTOM
        ))

    def _add_tower(self, tower: Tower):
        """添加塔到地图"""
        self.towers[tower.id] = tower
        # 在地图上标记塔的位置
        x, y = int(tower.position.x), int(tower.position.y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = "tower"

    def add_hero(self, hero: Role):
        """添加英雄到地图"""
        self.heroes[hero.id] = hero

    def move_hero(self, hero_id: str, new_position: Position):
        """移动英雄"""
        if hero_id in self.heroes:
            self.heroes[hero_id].position = new_position

    def get_cell_type(self, x: int, y: int) -> str:
        """获取指定位置的格子类型"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y, x]
        return "invalid"

    def is_walkable(self, x: int, y: int) -> bool:
        """检查位置是否可行走"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.walkable[y, x]
        return False

class MapVisualizer:
    """地图可视化器"""

    def __init__(self, game_map: MOBAMap):
        self.game_map = game_map
        self.fig, self.ax = plt.subplots(figsize=(12, 10))

        # 颜色定义
        self.colors = {
            "grass": "#90EE90",      # 浅绿色
            "path": "#DEB887",       # 浅棕色
            "base": "#87CEEB",       # 浅蓝色
            "enemy_base": "#FFB6C1", # 浅粉色
            "tower": "#A0522D"       # 棕色
        }

    def render(self):
        """渲染地图"""
        self.ax.clear()

        # 绘制基础地图
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                cell_type = self.game_map.get_cell_type(x, y)
                color = self.colors.get(cell_type, "#FFFFFF")
                rect = patches.Rectangle((x, y), 1, 1,
                                       facecolor=color,
                                       edgecolor='gray',
                                       linewidth=0.1)
                self.ax.add_patch(rect)

        # 绘制防御塔
        for tower in self.game_map.towers.values():
            color = "#0066CC" if tower.team == Team.ALLY else "#CC0000"
            circle = patches.Circle((tower.position.x, tower.position.y),
                                  1.5,
                                  facecolor=color,
                                  edgecolor='black',
                                  linewidth=2)
            self.ax.add_patch(circle)

            # 绘制攻击范围
            attack_circle = patches.Circle((tower.position.x, tower.position.y),
                                         tower.attack_range / 10,  # 缩放显示
                                         facecolor='none',
                                         edgecolor=color,
                                         linewidth=1,
                                         alpha=0.3,
                                         linestyle='--')
            self.ax.add_patch(attack_circle)

            # 添加塔的标签
            self.ax.text(tower.position.x, tower.position.y - 2.5,
                        f"{tower.id}",
                        ha='center', va='center',
                        fontsize=6, fontweight='bold')

        # 绘制英雄
        for hero in self.game_map.heroes.values():
            # 简单判断队伍：根据ID包含的内容
            if "enemy" in hero.id:
                color = "#FF0000"
                marker = "^"
            else:
                color = "#0000FF"
                marker = "o"

            self.ax.plot(hero.position.x, hero.position.y,
                        marker=marker,
                        markersize=8,
                        color=color,
                        markeredgecolor='black',
                        markeredgewidth=1)

            # 添加英雄名称
            self.ax.text(hero.position.x, hero.position.y + 1.5,
                        hero.name,
                        ha='center', va='center',
                        fontsize=7,
                        bbox=dict(boxstyle="round,pad=0.1",
                                facecolor='white',
                                alpha=0.8))

            # 显示血条
            bar_width = 3
            bar_height = 0.3
            bar_x = hero.position.x - bar_width / 2
            bar_y = hero.position.y - 1.5

            # 血条背景
            bg_rect = patches.Rectangle((bar_x, bar_y), bar_width, bar_height,
                                      facecolor='red',
                                      alpha=0.7)
            self.ax.add_patch(bg_rect)

            # 当前血量
            health_width = bar_width * (hero.health / hero.max_health)
            health_rect = patches.Rectangle((bar_x, bar_y), health_width, bar_height,
                                           facecolor='green',
                                           alpha=0.9)
            self.ax.add_patch(health_rect)

        # 设置图表属性
        self.ax.set_xlim(0, self.game_map.width)
        self.ax.set_ylim(0, self.game_map.height)
        self.ax.set_aspect('equal')
        self.ax.invert_yaxis()  # 翻转Y轴，使(0,0)在左上角
        self.ax.set_title('MOBA对战地图', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('X坐标', fontsize=12)
        self.ax.set_ylabel('Y坐标', fontsize=12)

        # 添加网格
        self.ax.grid(True, alpha=0.3)

        # 添加图例
        self._add_legend()

        plt.tight_layout()

    def _add_legend(self):
        """添加图例"""
        legend_elements = [
            patches.Patch(facecolor=self.colors["grass"], label='草地'),
            patches.Patch(facecolor=self.colors["path"], label='道路'),
            patches.Patch(facecolor=self.colors["base"], label='我方基地'),
            patches.Patch(facecolor=self.colors["enemy_base"], label='敌方基地'),
            patches.Patch(facecolor=self.colors["tower"], label='防御塔'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#0000FF',
                      markersize=8, label='我方英雄'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='#FF0000',
                      markersize=8, label='敌方英雄')
        ]

        self.ax.legend(handles=legend_elements, loc='upper left',
                      bbox_to_anchor=(1, 1), fontsize=10)

    def save_image(self, filename: str = "moba_map.png"):
        """保存图片"""
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"地图已保存为: {filename}")

    def show(self):
        """显示地图"""
        plt.show()

class BattleSimulator:
    """对战模拟器"""

    def __init__(self, game_map: MOBAMap):
        self.game_map = game_map
        self.turn_count = 0

    def create_sample_heroes(self):
        """创建示例英雄"""
        # 我方英雄
        ally_heroes = [
            Role(
                id="warrior_1",
                name="战士",
                position=Position(10, 10),
                health=1000,
                max_health=1000,
                mana=300,
                max_mana=300,
                attack_damage=80,
                defense=60,
                move_speed=3,
                attack_range=1,
                skills=["slash", "charge"],
                is_alive=True
            ),
            Role(
                id="mage_1",
                name="法师",
                position=Position(8, 25),
                health=600,
                max_health=600,
                mana=500,
                max_mana=500,
                attack_damage=120,
                defense=30,
                move_speed=2,
                attack_range=4,
                skills=["fireball", "freeze"],
                is_alive=True
            ),
            Role(
                id="support_1",
                name="辅助",
                position=Position(5, 40),
                health=700,
                max_health=700,
                mana=450,
                max_mana=450,
                attack_damage=50,
                defense=40,
                move_speed=2.5,
                attack_range=3,
                skills=["heal", "shield"],
                is_alive=True
            )
        ]

        # 敌方英雄
        enemy_heroes = [
            Role(
                id="enemy_warrior",
                name="敌战",
                position=Position(40, 10),
                health=1000,
                max_health=1000,
                mana=300,
                max_mana=300,
                attack_damage=85,
                defense=65,
                move_speed=3,
                attack_range=1,
                skills=["heavy_slash"],
                is_alive=True
            ),
            Role(
                id="enemy_mage",
                name="敌法",
                position=Position(42, 25),
                health=600,
                max_health=600,
                mana=500,
                max_mana=500,
                attack_damage=125,
                defense=28,
                move_speed=2,
                attack_range=4,
                skills=["lightning"],
                is_alive=True
            ),
            Role(
                id="enemy_support",
                name="敌辅",
                position=Position(45, 40),
                health=700,
                max_health=700,
                mana=450,
                max_mana=450,
                attack_damage=55,
                defense=42,
                move_speed=2.5,
                attack_range=3,
                skills=["dark_heal"],
                is_alive=True
            )
        ]

        # 添加英雄到地图
        for hero in ally_heroes + enemy_heroes:
            self.game_map.add_hero(hero)

    def simulate_movement(self):
        """模拟英雄移动"""
        self.turn_count += 1

        for hero_id, hero in self.game_map.heroes.items():
            if not hero.is_alive:
                continue

            # 简单AI：向敌方基地移动
            if "enemy" in hero_id:
                # 敌方向我方基地移动
                target_x, target_y = 5, 25
            else:
                # 我方向敌方基地移动
                target_x, target_y = 45, 25

            # 计算移动方向
            dx = target_x - hero.position.x
            dy = target_y - hero.position.y
            distance = (dx**2 + dy**2)**0.5

            if distance > 1:
                # 标准化方向向量并应用移动速度
                move_x = (dx / distance) * hero.move_speed
                move_y = (dy / distance) * hero.move_speed

                new_x = hero.position.x + move_x
                new_y = hero.position.y + move_y

                # 确保不超出边界
                new_x = max(0, min(self.game_map.width - 1, new_x))
                new_y = max(0, min(self.game_map.height - 1, new_y))

                self.game_map.move_hero(hero_id, Position(new_x, new_y))

    def simulate_battle(self):
        """模拟战斗"""
        # 简单的战斗模拟
        ally_towers = [t for t in self.game_map.towers.values() if t.team == Team.ALLY]
        enemy_towers = [t for t in self.game_map.towers.values() if t.team == Team.ENEMY]
        ally_heroes = [h for h in self.game_map.heroes.values() if "enemy" not in h.id and h.is_alive]
        enemy_heroes = [h for h in self.game_map.heroes.values() if "enemy" in h.id and h.is_alive]

        # 随机减少一些血量来模拟战斗
        for tower in ally_towers + enemy_towers:
            if random.random() < 0.1:  # 10%概率受到攻击
                damage = random.randint(50, 150)
                tower.health = max(0, tower.health - damage)

        for hero in ally_heroes + enemy_heroes:
            if random.random() < 0.2:  # 20%概率受到攻击
                damage = random.randint(20, 100)
                hero.health = max(0, hero.health - damage)
                if hero.health == 0:
                    hero.is_alive = False

    def run_simulation_turn(self):
        """运行一回合模拟"""
        print(f"===== 第 {self.turn_count + 1} 回合 =====")
        self.simulate_movement()
        self.simulate_battle()
        self.turn_count += 1

        # 显示当前状态
        self.print_battle_status()

    def print_battle_status(self):
        """打印战斗状态"""
        print(f"回合 {self.turn_count} 状态:")

        # 塔的状态
        ally_towers_health = sum(t.health for t in self.game_map.towers.values() if t.team == Team.ALLY)
        enemy_towers_health = sum(t.health for t in self.game_map.towers.values() if t.team == Team.ENEMY)
        print(f"  我方塔总血量: {ally_towers_health}")
        print(f"  敌方塔总血量: {enemy_towers_health}")

        # 英雄状态
        alive_allies = sum(1 for h in self.game_map.heroes.values() if "enemy" not in h.id and h.is_alive)
        alive_enemies = sum(1 for h in self.game_map.heroes.values() if "enemy" in h.id and h.is_alive)
        print(f"  我方存活英雄: {alive_allies}/3")
        print(f"  敌方存活英雄: {alive_enemies}/3")

def main():
    """主函数"""
    print("MOBA对战模拟器")
    print("=" * 40)

    # 创建地图
    game_map = MOBAMap(50, 50)
    print(f"创建 {game_map.width}x{game_map.height} 地图")

    # 创建模拟器
    simulator = BattleSimulator(game_map)

    # 添加英雄
    simulator.create_sample_heroes()
    print("添加示例英雄完成")

    # 创建可视化器
    visualizer = MapVisualizer(game_map)

    # 显示初始状态
    print("\n初始地图状态:")
    visualizer.render()
    visualizer.save_image("moba_battle_initial.png")

    # 运行几回合模拟
    print("\n开始对战模拟...")
    for i in range(5):
        simulator.run_simulation_turn()

        # 每2回合保存一次图片
        if (i + 1) % 2 == 0:
            visualizer.render()
            visualizer.save_image(f"moba_battle_turn_{i+1}.png")

    # 显示最终状态
    print("\n最终地图状态:")
    visualizer.render()
    visualizer.save_image("moba_battle_final.png")

    print(f"\n模拟完成！共进行了 {simulator.turn_count} 回合")
    print("地图图片已保存")

    # 显示最终地图
    visualizer.show()

if __name__ == "__main__":
    main()