# Honor For Legends - 使用指南

## 概述

这是一个为类MOBA回合制对战游戏设计的分层状态机架构，提供了完整的策略抽象、态势感知、动作执行和多角色协同功能。

## 核心特性

### 1. 策略抽象 (Strategy Abstraction)
- **BaseStrategy**: 所有策略的基类，提供统一的策略接口
- **StrategySelector**: 智能策略选择器，根据战场态势自动选择最优策略
- **内置策略**: 进攻、防守、辅助、团战等多种预设策略

### 2. 态势感知 (Situation Awareness)
- **SituationAwareness**: 全面的战场分析系统
- **威胁评估**: 实时计算威胁等级和危险程度
- **目标选择**: 智能选择最优攻击和支援目标

### 3. 动作执行 (Action Execution)
- **ActionExecutor**: 可靠的动作执行和验证系统
- **ActionOptimizer**: 动作优化器，提升决策质量
- **技能管理**: 完整的技能冷却和魔法值管理

### 4. 多角色协同 (Team Coordination)
- **TeamCoordinator**: 团队级协同管理
- **RoleCoordinator**: 角色级决策协调
- **队形控制**: 支持多种战术队形

## 快速开始

### 1. 基本使用

```python
from src.core import GameState, Role, Position
from src.sensors import SituationAwareness
from src.strategies import StrategyManager, OffensiveStrategy, DefensiveStrategy
from src.actions import ActionExecutor

# 创建游戏状态
game_state = GameState(
    roles={...},  # 我方角色
    enemies={...},  # 敌方角色
    towers=[...],  # 防御塔
    crystals=[...],  # 水晶
    current_turn=0,
    map_width=1000,
    map_height=800
)

# 创建策略管理器
strategy_manager = StrategyManager()

# 为角色注册策略
selector = StrategySelector()
selector.register_strategy(OffensiveStrategy())
selector.register_strategy(DefensiveStrategy())
strategy_manager.register_role_strategy(role_id, selector)

# 获取角色动作
action = strategy_manager.get_action_for_role(game_state, role, current_turn)

# 执行动作
executor = ActionExecutor()
result = executor.execute_action(game_state, role, action, current_turn)
```

### 2. 创建自定义策略

```python
from src.strategies.base_strategy import BaseStrategy, StrategyResult, StrategyType
from src.core import Action, ActionType

class CustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("自定义策略", StrategyType.OFFENSIVE)

    def evaluate(self, game_state: GameState, role: Role) -> float:
        """评估策略适用性"""
        situation = self.get_battle_situation(game_state, role)

        # 根据战场情况返回0-1的分数
        score = 0.5
        if role.health_percentage > 0.7:
            score += 0.3
        if situation.team_advantage > 0.2:
            score += 0.2

        return min(1.0, score)

    def execute(self, game_state: GameState, role: Role) -> StrategyResult:
        """执行策略"""
        target = self.situation_awareness.find_best_target(game_state, role)

        if target:
            action = Action(
                action_type=ActionType.ATTACK,
                target_id=target.id,
                priority=2
            )
            return StrategyResult(
                action=action,
                confidence=0.8,
                reasoning="攻击最优目标",
                priority=2
            )

        return StrategyResult(
            action=None,
            confidence=0.0,
            reasoning="没有找到目标",
            priority=0
        )

    def get_transition_conditions(self) -> Dict[StrategyType, float]:
        """获取策略转换条件"""
        return {
            StrategyType.DEFENSIVE: 0.3,  # 血量低于30%时转换为防守
            StrategyType.SUPPORT: 0.2     # 队友需要帮助时转换为辅助
        }
```

### 3. 使用团队协同

```python
from src.coordinators import TeamCoordinator

# 创建团队协调器
team_coordinator = TeamCoordinator()

# 更新团队策略
team_coordinator.update_team_strategy(game_state, current_turn)

# 获取团队协同动作
action = team_coordinator.get_role_action(game_state, role, current_turn)

# 协同移动
formation_positions = team_coordinator.coordinate_team_movement(
    game_state,
    target_position=Position(500, 400),
    formation="wedge"
)

# 协同防守
defense_positions = team_coordinator.should_coordinate_defense(game_state)
```

### 4. 角色级协调

```python
from src.coordinators import RoleCoordinator, RoleDirective

# 创建角色协调器
role_coordinator = RoleCoordinator(role_id)

# 设置角色指令
directive = RoleDirective(
    primary_target="enemy_mage",
    position_priority=[Position(400, 300), Position(500, 400)],
    engagement_rules={"cautious": True},
    coordination_requests=["support_1"]
)
role_coordinator.update_directive(directive)

# 获取协调后的动作
coordinated_action = role_coordinator.get_coordinated_action(
    game_state, role, strategy_result, current_turn
)

# 检查是否需要支援
if role_coordinator.should_request_support(game_state, role):
    support_info = role_coordinator.get_support_request_info(game_state, role)
    # 处理支援请求
```

## 高级特性

### 1. 态势感知定制

```python
from src.sensors import SituationAwareness

# 自定义感知参数
awareness = SituationAwareness(
    danger_health_threshold=0.4,  # 危险血量阈值
    danger_mana_threshold=0.3    # 危险魔法阈值
)

# 分析战场态势
battle_situation = awareness.analyze_battle_situation(game_state, role)
print(f"威胁等级: {battle_situation.threat_level}")
print(f"团队优势: {battle_situation.team_advantage}")

# 分析角色状态
role_status = awareness.analyze_role_status(game_state, role)
print(f"是否危险: {role_status.is_in_danger}")
```

### 2. 动作优化

```python
from src.actions import ActionOptimizer

optimizer = ActionOptimizer()

# 优化单个动作
optimized_action = optimizer.optimize_action(game_state, role, strategy_result)

# 从多个候选动作中选择最优
candidates = [action1, action2, action3]
best_action = optimizer.optimize_multiple_actions(game_state, role, candidates)
```

### 3. 技能管理

```python
from src.actions import ActionExecutor

executor = ActionExecutor()

# 执行技能攻击
skill_action = Action(
    action_type=ActionType.SKILL_ATTACK,
    target_id="enemy_mage",
    skill_id="fireball",
    priority=3
)
result = executor.execute_action(game_state, role, skill_action, current_turn)

# 检查技能冷却
cooldowns = executor.get_skill_cooldowns(role_id)
print(f"技能冷却: {cooldowns}")
```

## 架构说明

### 分层架构

```
策略层 (Strategy Layer)
├── BaseStrategy - 策略基类
├── StrategySelector - 策略选择器
└── 具体策略实现

感知层 (Sensing Layer)
└── SituationAwareness - 态势感知系统

执行层 (Execution Layer)
├── ActionExecutor - 动作执行器
└── ActionOptimizer - 动作优化器

协同层 (Coordination Layer)
├── TeamCoordinator - 团队协调器
└── RoleCoordinator - 角色协调器
```

### 策略切换流程

1. **战场分析**: SituationAwareness 分析当前战场态势
2. **策略评估**: 每个策略评估自己的适用性分数
3. **策略选择**: StrategySelector 选择分数最高的策略
4. **动作生成**: 选中的策略生成具体的动作
5. **动作优化**: ActionOptimizer 优化动作质量
6. **协同调整**: 协调器根据团队需求调整动作
7. **动作执行**: ActionExecutor 执行最终动作

### 多角色协同机制

1. **团队计划制定**: TeamCoordinator 根据战场形势制定团队目标
2. **角色任务分配**: 为每个角色分配具体的任务和位置
3. **协同动作执行**: 角色间相互配合执行团队战术
4. **动态调整**: 根据战场变化动态调整协同策略

## 最佳实践

### 1. 策略设计原则

- **单一职责**: 每个策略专注于特定的战术目标
- **状态评估**: 准确评估策略的适用条件
- **平滑切换**: 设计合理的策略转换条件
- **冷却管理**: 合理使用技能冷却机制

### 2. 性能优化

- **缓存计算结果**: 避免重复计算战场态势
- **限制搜索范围**: 限制目标搜索的距离范围
- **合理使用日志**: 控制日志输出频率
- **异步处理**: 对于复杂计算考虑异步处理

### 3. 扩展建议

- **新策略类型**: 继承BaseStrategy实现新的策略
- **新队形支持**: 在TeamCoordinator中添加新的队形算法
- **自定义感知**: 扩展SituationAwareness添加专用的感知功能
- **插件系统**: 设计插件架构支持模块化扩展

## 故障排除

### 常见问题

1. **角色不做任何动作**
   - 检查角色是否存活
   - 确认策略是否正确注册
   - 验证动作验证是否通过

2. **策略频繁切换**
   - 调整策略转换条件阈值
   - 增加最小策略持续时间
   - 检查战场态势计算是否正确

3. **协同动作不执行**
   - 确认团队计划是否正确制定
   - 检查角色分配是否有效
   - 验证动作优先级设置

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查策略评分
for strategy in selector.strategies.values():
    score = strategy.evaluate(game_state, role)
    print(f"{strategy.name}: {score}")

# 查看团队状态
team_status = team_coordinator.get_team_status(game_state)
print(f"当前目标: {team_status['current_objective']}")

# 检查动作执行历史
history = executor.get_execution_history(role_id)
for turn, role_id, result in history:
    print(f"回合{turn}: {result.message}")
```

## API参考

详细的API文档请参考各个模块的源代码注释，每个类和方法都有详细的使用说明和参数说明。