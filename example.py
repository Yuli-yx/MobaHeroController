#!/usr/bin/env python3
"""
Honor For Legends - 分层状态机架构示例

这个示例展示了如何使用分层状态机架构来控制MOBA游戏中的角色。
"""

import logging
from typing import Dict, List
from src.core import GameState, Role, Position, Action, ActionType
from src.sensors import SituationAwareness
from src.strategies import StrategyManager, StrategySelector, OffensiveStrategy, DefensiveStrategy, SupportStrategy, TeamFightStrategy
from src.actions import ActionExecutor, ActionOptimizer
from src.coordinators import TeamCoordinator, RoleCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameSimulation:
    """游戏模拟器"""

    def __init__(self):
        self.game_state = None
        self.team_coordinator = TeamCoordinator()
        self.role_coordinators: Dict[str, RoleCoordinator] = {}
        self.strategy_manager = StrategyManager()
        self.action_executor = ActionExecutor()
        self.action_optimizer = ActionOptimizer()
        self.current_turn = 0

    def create_sample_game_state(self) -> GameState:
        """创建示例游戏状态"""
        # 创建我方角色
        roles = {
            "warrior_1": Role(
                id="warrior_1",
                name="战士1",
                position=Position(100, 300),
                health=800,
                max_health=1000,
                mana=200,
                max_mana=300,
                attack_damage=80,
                defense=60,
                move_speed=100,
                attack_range=100,
                skills=["slash", "whirlwind"],
                is_alive=True
            ),
            "mage_1": Role(
                id="mage_1",
                name="法师1",
                position=Position(150, 350),
                health=500,
                max_health=600,
                mana=400,
                max_mana=500,
                attack_damage=120,
                defense=30,
                move_speed=80,
                attack_range=400,
                skills=["fireball", "freeze", "teleport"],
                is_alive=True
            ),
            "support_1": Role(
                id="support_1",
                name="辅助1",
                position=Position(200, 250),
                health=550,
                max_health=700,
                mana=350,
                max_mana=450,
                attack_damage=50,
                defense=40,
                move_speed=90,
                attack_range=350,
                skills=["heal", "shield", "speed_boost"],
                is_alive=True
            )
        }

        # 创建敌方角色
        enemies = {
            "enemy_warrior": Role(
                id="enemy_warrior",
                name="敌方战士",
                position=Position(800, 400),
                health=900,
                max_health=1000,
                mana=150,
                max_mana=300,
                attack_damage=90,
                defense=70,
                move_speed=95,
                attack_range=110,
                skills=["heavy_slash", "charge"],
                is_alive=True
            ),
            "enemy_mage": Role(
                id="enemy_mage",
                name="敌方法师",
                position=Position(750, 350),
                health=450,
                max_health=600,
                mana=380,
                max_mana=500,
                attack_damage=130,
                defense=25,
                move_speed=85,
                attack_range=420,
                skills=["lightning", "ice_storm"],
                is_alive=True
            )
        }

        # 创建游戏状态
        game_state = GameState(
            roles=roles,
            enemies=enemies,
            towers=[
                {"id": "tower_1", "position": Position(50, 300), "health": 2000, "max_health": 2000, "team": "ally"},
                {"id": "tower_2", "position": Position(850, 400), "health": 1800, "max_health": 2000, "team": "enemy"}
            ],
            crystals=[
                {"id": "crystal_1", "position": Position(20, 300), "health": 3000, "max_health": 3000, "team": "ally"},
                {"id": "crystal_2", "position": Position(980, 400), "health": 2800, "max_health": 3000, "team": "enemy"}
            ],
            minions=[],  # 简化处理，不包含小兵
            current_turn=0,
            map_width=1000,
            map_height=800
        )

        return game_state

    def initialize_strategies(self) -> None:
        """初始化策略管理器"""
        # 为每个角色创建策略选择器
        for role_id in self.game_state.roles.keys():
            selector = StrategySelector()

            # 注册各种策略
            selector.register_strategy(OffensiveStrategy())
            selector.register_strategy(DefensiveStrategy())
            selector.register_strategy(SupportStrategy())
            selector.register_strategy(TeamFightStrategy())

            self.strategy_manager.register_role_strategy(role_id, selector)

    def initialize_coordinators(self) -> None:
        """初始化协调器"""
        # 创建角色协调器
        for role_id in self.game_state.roles.keys():
            self.role_coordinators[role_id] = RoleCoordinator(role_id)

    def simulate_turn(self) -> None:
        """模拟一个回合"""
        self.current_turn += 1
        logger.info(f"===== 第 {self.current_turn} 回合 =====")

        # 更新团队策略
        self.team_coordinator.update_team_strategy(self.game_state, self.current_turn)

        # 更新动作执行器的冷却时间
        self.action_executor.update_cooldowns()

        # 为每个角色决策和执行动作
        for role_id, role in self.game_state.roles.items():
            if not role.is_alive:
                continue

            logger.info(f"--- {role.name} 的回合 ---")

            # 1. 获取策略建议
            strategy_result = self.strategy_manager.get_action_for_role(
                self.game_state, role, self.current_turn
            )

            if strategy_result:
                # 创建一个模拟的StrategyResult
                from src.strategies.base_strategy import StrategyResult
                mock_result = StrategyResult(
                    action=strategy_result,
                    confidence=0.8,
                    reasoning="基于当前策略的建议",
                    priority=2
                )

                logger.info(f"策略建议: {mock_result.reasoning}")

                # 2. 优化动作
                optimized_action = self.action_optimizer.optimize_action(
                    self.game_state, role, mock_result
                )

                # 3. 获取角色协调后的动作
                role_coordinator = self.role_coordinators[role_id]
                coordinated_action = role_coordinator.get_coordinated_action(
                    self.game_state, role, mock_result, self.current_turn
                )

                # 4. 获取团队协同建议的动作
                team_action = self.team_coordinator.get_role_action(
                    self.game_state, role, self.current_turn
                )

                # 选择最终动作（优先级：团队协调 > 角色协调 > 优化动作）
                final_action = team_action or coordinated_action or optimized_action

                if final_action:
                    # 5. 执行动作
                    result = self.action_executor.execute_action(
                        self.game_state, role, final_action, self.current_turn
                    )

                    logger.info(f"执行动作: {final_action.action_type.value}")
                    logger.info(f"执行结果: {result.message}")

                    # 6. 检查是否需要支援
                    if role_coordinator.should_request_support(self.game_state, role):
                        support_info = role_coordinator.get_support_request_info(
                            self.game_state, role
                        )
                        logger.info(f"请求支援: {support_info['reason']}")
                else:
                    logger.info("没有可执行的动作")

            # 显示角色状态
            logger.info(f"当前状态 - 生命: {role.health:.0f}/{role.max_health}, "
                       f"魔法: {role.mana:.0f}/{role.max_mana}, "
                       f"位置: ({role.position.x:.0f}, {role.position.y:.0f})")

        # 显示游戏状态概览
        self.log_game_status()

    def log_game_status(self) -> None:
        """记录游戏状态"""
        alive_allies = sum(1 for role in self.game_state.roles.values() if role.is_alive)
        alive_enemies = sum(1 for role in self.game_state.enemies.values() if role.is_alive)

        team_health = sum(role.health_percentage for role in self.game_state.roles.values() if role.is_alive)
        enemy_health = sum(enemy.health_percentage for enemy in self.game_state.enemies.values() if enemy.is_alive)

        logger.info(f"游戏状态 - 我方存活: {alive_allies}, 敌方存活: {alive_enemies}")
        ally_health_avg = team_health / alive_allies if alive_allies > 0 else 0
        enemy_health_avg = enemy_health / alive_enemies if alive_enemies > 0 else 0
        logger.info(f"平均血量 - 我方: {ally_health_avg:.1%}, 敌方: {enemy_health_avg:.1%}")

        # 显示团队状态
        team_status = self.team_coordinator.get_team_status(self.game_state)
        logger.info(f"团队目标: {team_status['current_objective']}, "
                   f"协同程度: {team_status['coordination_level']:.1%}")

    def run_simulation(self, turns: int = 10) -> None:
        """运行模拟"""
        logger.info("开始游戏模拟")

        # 初始化游戏状态
        self.game_state = self.create_sample_game_state()
        self.initialize_strategies()
        self.initialize_coordinators()

        logger.info(f"游戏初始化完成，地图大小: {self.game_state.map_width}x{self.game_state.map_height}")
        logger.info(f"我方角色: {list(self.game_state.roles.keys())}")
        logger.info(f"敌方角色: {list(self.game_state.enemies.keys())}")

        # 运行指定回合数
        for turn in range(turns):
            self.simulate_turn()

            # 检查游戏是否结束
            alive_allies = sum(1 for role in self.game_state.roles.values() if role.is_alive)
            alive_enemies = sum(1 for role in self.game_state.enemies.values() if role.is_alive)

            if alive_allies == 0:
                logger.info("我方全军覆没，游戏结束！")
                break
            elif alive_enemies == 0:
                logger.info("敌方全军覆没，我方获胜！")
                break

            logger.info("")  # 空行分隔

        logger.info("游戏模拟结束")


def main():
    """主函数"""
    print("Honor For Legends - 分层状态机架构示例")
    print("=" * 50)

    # 创建并运行游戏模拟
    simulation = GameSimulation()
    simulation.run_simulation(turns=15)


if __name__ == "__main__":
    main()