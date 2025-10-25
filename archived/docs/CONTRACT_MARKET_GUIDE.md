# 📈 合约市场监控指南

## 🎯 什么是合约市场？

很多新币、小币**只在合约市场（永续合约/期货）上线**，现货市场没有。使用合约市场监控功能，你可以：

- ✅ 监控只在合约市场的币种（如 PEPE、BONK等）
- ✅ 使用杠杆交易（1x-125x）
- ✅ 做多或做空
- ✅ 同时监控现货和合约市场

---

## 🔄 现货 vs 合约市场

| 特性 | 现货市场 | 合约市场 |
|------|---------|---------|
| **交易对格式** | `BTC/USDT` | `BTC/USDT:USDT` |
| **币种数量** | 较少 | 更多（包括新币） |
| **杠杆** | 无 | 1x-125x |
| **做空** | ❌ 不支持 | ✅ 支持 |
| **资金费率** | 无 | 有（8小时收一次） |
| **风险** | 低 | 高（可以爆仓） |

---

## 🚀 快速开始

### 监控合约市场的币种

```bash
# 单个币种监控（合约市场）
python realtime_monitor_pro.py BTC/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890

# 只在合约市场的新币
python realtime_monitor_pro.py PEPE/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890

# 多币种监控（合约市场）
python multi_monitor.py BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT -t 1h -m future --proxy http://127.0.0.1:7890
```

### 同时监控现货和合约

```bash
# 终端1: 现货市场
python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy http://127.0.0.1:7890

# 终端2: 合约市场
python multi_monitor.py BTC/USDT:USDT PEPE/USDT:USDT BONK/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
```

---

## 📋 交易对格式说明

### ⚠️ 非常重要：交易对格式

**现货市场**：
```
BTC/USDT
ETH/USDT
SOL/USDT
```

**合约市场**（注意有 `:USDT` 后缀）：
```
BTC/USDT:USDT
ETH/USDT:USDT
PEPE/USDT:USDT
BONK/USDT:USDT
```

### 如何查找合约交易对？

1. 打开币安合约交易页面
2. 搜索你想监控的币种
3. 如果显示"永续合约"，说明该币有合约市场
4. 使用格式：`币种/USDT:USDT`

**示例**：
- 币安显示：`PEPE 永续合约`
- 监控格式：`PEPE/USDT:USDT`

---

## 💡 使用示例

### 示例1：监控只在合约市场的新币

某些新币只在合约市场，现货没有：

```bash
# PEPE 只在合约市场
python realtime_monitor_pro.py PEPE/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890

# BONK 只在合约市场
python realtime_monitor_pro.py BONK/USDT:USDT -t 1h -m future --proxy http://127.0.0.1:7890
```

### 示例2：多个合约币种监控

```bash
python multi_monitor.py \
  PEPE/USDT:USDT \
  BONK/USDT:USDT \
  WIF/USDT:USDT \
  -t 15m -m future --proxy http://127.0.0.1:7890
```

运行效果：
```
================================================================================
🚀 多币种交易信号监控系统
================================================================================
监控币种: PEPE/USDT:USDT, BONK/USDT:USDT, WIF/USDT:USDT
市场类型: 合约/永续 (future)
时间周期: 15m
交易所: binance
================================================================================
```

### 示例3：同时监控现货和合约

```bash
# 监控BTC的现货和合约
python multi_monitor.py BTC/USDT BTC/USDT:USDT -t 15m --proxy http://127.0.0.1:7890
```

⚠️ **注意**：这会尝试用现货API获取合约数据，会出错。应该分开运行：

```bash
# 正确做法：两个终端分别运行

# 终端1: 现货
python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy http://127.0.0.1:7890

# 终端2: 合约（注意加 -m future）
python multi_monitor.py BTC/USDT:USDT ETH/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
```

---

## ⚠️ 重要注意事项

### 1. 必须指定 `-m future` 参数

监控合约市场时，**必须**加上 `-m future` 参数：

```bash
# ❌ 错误（会尝试用现货API）
python multi_monitor.py PEPE/USDT:USDT -t 15m --proxy http://127.0.0.1:7890

# ✅ 正确
python multi_monitor.py PEPE/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
```

### 2. 交易对格式必须正确

合约市场的交易对**必须**有 `:USDT` 后缀：

```bash
# ❌ 错误
PEPE/USDT

# ✅ 正确
PEPE/USDT:USDT
```

### 3. 合约交易风险更高

- 🚨 可以使用杠杆（1x-125x），风险极高
- 🚨 价格波动大，可能爆仓
- 🚨 有资金费率（每8小时结算一次）
- 💡 建议：信号给出买卖建议，但**只做参考**
- 💡 建议：使用**小杠杆**（1x-3x）或不用杠杆

### 4. 信号保存文件统一

无论现货还是合约，所有信号都保存到同一个文件：
```
signal_logs/signals_20251024.csv
signal_logs/signals_20251024.json
```

在CSV文件的"交易对"列可以区分：
- `BTC/USDT` - 现货
- `BTC/USDT:USDT` - 合约

---

## 📊 查看可用的合约交易对

### 方法1：通过币安官网

1. 访问 https://www.binance.com/zh-CN/futures/BTC_USDT
2. 点击交易对选择器
3. 查看所有可用的永续合约
4. 格式转换：`PEPE 永续合约` → `PEPE/USDT:USDT`

### 方法2：通过Python代码

创建一个脚本 `list_futures.py`：

```python
import ccxt

exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'proxies': {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }
})

markets = exchange.load_markets()
futures = [symbol for symbol in markets if ':USDT' in symbol]

print("可用的永续合约交易对：")
for symbol in sorted(futures):
    print(f"  {symbol}")
```

运行：
```bash
python list_futures.py
```

---

## 🎯 推荐工作流程

### 新手推荐

1. **先从现货开始**
   ```bash
   python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy http://127.0.0.1:7890
   ```

2. **熟悉后，再监控合约市场**
   ```bash
   python multi_monitor.py BTC/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
   ```

3. **不要一开始就用合约交易**
   - 先用现货练习几个月
   - 熟悉信号准确率
   - 建立信心后再考虑合约

### 进阶用法

同时监控多个市场，寻找套利机会：

```bash
# 终端1: 现货BTC
python realtime_monitor_pro.py BTC/USDT -t 15m --proxy http://127.0.0.1:7890

# 终端2: 合约BTC
python realtime_monitor_pro.py BTC/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
```

对比两个市场的信号差异：
- 如果现货给 BUY 信号，合约也给 BUY → 强信号
- 如果现货给 BUY 信号，合约给 SELL → 谨慎

---

## 🛠️ 故障排查

### 问题1：找不到交易对

```
❌ 错误: binance does not have market symbol PEPE/USDT
```

**原因**：该币只在合约市场
**解决**：
1. 改用合约格式：`PEPE/USDT:USDT`
2. 添加 `-m future` 参数

```bash
# 正确用法
python multi_monitor.py PEPE/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
```

### 问题2：API错误 (fapi)

```
❌ 错误: GET https://fapi.binance.com/fapi/v1/exchangeInfo
```

**原因**：使用了合约交易对 `BTC/USDT:USDT` 但没加 `-m future`
**解决**：添加 `-m future` 参数

### 问题3：不知道币种是否在合约市场

**解决方法**：
1. 访问币安合约页面搜索
2. 或者两种都试试：
   ```bash
   # 试试现货
   python realtime_monitor_pro.py XXX/USDT -t 15m --proxy http://127.0.0.1:7890

   # 如果报错，试试合约
   python realtime_monitor_pro.py XXX/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890
   ```

---

## 📋 命令对照表

| 目的 | 命令 |
|------|------|
| 监控现货BTC | `python multi_monitor.py BTC/USDT -t 15m --proxy ...` |
| 监控合约BTC | `python multi_monitor.py BTC/USDT:USDT -t 15m -m future --proxy ...` |
| 监控现货新币 | `python multi_monitor.py PEPE/USDT -t 15m --proxy ...` |
| 监控合约新币 | `python multi_monitor.py PEPE/USDT:USDT -t 15m -m future --proxy ...` |
| 多个现货币种 | `python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy ...` |
| 多个合约币种 | `python multi_monitor.py BTC/USDT:USDT ETH/USDT:USDT -t 15m -m future --proxy ...` |

---

## 🎊 总结

**合约市场监控**让你可以：
- ✅ 监控只在合约市场的新币
- ✅ 捕捉更多交易机会
- ✅ 做多或做空
- ✅ 自动保存所有信号

**使用要点**：
1. 交易对格式：`币种/USDT:USDT`（注意 `:USDT` 后缀）
2. 必须添加：`-m future` 参数
3. 风险更高：建议小仓位、低杠杆
4. 严格止损：合约市场波动大，严格执行止损

**推荐**：
- 新手先从现货开始
- 熟悉系统后再尝试合约
- 记录每笔交易结果
- 持续优化策略

祝交易顺利！📈
