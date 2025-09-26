# Cloud Code Coding Race - 分层状态机架构

这是一个为类MOBA回合制对战游戏设计的分层状态机架构项目，用于实现智能的角色决策系统和团队协作策略。

## 项目概述

本项目实现了基于分层状态机的MOBA游戏AI控制系统，包含以下核心模块：

- **策略系统**：支持多种战术策略的动态切换
- **感知系统**：实时分析战场态势和环境信息
- **动作执行**：优化角色动作的执行和协调
- **团队协作**：多角色协同作战和分工

## 架构设计

### 整体架构

![系统架构图](docs/architecture.md#1-整体架构图)

本项目采用分层架构设计，从底层的游戏状态处理到高层的策略决策，形成了完整的AI决策系统。

### 核心模块

#### 📁 src/core
- `base.py` - 基础数据结构和游戏状态定义
- `state_machine.py` - 分层状态机实现
- `__init__.py` - 模块导出

#### 📁 src/sensors
- `situation_awareness.py` - 战场态势感知和分析

#### 📁 src/strategies
- `base_strategy.py` - 策略基类和接口定义
- `concrete_strategies.py` - 具体策略实现
- `__init__.py` - 模块导出

#### 📁 src/actions
- `action_executor.py` - 动作执行器
- `action_optimizer.py` - 动作优化器
- `__init__.py` - 模块导出

#### 📁 src/states
- `offensive.py` - 进攻状态
- `defensive.py` - 防守状态
- `support.py` - 支援状态
- `__init__.py` - 模块导出

#### 📁 src/coordinators
- `team_coordinator.py` - 团队协调器
- `role_coordinator.py` - 角色协调器
- `__init__.py` - 模块导出

### 技术特性

- **分层状态机**：支持复杂的状态管理和转换
- **策略模式**：灵活的策略切换和扩展
- **态势感知**：实时战场环境分析
- **多角色协作**：智能团队配合机制
- **动作优化**：高效的决策执行系统

### 决策流程

![状态机流程图](docs/architecture.md#2-分层状态机流程图)

系统通过感知-决策-执行-评估的循环，实现智能的角色行为控制。

### 策略切换机制

![策略切换图](docs/architecture.md#3-策略切换决策图)

根据战场态势的动态变化，自动选择最优的策略组合。

## 快速开始

### 环境要求

- Python 3.13+
- 无外部依赖（纯Python实现）

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd CloudCodeCodingRace

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
```

### 运行示例

```bash
# 运行示例程序
python example.py

# 运行主程序
python main.py
```

## 使用示例

### 基础用法

```python
from src.core import GameState, Role, Position
from src.sensors import SituationAwareness
from src.strategies import StrategyManager
from src.coordinators import TeamCoordinator

# 创建游戏状态
game_state = GameState(...)

# 初始化组件
situation_awareness = SituationAwareness()
strategy_manager = StrategyManager()
team_coordinator = TeamCoordinator()

# 分析战场态势
battle_situation = situation_awareness.analyze_battle_situation(game_state)

# 选择策略
strategy = strategy_manager.select_strategy(battle_situation)

# 协调团队行动
actions = team_coordinator.coordinate_team(game_state, strategy)
```

### 高级用法

查看 `example.py` 文件获取完整的使用示例，包括：

- 游戏状态模拟
- 多角色协同
- 策略切换
- 动作优化

## 主要功能

### 策略系统
- **进攻策略**：主动进攻敌方目标
- **防守策略**：保护我方阵地
- **支援策略**：协助队友作战
- **团队战斗**：集体作战协调

### 感知系统
- **威胁评估**：分析敌方威胁程度
- **战场分析**：评估整体战局
- **位置感知**：计算距离和位置关系
- **状态监控**：跟踪角色状态变化

### 协作机制
- **角色分工**：根据角色特性分配任务
- **目标协同**：统一作战目标
- **资源调度**：合理分配资源
- **战术配合**：复杂的战术组合

## 架构图详情

更多详细的架构图和技术说明请参考 [架构文档](docs/architecture.md)，包括：

- **模块依赖关系图**：展示各模块间的依赖关系
- **时序图**：描述决策执行的时序流程
- **详细流程图**：各个子系统的详细工作流程

## 开发指南

### 添加新策略

1. 在 `src/strategies/concrete_strategies.py` 中实现新的策略类
2. 继承 `BaseStrategy` 基类
3. 实现必要的抽象方法
4. 在策略管理器中注册新策略

### 扩展感知功能

1. 在 `src/sensors/situation_awareness.py` 中添加新的分析方法
2. 定义相应的数据结构
3. 集成到现有感知系统中

### 自定义动作

1. 在动作相关模块中添加新的动作类型
2. 实现动作执行逻辑
3. 添加优化规则

## 配置

项目支持通过配置文件进行自定义设置，包括：

- 策略参数
- 感知阈值
- 动作优先级
- 团队协调规则

## 贡献指南

欢迎提交问题和改进建议！请确保：

1. 遵循现有代码风格
2. 添加适当的测试
3. 更新相关文档
4. 提交前运行自检

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues
- 项目讨论区