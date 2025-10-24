# 📁 量化交易系统项目结构

## 🎯 系统概览

这是一个完整的量化交易信号分析系统，包含两个核心功能：

1. **批量分析** - 一次性分析多个交易对，筛选机会
2. **实时监控** - WebSocket 实时监听，及时捕捉信号

---

## 📂 项目结构

```
quant-trading/
├── 📊 核心模块
│   ├── data_collector.py          # 数据抓取（历史K线）
│   ├── strategy_engine.py         # 策略引擎（信号生成）
│   ├── signal_analyzer.py         # 批量分析工具
│   ├── websocket_stream.py        # WebSocket 数据流
│   ├── realtime_engine.py         # 实时信号引擎
│   └── realtime_monitor.py        # 实时监控主程序
│
├── 🛠️ 工具模块
│   └── utils/
│       ├── indicators.py          # 技术指标计算
│       └── data_buffer.py         # 数据缓冲区管理
│
├── ⚙️ 配置文件
│   └── config/
│       ├── strategy_params.py     # 策略参数
│       └── risk_params.py         # 风险参数
│
├── 📚 文档
│   ├── README.md                  # 项目说明
│   ├── SIGNAL_ANALYZER_GUIDE.md   # 批量分析使用指南
│   ├── REALTIME_MONITOR_GUIDE.md  # 实时监控使用指南
│   ├── NETWORK_TROUBLESHOOTING.md # 网络问题排查
│   ├── PROJECT_STRUCTURE.md       # 项目结构（本文档）
│   └── DEPLOYMENT_GUIDE.md        # 部署指南
│
├── 🗄️ 数据和脚本
│   ├── scripts/
│   │   └── init_db.sql            # 数据库初始化
│   ├── logs/                      # 日志目录
│   └── data/                      # 数据目录
│
└── 🔧 配置和依赖
    ├── requirements.txt           # Python 依赖
    ├── docker-compose.yml         # Docker 配置
    ├── .env.example               # 环境变量模板
    └── .gitignore                 # Git 忽略文件
```

---

## 🔄 系统架构

### 1. 批量分析架构

```
┌─────────────────┐
│  用户命令行请求   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ signal_analyzer │ ◄── 用户输入（交易对、周期）
└────────┬────────┘
         │
         ├─► DataCollector ──► 交易所API ──► 获取历史K线
         │
         ├─► StrategyEngine
         │   ├─► Indicators (计算EMA/RSI/MACD/ADX/BBW)
         │   ├─► 市场状态识别
         │   └─► 信号生成（趋势/均值回归/突破）
         │
         └─► 格式化输出 ──► 终端显示
```

### 2. 实时监控架构

```
┌─────────────────┐
│   WebSocket     │
│  连接交易所      │
└────────┬────────┘
         │ 实时K线数据
         ▼
┌─────────────────┐
│  KlineBuffer    │ ◄── 维护滚动窗口（最近500条）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RealtimeEngine  │
│  ├─► 检测新K线封闭
│  ├─► 计算技术指标
│  ├─► 生成交易信号
│  └─► 信号变化检测
└────────┬────────┘
         │
         ├─► 实时状态更新（单行刷新）
         └─► 信号变化提醒（完整输出）
```

---

## 📦 核心模块说明

### data_collector.py

**功能：** 从交易所获取历史K线数据

**主要类：**
```python
class DataCollector:
    def __init__(exchange_name, proxy)
    def fetch_ohlcv(symbol, timeframe, limit)
    def fetch_recent_data(symbol, timeframe, days)
    def get_current_price(symbol)
```

**特点：**
- 支持多交易所（Binance, OKX, Bybit等）
- 代理支持
- 备用域名自动切换
- 错误重试

---

### strategy_engine.py

**功能：** 策略引擎，计算指标并生成信号

**主要类：**
```python
class StrategyEngine:
    def calculate_all_indicators(df)        # 计算所有指标
    def identify_market_regime(df)          # 识别市场状态
    def generate_trend_signal(df)           # 趋势跟随信号
    def generate_mean_reversion_signal(df)  # 均值回归信号
    def generate_signal(df)                 # 综合信号生成
```

**支持的指标：**
- EMA (50/200)
- MACD (12/26/9)
- RSI (14)
- ADX (14) + DI
- Bollinger Bands (20, 2std)
- BBW (Bollinger Band Width)
- ATR (14)

**市场状态：**
- STRONG_TREND - 强趋势
- TREND - 趋势
- RANGE - 震荡
- SQUEEZE - 挤压
- NEUTRAL - 中性

**策略类型：**
- 趋势跟随（TREND_FOLLOWING）
- 均值回归（MEAN_REVERSION）
- 突破等待（BREAKOUT_WAIT）

---

### signal_analyzer.py

**功能：** 批量分析工具（命令行）

**使用场景：**
- 盘前扫描交易机会
- 批量分析多个币种
- 快速查看市场状态

**示例：**
```bash
# 分析单个
python signal_analyzer.py BTC/USDT

# 分析多个
python signal_analyzer.py BTC/USDT ETH/USDT SOL/USDT

# 批量扫描
python signal_analyzer.py --scan USDT --min-strength 60
```

---

### websocket_stream.py

**功能：** WebSocket 数据流管理

**主要类：**
```python
class WebSocketStream:
    async def watch_ohlcv(symbol, timeframe, callback)
    async def watch_trades(symbol, callback)
```

**特点：**
- 优先使用 ccxt.pro WebSocket
- 自动降级到轮询模式
- 错误自动重连
- 灵活的回调机制

---

### realtime_engine.py

**功能：** 实时信号引擎

**主要类：**
```python
class RealtimeSignalEngine:
    def initialize(historical_data)        # 历史数据初始化
    async def on_kline(kline)              # 处理新K线
    def _generate_signal()                 # 生成信号
    def get_signal()                       # 获取当前信号
```

**工作流程：**
1. 用历史数据初始化缓冲区
2. 实时接收新K线
3. 检测K线封闭
4. 重新计算指标
5. 生成新信号
6. 检测信号变化
7. 触发回调

---

### realtime_monitor.py

**功能：** 实时监控主程序（命令行）

**使用场景：**
- 盘中实时监控
- 及时捕捉信号变化
- 持续追踪市场

**示例：**
```bash
# 监控 BTC 1小时
python realtime_monitor.py BTC/USDT -t 1h --proxy http://127.0.0.1:7890

# 监控 ETH 15分钟
python realtime_monitor.py ETH/USDT -t 15m --proxy http://127.0.0.1:7890
```

---

### utils/indicators.py

**功能：** 技术指标计算库

**主要函数：**
```python
calculate_ema(df, period)
calculate_macd(df, fast, slow, signal)
calculate_rsi(df, period)
calculate_adx(df, period)
calculate_bollinger_bands(df, period, std)
calculate_bbw(df, period, std)
calculate_atr(df, period)
```

**依赖：** TA-Lib（专业的技术分析库）

---

### utils/data_buffer.py

**功能：** K线数据缓冲区管理

**主要类：**
```python
class KlineBuffer:
    def initialize(historical_data)       # 初始化
    def update_kline(kline)               # 更新K线
    def to_dataframe(include_current)     # 转为DataFrame
    def is_ready(min_periods)             # 检查就绪
```

**特点：**
- 使用 deque 实现高效滚动窗口
- 自动维护最近 N 条K线
- 支持当前正在形成的K线
- 内存高效

---

## ⚙️ 配置系统

### config/strategy_params.py

**包含：**
- `MARKET_REGIME_PARAMS` - 市场状态识别参数
- `TREND_FOLLOWING_PARAMS` - 趋势跟随策略参数
- `MEAN_REVERSION_PARAMS` - 均值回归策略参数
- `BREAKOUT_PARAMS` - 突破策略参数
- `SIGNAL_FUSION_PARAMS` - 信号融合参数

**可调参数：**
- EMA 周期（默认 50/200）
- RSI 阈值（默认 25/75）
- ADX 阈值（默认 30）
- 布林带参数（默认 20, 2std）
- 止盈止损比例

### config/risk_params.py

**包含：**
- `ACCOUNT_RISK_LIMITS` - 账户风险限制
- `POSITION_SIZE_PARAMS` - 仓位管理参数
- `DYNAMIC_RISK_ADJUSTMENT` - 动态风险调整

---

## 🔀 数据流向

### 批量分析数据流

```
用户输入 → signal_analyzer.py
    ↓
DataCollector.fetch_ohlcv()
    ↓
交易所 API → 返回历史K线 (DataFrame)
    ↓
StrategyEngine.generate_signal()
    ↓
Indicators 计算 → EMA/RSI/MACD/ADX/BBW
    ↓
市场状态识别 → STRONG_TREND/TREND/RANGE/SQUEEZE/NEUTRAL
    ↓
信号生成 → BUY/SELL/HOLD + 强度 + 理由
    ↓
格式化输出 → 终端显示
```

### 实时监控数据流

```
启动 realtime_monitor.py
    ↓
1. DataCollector 获取历史数据 → 初始化 KlineBuffer
    ↓
2. WebSocketStream 连接交易所
    ↓
3. 实时K线数据流 → on_kline() 回调
    ↓
4. KlineBuffer.update_kline() → 更新缓冲区
    ↓
5. 检测K线封闭 → 是新K线?
    ↓
6. RealtimeEngine.generate_signal()
    ├─► Indicators 计算
    ├─► 市场状态识别
    └─► 信号生成
    ↓
7. 检测信号变化 → 操作改变?
    ├─► 是 → 完整信号输出 + 提醒
    └─► 否 → 单行状态更新
```

---

## 🎯 使用场景对比

| 场景 | 工具 | 优势 | 使用时机 |
|------|------|------|----------|
| **盘前筛选** | signal_analyzer | 快速扫描多个币种 | 开盘前 |
| **批量对比** | signal_analyzer | 一次看多个币种 | 寻找机会 |
| **实时监控** | realtime_monitor | 及时捕捉信号 | 盘中 |
| **信号提醒** | realtime_monitor | 自动通知变化 | 持续追踪 |
| **短线交易** | realtime_monitor (15m) | 高频更新 | 日内交易 |
| **中长线** | signal_analyzer (4h/1d) | 降低噪音 | 波段交易 |

---

## 🛠️ 开发指南

### 添加新的技术指标

1. 在 `utils/indicators.py` 添加计算函数
2. 在 `StrategyEngine.calculate_all_indicators()` 中调用
3. 在策略逻辑中使用新指标

### 添加新的策略

1. 在 `config/strategy_params.py` 添加参数
2. 在 `StrategyEngine` 中添加策略方法
3. 在 `generate_signal()` 中集成

### 自定义输出格式

修改 `signal_analyzer.py` 或 `realtime_monitor.py` 中的显示函数

### 添加通知功能

在 `realtime_monitor.py` 的 `on_signal_change()` 中添加：
- Telegram 机器人
- 邮件
- 短信
- 系统通知

---

## 📊 性能优化

### 内存管理

- KlineBuffer 使用 `deque` 限制最大长度
- DataFrame 操作后及时删除
- 避免不必要的数据复制

### 计算优化

- 指标只在新K线封闭时计算
- 缓存计算结果
- 使用向量化操作（NumPy/Pandas）

### 网络优化

- 优先使用 WebSocket（减少请求）
- 启用代理（加速访问）
- 错误重试和超时设置

---

## 🔐 安全建议

1. **API 密钥管理**
   - 使用 `.env` 文件
   - 永远不要提交到 Git
   - 定期轮换密钥

2. **风险控制**
   - 设置止损
   - 控制仓位
   - 测试模式先运行

3. **数据安全**
   - 本地数据加密
   - 日志脱敏
   - 定期备份

---

## 📈 扩展方向

### 短期（1-2周）

- [ ] 添加更多技术指标（KDJ、BOLL、威廉指标）
- [ ] Telegram 通知集成
- [ ] 信号历史记录

### 中期（1个月）

- [ ] 回测引擎
- [ ] 参数优化器
- [ ] Web 界面
- [ ] 数据库持久化

### 长期（2-3个月）

- [ ] 机器学习模型集成
- [ ] 多策略组合
- [ ] 自动交易（谨慎）
- [ ] 风险管理系统

---

## 🤝 贡献指南

欢迎贡献！请遵循：

1. Fork 项目
2. 创建 feature 分支
3. 提交 Pull Request
4. 代码风格遵循 PEP 8
5. 添加测试和文档

---

## 📞 获取帮助

- [SIGNAL_ANALYZER_GUIDE.md](SIGNAL_ANALYZER_GUIDE.md) - 批量分析详细教程
- [REALTIME_MONITOR_GUIDE.md](REALTIME_MONITOR_GUIDE.md) - 实时监控详细教程
- [NETWORK_TROUBLESHOOTING.md](NETWORK_TROUBLESHOOTING.md) - 网络问题解决

---

## 📝 更新日志

### v2.0 (2025-10-24)
- ✅ 添加 WebSocket 实时监控
- ✅ 数据缓冲区管理
- ✅ 实时信号引擎
- ✅ 完整文档

### v1.0 (2025-10-23)
- ✅ 批量信号分析
- ✅ 技术指标计算
- ✅ 策略引擎
- ✅ 市场状态识别

---

祝交易顺利！📈💰
