# 项目目录结构

```
quant-trading/
├── 📄 核心文档
│   ├── README.md                      # 项目介绍
│   ├── QUICK_START_BACKTEST.md        # 快速开始指南 ⭐
│   ├── PARAMETER_GUIDE.md             # 参数配置指南 ⭐
│   ├── IMPLEMENTATION_STATUS.md       # 实施状态报告
│   └── PROJECT_LAYOUT.md              # 本文件
│
├── ⚙️ 配置文件
│   ├── config/
│   │   ├── strategy_params.py         # 策略参数配置 ⭐
│   │   └── storage_params.py          # 存储参数配置
│   ├── .env.example                   # 环境变量模板
│   └── docker-compose.yml             # Docker配置
│
├── 🔧 核心工具
│   ├── config_manager.py              # 配置管理工具 ⭐
│   ├── backtest_engine.py             # 回测引擎 ⭐
│   ├── test_backtest.sh               # 测试脚本
│   └── requirements.txt               # Python依赖
│
├── 🎯 策略引擎
│   ├── strategy_engine.py             # 策略引擎（信号生成）⭐
│   ├── data_collector.py              # 数据采集器
│   ├── realtime_engine.py             # 实时信号引擎
│   └── websocket_stream.py            # WebSocket数据流
│
├── 📊 分析工具
│   ├── signal_analyzer.py             # 信号分析工具
│   ├── realtime_monitor_pro.py        # 实时监控（双流）
│   ├── multi_monitor.py               # 多币种监控
│   └── query_signals.py               # 信号查询工具
│
├── 🛠️ 工具模块
│   └── utils/
│       ├── indicators.py              # 技术指标库
│       ├── market_sentiment.py        # 市场情绪分析
│       ├── exchange_info.py           # 交易所信息
│       ├── signal_storage.py          # 信号存储
│       ├── signal_logger.py           # 信号日志
│       └── data_buffer.py             # 数据缓冲
│
├── 🗃️ 归档文件
│   └── archived/
│       ├── docs/                      # 旧版文档（已归档）
│       └── main.py                    # 旧版主程序
│
└── 📦 脚本
    └── scripts/
        └── init_db.sql                # 数据库初始化

```

## 🎯 快速导航

### 新手入门
1. 阅读 [README.md](README.md) 了解项目
2. 查看 [QUICK_START_BACKTEST.md](QUICK_START_BACKTEST.md) 开始回测
3. 参考 [PARAMETER_GUIDE.md](PARAMETER_GUIDE.md) 调整参数

### 回测验证
1. 运行 `./test_backtest.sh` 快速测试
2. 使用 `python3 backtest_engine.py BTC/USDT -t 1h` 回测
3. 查看 `backtest_trades_*.csv` 分析交易记录

### 配置管理
1. 查看配置: `python3 config_manager.py --show-all`
2. 修改配置: `nano config/strategy_params.py`
3. 对比配置: `python3 config_manager.py --compare aggressive`

### 实时监控
1. 信号分析: `python3 signal_analyzer.py BTC/USDT -t 1h`
2. 实时监控: `python3 realtime_monitor_pro.py BTC/USDT -t 15m`
3. 多币监控: `python3 multi_monitor.py`

## 📝 核心文件说明

### 必读文档 ⭐

| 文件 | 作用 | 何时阅读 |
|-----|------|---------|
| [README.md](README.md) | 项目介绍 | 首次使用 |
| [QUICK_START_BACKTEST.md](QUICK_START_BACKTEST.md) | 回测快速开始 | 开始回测前 |
| [PARAMETER_GUIDE.md](PARAMETER_GUIDE.md) | 参数详细说明 | 调整参数前 |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | 实施状态 | 了解进度 |

### 核心配置文件 ⚙️

| 文件 | 作用 | 修改频率 |
|-----|------|---------|
| [config/strategy_params.py](config/strategy_params.py) | 策略参数 | 经常 ⭐ |
| [.env.example](.env.example) | API密钥模板 | 一次 |

### 核心工具 🔧

| 文件 | 作用 | 使用场景 |
|-----|------|---------|
| [backtest_engine.py](backtest_engine.py) | 回测引擎 | 验证策略 ⭐ |
| [config_manager.py](config_manager.py) | 配置管理 | 查看/对比配置 |
| [strategy_engine.py](strategy_engine.py) | 策略引擎 | 信号生成核心 |

## 🗂️ 文件组织原则

### 保留在根目录
- ✅ 核心文档（README、快速开始、参数指南）
- ✅ 主要工具脚本（回测、配置管理）
- ✅ 策略和分析工具

### 归档到 archived/
- ✅ 旧版文档
- ✅ 历史分析报告
- ✅ 已废弃的代码

### 放入子目录
- ✅ 配置文件 → `config/`
- ✅ 工具模块 → `utils/`
- ✅ 初始化脚本 → `scripts/`

---

**更新时间**: 2025-10-27
**项目版本**: v3.2
