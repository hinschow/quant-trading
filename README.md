# 数字货币量化交易系统 v3.2

基于 v3.1 稳健收益版的完整实现，融合趋势跟踪与均值回归策略，目标年化收益 15-25%，最大回撤 ≤8%。

## 项目特点

- ✅ **双策略引擎**：趋势跟踪 + 均值回归 + 布林带增强
- ✅ **动态风险调整**：根据市场环境自适应调整仓位
- ✅ **多交易所支持**：Binance、OKX、Bybit
- ✅ **完整回测系统**：历史数据验证 + 参数优化
- ✅ **实时监控告警**：Telegram 通知 + Grafana 仪表板
- ✅ **容器化部署**：Docker Compose 一键启动

## 目录结构

```
quant_trading/
├── config/                  # 配置文件
│   ├── settings.py         # 全局配置
│   ├── strategy_params.py  # 策略参数
│   └── risk_params.py      # 风险参数
├── data/                    # 数据模块
│   ├── collectors/         # 数据采集器
│   │   ├── binance_collector.py
│   │   ├── okx_collector.py
│   │   └── bybit_collector.py
│   └── storage/            # 数据存储
│       ├── redis_handler.py
│       └── postgres_handler.py
├── strategies/             # 策略模块
│   ├── base_strategy.py   # 策略基类
│   ├── trend_following.py # 趋势跟踪
│   ├── mean_reversion.py  # 均值回归
│   └── market_regime.py   # 市场状态识别
├── execution/              # 交易执行
│   ├── order_manager.py   # 订单管理
│   ├── position_manager.py # 仓位管理
│   └── smart_router.py    # 智能路由
├── risk/                   # 风险管理
│   ├── risk_manager.py    # 风险管理器
│   ├── position_sizer.py  # 仓位计算
│   └── circuit_breaker.py # 熔断机制
├── backtest/               # 回测系统
│   ├── engine.py          # 回测引擎
│   ├── metrics.py         # 性能指标
│   └── optimizer.py       # 参数优化
├── monitor/                # 监控模块
│   ├── performance_tracker.py
│   ├── alert_manager.py
│   └── telegram_bot.py
├── utils/                  # 工具模块
│   ├── logger.py          # 日志系统
│   ├── indicators.py      # 技术指标
│   └── helpers.py         # 辅助函数
├── tests/                  # 测试
├── logs/                   # 日志文件
├── docker-compose.yml      # Docker 配置
├── requirements.txt        # 依赖包
├── .env.example           # 环境变量示例
└── main.py                # 主程序入口
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

### 4. 启动服务

```bash
# 启动数据库和缓存
docker-compose up -d

# 初始化数据库
python scripts/init_db.py

# 运行回测
python main.py --mode backtest --start 2022-01-01 --end 2024-12-31

# 运行模拟交易
python main.py --mode paper

# 运行实盘交易（谨慎！）
python main.py --mode live
```

## 策略说明

### 市场状态识别（整合 ADX + BBW）

| 状态 | 条件 | 策略 | 仓位 |
|------|------|------|------|
| STRONG_TREND | ADX>30 且 BBW>1.2 | 趋势跟踪 | 100% |
| TREND | ADX>25 且 BBW>1.0 | 趋势跟踪 | 80% |
| RANGE | ADX<18 且 BBW<0.8 | 均值回归 | 60% |
| SQUEEZE | BBW<0.5 | 突破策略 | 30% |
| NEUTRAL | 其他 | 空仓 | 0% |

### 趋势跟踪策略

- **指标**：EMA(50/200)、ADX(30)、成交量确认
- **止损**：1.5%
- **止盈**：3%
- **移动止损**：盈利>2%后移至成本价

### 均值回归策略

- **指标**：RSI(25/75)、布林带(2.5σ)、ATR过滤
- **止损**：1.5%
- **止盈**：价格回归中轨或RSI回到50

## 风险控制

- 单笔风险：≤1% 账户资金
- 总仓位：≤50%
- 单日最大亏损：≤3%
- 最大回撤：≤8%（触发预警）
- 熔断机制：回撤≥10% 全部平仓

## 性能目标

| 指标 | 目标值 |
|------|--------|
| 年化收益率 | 15-25% |
| 最大回撤 | ≤8% |
| 夏普比率 | ≥2.5 |
| 盈亏比 | ≥1.8:1 |
| 胜率 | ≥55% |

## 监控与告警

- **Telegram 通知**：交易信号、风险告警、每日报告
- **Grafana 仪表板**：实时性能、仓位、收益曲线
- **日志系统**：所有交易和风控事件记录

## 测试

```bash
# 单元测试
pytest tests/

# 策略回测
python -m backtest.engine --config config/backtest.yaml

# 性能测试
python tests/performance_test.py
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。数字货币交易具有极高风险，请谨慎使用。

---

**版本**：v3.2
**作者**：hins chow
**更新时间**：2025-10-23
