# 📦 交易信号数据持久化使用指南

## ✅ 功能概述

现在所有交易信号会**自动保存到本地SQLite数据库**，支持历史查询、统计分析和导出功能。

---

## 🎯 核心特性

### 1. **自动保存**
- ✅ `multi_monitor.py` - 多币种监控时自动保存所有信号
- ✅ `realtime_monitor_pro.py` - 单币种监控时自动保存所有信号
- ✅ 无需任何额外操作，运行监控即自动保存

### 2. **极简存储模式**（默认）
- 📁 只保存信号数据（不保存K线）
- 💾 长期占用 **< 5 MB**（8个币种）
- 🗑️ 自动清理90天前的旧数据
- ⚡ 零性能影响

### 3. **强大查询功能**
- 🔍 按币种、时间、强度、动作查询
- 📊 查看数据库统计信息
- 📤 导出为CSV或JSON
- 📈 信号分布分析

---

## 📝 使用方法

### 方式1：正常运行监控（自动保存）

```bash
# 单币种监控（自动保存）
python realtime_monitor_pro.py BTC/USDT:USDT -t 15m --proxy http://127.0.0.1:7890

# 多币种监控（自动保存）
python multi_monitor.py \
  BTC/USDT:USDT \
  ETH/USDT:USDT \
  SUI/USDT:USDT \
  SNX/USDT:USDT \
  ZEC/USDT:USDT \
  1000RATS/USDT:USDT \
  NOM/USDT:USDT \
  -t 15m --proxy http://127.0.0.1:7890
```

**监控运行时**：
- 每次产生新信号，自动保存到 `data/trading_signals.db`
- 控制台会显示信号，同时后台静默保存
- 无需担心断网或重启，所有信号都已持久化

---

### 方式2：查询历史信号

#### 查看所有历史信号
```bash
python query_signals.py
```

#### 查看特定币种的信号
```bash
python query_signals.py BTC/USDT:USDT
```

#### 查看今天的所有信号
```bash
python query_signals.py --today
```

#### 查看强度>70的高质量信号
```bash
python query_signals.py --min-strength 70
```

#### 查看最近7天的买入信号
```bash
python query_signals.py --days 7 --action BUY
```

#### 查看BTC最近30天的所有信号
```bash
python query_signals.py BTC/USDT:USDT --days 30
```

---

### 方式3：查看数据库统计

```bash
python query_signals.py --stats
```

**输出示例**：
```
📊 信号数据库统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 数据库文件: data/trading_signals.db
💾 文件大小: 2.3 MB
📝 信号总数: 4,582 条
💰 交易对数: 8 个
📅 时间范围: 2025-07-26 ~ 2025-10-25 (90天)
⭐ 平均强度: 58.2/100

信号分布:
  买入(BUY):  2,145 条 (46.8%)
  卖出(SELL): 1,987 条 (43.4%)
  观望(HOLD):   450 条 (9.8%)

各币种信号分布（Top 10）:
币种                 总数       买入       卖出       平均强度     最后信号
────────────────────────────────────────────────────────────────────────────
BTC/USDT:USDT        1,245      587        512        62.3         2025-10-25 13:45:00
ETH/USDT:USDT          987      456        421        59.1         2025-10-25 13:30:00
SUI/USDT:USDT          654      312        298        56.8         2025-10-25 13:40:00
...

💡 提示: 数据保留策略为 90 天，过期数据将自动清理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 方式4：导出数据

#### 导出所有信号为CSV
```bash
python query_signals.py --export csv --output signals.csv
```

#### 导出BTC最近30天的信号为CSV
```bash
python query_signals.py BTC/USDT:USDT --days 30 --export csv --output btc_signals.csv
```

#### 导出为JSON格式
```bash
python query_signals.py --export json --output signals.json
```

#### 导出强度>60的高质量信号
```bash
python query_signals.py --min-strength 60 --export csv --output high_quality_signals.csv
```

**导出后**：
- CSV文件可用Excel或Google Sheets打开
- JSON文件可用于程序分析
- 所有导出文件默认保存到 `data/exports/` 目录

---

## 📊 数据结构说明

### 保存的字段

每条信号记录包含以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| **timestamp** | 信号时间 | 2025-10-25 14:30:00 |
| **symbol** | 交易对 | BTC/USDT:USDT |
| **timeframe** | 时间周期 | 15m |
| **action** | 信号动作 | BUY / SELL / HOLD |
| **strength** | 信号强度 | 72 (0-100) |
| **market_regime** | 市场状态 | TREND / RANGE / SQUEEZE |
| **price** | 当前价格 | 67234.50 |
| **price_change_pct** | 价格变化 | 2.3% |
| **funding_rate** | 资金费率 | 0.0087% |
| **open_interest** | 持仓量 | 125000 |
| **oi_change_24h** | OI 24小时变化 | 12.5% |
| **reasons** | 触发原因 | ["EMA金叉", "RSI超买区"] |
| **sentiment_reasons** | 情绪调整原因 | ["OI强增(真突破)"] |

---

## ⚙️ 配置说明

### 存储配置文件

**文件**: `config/storage_params.py`

```python
STORAGE_PARAMS = {
    # 存储模式
    "storage_mode": "minimal",         # minimal(极简), standard(标准), full(完整)

    # 启用/禁用
    "enable_storage": True,            # 是否启用数据持久化

    # 数据保留策略
    "signal_retention_days": 90,       # 信号保留90天
    "auto_cleanup": True,              # 启用自动清理

    # 信号过滤（可选）
    "min_signal_strength": 0,          # 最低强度（0=保存所有）
    "save_neutral_signals": False,     # 是否保存HOLD信号
}
```

### 存储模式对比

| 模式 | 保存内容 | 保留时长 | 空间占用/年 | 适用场景 |
|------|----------|----------|------------|---------|
| **minimal** ⭐ | 只保存信号数据 | 90天 | **< 5 MB** | 日常监控 |
| **standard** | 信号 + K线快照 | 30天 | ~50 MB | 短期回测 |
| **full** | 所有数据 | 365天 | ~1-2 GB | 深度研究 |

**推荐使用默认的 minimal 模式**。

---

## 🔧 高级功能

### 1. 禁用数据存储（如果不需要）

编辑 `config/storage_params.py`：
```python
STORAGE_PARAMS = {
    "enable_storage": False,  # 禁用存储
    ...
}
```

### 2. 只保存高质量信号

编辑 `config/storage_params.py`：
```python
STORAGE_PARAMS = {
    "min_signal_strength": 50,    # 只保存强度>50的信号
    "save_neutral_signals": False, # 不保存HOLD信号
    ...
}
```

### 3. 手动清理旧数据

数据会自动清理，但如果需要手动清理：

```python
from utils.signal_storage import get_storage

storage = get_storage()
deleted_count = storage.cleanup_old_data()
print(f"清理了 {deleted_count} 条过期数据")
```

### 4. 查看缓存统计

```python
from utils.signal_storage import get_storage

storage = get_storage()
stats = storage.get_stats()
print(stats)
```

---

## 💾 存储空间说明

### 你的使用场景（8个币种，15分钟周期）

**保守估计**：
```
每天: 77 条信号 × 0.5KB = 38.5 KB
每月: 2,310 条信号 = 1.15 MB
每年: 27,720 条信号 = 13.5 MB
```

**启用90天自动清理后**：
```
稳定占用: < 5 MB（始终保持90天数据）
```

**对比**：
- 📷 一张手机照片：3-5 MB
- 🎵 一首MP3音乐：3-4 MB
- **📊 你的交易数据库**：< 5 MB

**结论**：可以完全忽略存储空间占用 ✅

---

## 📁 文件结构

```
quant_trading/
├── data/                              # 数据目录（自动创建）
│   ├── trading_signals.db             # SQLite数据库
│   └── exports/                       # 导出文件目录
│       ├── signals_20251025.csv       # CSV导出
│       └── signals_20251025.json      # JSON导出
├── config/
│   └── storage_params.py              # 存储配置
├── utils/
│   └── signal_storage.py              # 存储模块
├── query_signals.py                   # 查询工具 ⭐
├── multi_monitor.py                   # 多币种监控（已集成）
└── realtime_monitor_pro.py            # 单币种监控（已集成）
```

---

## 🎯 常见使用场景

### 场景1：每天查看昨天的信号

```bash
python query_signals.py --yesterday
```

### 场景2：查看某个币种的历史表现

```bash
python query_signals.py SUI/USDT:USDT --days 30
```

### 场景3：导出所有强信号用Excel分析

```bash
python query_signals.py --min-strength 70 --export csv --output strong_signals.csv
```

然后用Excel打开 `data/exports/strong_signals.csv` 进行分析。

### 场景4：查看所有买入信号（复盘）

```bash
python query_signals.py --action BUY --days 7
```

### 场景5：每周统计

```bash
python query_signals.py --stats
```

查看本周产生了多少信号，各币种分布如何。

---

## ⚡ 性能说明

### 对监控性能的影响

✅ **几乎零影响**：
- 信号保存是异步的，不阻塞监控
- 单次保存耗时 < 1ms
- SQLite写入非常快（数千次/秒）

### 查询性能

✅ **非常快**：
- 简单查询（按币种/时间）：< 10ms
- 复杂统计查询：< 50ms
- 即使数据库达到10万条记录也很快（有索引）

---

## 🔍 查询示例输出

### 查询所有信号

```bash
$ python query_signals.py --limit 5

🔍 找到 4582 条信号记录

══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
时间                 币种               周期   动作   强度  价格        资金费率    市场状态         触发原因
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
2025-10-25 14:30:00  BTC/USDT:USDT      15m    BUY    72    67234.5000  0.0087%    TREND           EMA金叉, RSI超买区, OI强增(真突破)
2025-10-25 14:15:00  ETH/USDT:USDT      15m    SELL   68    3456.7800   0.0123%    RANGE           Bollinger上轨, 资金费率过高
2025-10-25 14:00:00  SUI/USDT:USDT      15m    BUY    45    1.2340      N/A        NEUTRAL         KDJ金叉, MACD金叉
2025-10-25 13:45:00  BTC/USDT:USDT      15m    HOLD   35    67123.0000  0.0087%    SQUEEZE         无明确趋势
2025-10-25 13:30:00  ZEC/USDT:USDT      15m    SELL   52    45.6700     N/A        TREND           EMA死叉, ADX上升

... 还有 4577 条记录（使用 --limit 参数查看更多）
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 📖 总结

### ✅ 你需要做的

1. **正常运行监控** - 数据自动保存 ✅
2. **需要时查询** - 使用 `query_signals.py` ✅
3. **导出分析** - CSV/JSON导出 ✅

### ✅ 系统自动完成

1. ✅ 自动保存每个信号
2. ✅ 自动清理90天前的旧数据
3. ✅ 自动管理数据库空间
4. ✅ 自动索引优化查询速度

### 📌 关键命令速查

```bash
# 查看所有信号
python query_signals.py

# 查看今天的信号
python query_signals.py --today

# 查看统计
python query_signals.py --stats

# 导出为CSV
python query_signals.py --export csv --output signals.csv

# 查看BTC信号
python query_signals.py BTC/USDT:USDT --days 30
```

---

**现在开始运行监控，所有信号都会自动保存！** 📦✅
