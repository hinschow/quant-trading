# 🎉 混合监控指南（现货+合约同时监控）

## ✨ 重大更新

现在可以**在同一个终端**同时监控现货和合约市场！系统会**自动识别**交易对类型，无需手动指定。

---

## 🚀 快速开始

### 混合监控（推荐）

```bash
# 同时监控现货和合约
python multi_monitor.py BTC/USDT PEPE/USDT:USDT ETH/USDT SOL/USDT:USDT -t 15m --proxy http://127.0.0.1:7890
```

**系统会自动识别**：
- `BTC/USDT` → 现货
- `PEPE/USDT:USDT` → 合约
- `ETH/USDT` → 现货
- `SOL/USDT:USDT` → 合约

**运行效果**：
```
================================================================================
🚀 多币种交易信号监控系统
================================================================================
监控币种: BTC/USDT, PEPE/USDT:USDT, ETH/USDT, SOL/USDT:USDT
市场类型: 现货 2 个, 合约 2 个  ← 自动统计
时间周期: 15m
================================================================================

📥 正在初始化各币种数据...

  BTC/USDT (现货): 获取历史数据... ✅ 完成
  PEPE/USDT:USDT (合约): 获取历史数据... ✅ 完成
  ETH/USDT (现货): 获取历史数据... ✅ 完成
  SOL/USDT:USDT (合约): 获取历史数据... ✅ 完成
```

---

## 📋 交易对格式

**自动识别规则**：

| 格式 | 市场类型 | 示例 |
|------|---------|------|
| `币种/USDT` | 现货 | `BTC/USDT`, `ETH/USDT` |
| `币种/USDT:USDT` | 合约 | `BTC/USDT:USDT`, `PEPE/USDT:USDT` |

⚠️ **关键区别**：合约交易对有 **`:USDT`** 后缀

---

## 💡 使用场景

### 场景1：主流币现货 + 新币合约

```bash
# 主流币用现货（风险低）
# 新币用合约（只在合约市场上线）
python multi_monitor.py \
  BTC/USDT \
  ETH/USDT \
  PEPE/USDT:USDT \
  BONK/USDT:USDT \
  -t 15m --proxy http://127.0.0.1:7890
```

### 场景2：同一币种现货+合约对比

```bash
# 同时监控BTC的现货和合约，对比信号
python multi_monitor.py BTC/USDT BTC/USDT:USDT -t 15m --proxy http://127.0.0.1:7890
```

**用途**：
- 如果现货给 BUY，合约也给 BUY → 强信号
- 如果现货给 BUY，合约给 SELL → 谨慎

### 场景3：纯现货监控

```bash
# 所有交易对都是现货格式（无冒号）
python multi_monitor.py BTC/USDT ETH/USDT SOL/USDT -t 15m --proxy http://127.0.0.1:7890
```

### 场景4：纯合约监控

```bash
# 所有交易对都是合约格式（有 :USDT）
python multi_monitor.py BTC/USDT:USDT PEPE/USDT:USDT WIF/USDT:USDT -t 15m --proxy http://127.0.0.1:7890
```

---

## 🔄 对比旧版本

### ❌ 旧版本（需要手动指定）

```bash
# 现货和合约要分开运行

# 终端1: 现货
python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy ...

# 终端2: 合约（需要加 -m future）
python multi_monitor.py PEPE/USDT:USDT BONK/USDT:USDT -t 15m -m future --proxy ...
```

### ✅ 新版本（自动识别）

```bash
# 一个终端搞定，自动识别市场类型
python multi_monitor.py BTC/USDT PEPE/USDT:USDT ETH/USDT BONK/USDT:USDT -t 15m --proxy ...
```

**优势**：
- ✅ 不需要 `-m` 参数
- ✅ 不需要开多个终端
- ✅ 一个命令监控所有市场
- ✅ 更简单、更方便

---

## 📊 状态显示

运行后每分钟显示所有币种状态：

```
────────────────────────────────────────────────────────────────────────────────
📊 当前状态 (17:30:00)
────────────────────────────────────────────────────────────────────────────────
BTC/USDT     | $ 67,234.50 | 📈 TREND       | 🟢 BUY  | 强度:  60/100
PEPE/USDT:USDT | $  0.00001234 | ↔️ RANGE     | ⚪ HOLD | 强度:   0/100
ETH/USDT     | $  3,456.78 | 🔥 STRONG_TREND | 🟢 BUY  | 强度:  75/100
SOL/USDT:USDT | $   145.23 | 📈 TREND       | 🟢 BUY  | 强度:  65/100
────────────────────────────────────────────────────────────────────────────────
```

**一目了然**：
- 每个币种的当前价格
- 市场状态（趋势/震荡/挤压）
- 买卖信号
- 信号强度

---

## 💾 信号保存

所有信号（现货+合约）保存在同一个文件：

```
signal_logs/signals_20251024.csv
signal_logs/signals_20251024.json
```

在CSV文件中，"交易对"列可以区分：
- `BTC/USDT` - 现货信号
- `PEPE/USDT:USDT` - 合约信号

**分析方法**：
```
打开CSV文件 → 筛选"交易对"列：
- 只看现货：筛选不包含 ":" 的
- 只看合约：筛选包含 ":" 的
```

---

## ⚠️ 注意事项

### 1. 交易对格式要正确

```bash
# ❌ 错误（合约缺少 :USDT）
python multi_monitor.py PEPE/USDT -t 15m --proxy ...
# 系统会当成现货，找不到交易对会报错

# ✅ 正确
python multi_monitor.py PEPE/USDT:USDT -t 15m --proxy ...
```

### 2. 合约风险更高

即使混合监控很方便，也要记住：
- 🚨 合约有杠杆，可能爆仓
- 🚨 资金费率每8小时结算
- 💡 建议：合约用小仓位

### 3. 信号对比使用

当同时监控 `BTC/USDT` 和 `BTC/USDT:USDT` 时：
- 两个都给 BUY → 强信号，可以考虑入场
- 一个 BUY 一个 SELL → 信号冲突，谨慎观望
- 都给 HOLD → 等待更好的机会

---

## 🎯 推荐工作流程

### 每天早上

```bash
cd /Volumes/datedisk/code/quant-trading
source venv/bin/activate

# 启动混合监控
python multi_monitor.py \
  BTC/USDT \
  ETH/USDT \
  PEPE/USDT:USDT \
  BONK/USDT:USDT \
  -t 15m --proxy http://127.0.0.1:7890
```

### 听到信号时

1. 查看终端显示的完整信号
2. 查看是现货还是合约
3. 判断是否入场
4. 设置止盈止损

### 每天晚上

```bash
# 打开信号文件
open signal_logs/signals_YYYYMMDD.csv

# 在Excel中：
# 1. 筛选现货信号（交易对不包含":"）
# 2. 筛选合约信号（交易对包含":"）
# 3. 记录实际操作结果
# 4. 统计成功率
```

---

## 🎊 总结

**混合监控**让你：
- ✅ 一个终端监控所有市场
- ✅ 自动识别现货和合约
- ✅ 不会错过任何机会
- ✅ 操作更简单方便

**使用要点**：
1. 交易对格式：
   - 现货：`BTC/USDT`（无冒号）
   - 合约：`BTC/USDT:USDT`（有 `:USDT`）

2. 无需参数：
   - 不需要 `-m` 参数
   - 系统自动识别

3. 混合监控：
   - 现货和合约可以一起监控
   - 一个命令搞定

试试吧！📈
