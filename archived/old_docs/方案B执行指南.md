# 方案B执行指南 - 快速开始

## 📋 前提条件

确保你已经完成方案A的30m回测，并且结果保存在：
```
backtest_results/multi_timeframe/30m/
```

## 🚀 执行步骤

### 步骤1：备份方案A结果

```bash
cd ~/quant-trading

# 创建方案A备份目录
mkdir -p backtest_results/plan_a_30m

# 备份方案A的回测结果
cp backtest_results/multi_timeframe/30m/*.csv backtest_results/plan_a_30m/
cp backtest_results/multi_timeframe/30m/metadata.json backtest_results/plan_a_30m/

# 确认备份成功
ls -lh backtest_results/plan_a_30m/
```

### 步骤2：验证方案B配置

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行验证脚本
python3 verify_plan_b.py
```

**预期输出**：
```
✅✅ 方案B配置完全正确！可以开始回测。
```

如果有错误，请检查：
- [config/strategy_params.py](config/strategy_params.py:188)
- [strategy_engine.py](strategy_engine.py:522)

### 步骤3：执行方案B回测

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 执行30m周期回测（只测试30m，因为方案A已证明30m最优）
python run_multi_timeframe_backtest.py
```

**预计执行时间**：5-10分钟

### 步骤4：查看回测结果

```bash
# 查看30m回测结果
ls -lh backtest_results/multi_timeframe/30m/

# 快速查看各品种收益
grep "SELL" backtest_results/multi_timeframe/30m/backtest_trades_BTC_USDT_30m.csv | tail -1
grep "SELL" backtest_results/multi_timeframe/30m/backtest_trades_ETH_USDT_30m.csv | tail -1
grep "SELL" backtest_results/multi_timeframe/30m/backtest_trades_SOL_USDT_30m.csv | tail -1
```

### 步骤5：对比方案A和方案B

```bash
# 运行对比分析脚本
python3 compare_plan_a_vs_b.py
```

**预期看到**：
- 各品种收益对比
- 交易次数变化
- 胜率和盈亏比变化
- 是否达到预期目标

### 步骤6：提交结果到服务器

```bash
# 查看修改
git status

# 添加所有修改
git add .

# 提交
git commit -m "方案B回测完成：BTC/ETH微调 + 量价背离过滤

- BTC: min_signal_strength 65→60, adx_threshold 35→30
- ETH: adx_threshold 35→30
- SOL: 参数保持不变
- 新增量价背离过滤逻辑
- 回测结果: [在此填写总收益]"

# 推送到远程
git push
```

## 📊 关键指标检查清单

### 交易次数变化
- [ ] BTC: 从3笔增加到5-8笔？
- [ ] ETH: 保持5笔左右？
- [ ] SOL: 保持5笔？

### 收益率改善
- [ ] BTC: 从-3.47%改善？
- [ ] ETH: 从-0.76%改善到正收益？
- [ ] SOL: 保持+1.15%左右？
- [ ] **总收益: 从-3.09%改善到0%以上？** ✨

### 量价背离过滤效果
检查CSV文件中被过滤的信号：

```bash
# 方案A有多少笔交易包含"量价背离"警告
cd backtest_results/plan_a_30m
grep "量价背离" *.csv | wc -l

# 方案B有多少笔（应该更少）
cd ../../multi_timeframe/30m
grep "量价背离" *.csv | wc -l
```

### 信号强度分布

```bash
# 查看各品种的信号强度（应该都满足阈值）
# BTC: ≥60（无背离）或 ≥75（有背离）
grep "BUY" backtest_trades_BTC_USDT_30m.csv | cut -d',' -f7 | sort -n

# ETH: ≥65（无背离）或 ≥75（有背离）
grep "BUY" backtest_trades_ETH_USDT_30m.csv | cut -d',' -f7 | sort -n

# SOL: ≥60（无背离）或 ≥80（有背离）
grep "BUY" backtest_trades_SOL_USDT_30m.csv | cut -d',' -f7 | sort -n
```

## 🎯 预期目标（vs 方案A）

| 指标 | 方案A | 方案B目标 | 判断标准 |
|------|------|----------|---------|
| BTC收益 | -3.47% | -1% ~ 0% | 改善 >2% |
| ETH收益 | -0.76% | 0% ~ +2% | 实现盈利 |
| SOL收益 | +1.15% | +1% ~ +3% | 保持盈利 |
| **总收益** | **-3.09%** | **0% ~ +2%** | **实现盈利** ✅ |
| BTC交易数 | 3笔 | 5-8笔 | 增加机会 |
| ETH交易数 | 5笔 | 4-6笔 | 保持/略减 |
| SOL交易数 | 5笔 | 5笔 | 保持不变 |

## ⚠️ 常见问题

### Q1: 验证脚本报错怎么办？
A: 检查以下文件是否正确修改：
- `config/strategy_params.py` - 参数配置
- `strategy_engine.py` - 量价背离过滤逻辑

参考 [方案B优化说明.md](方案B优化说明.md) 中的代码示例。

### Q2: 回测结果不如预期怎么办？
A:
1. 确认参数配置正确（运行 `verify_plan_b.py`）
2. 检查是否在30m周期测试（方案A证明30m最优）
3. 查看详细交易记录，分析哪些交易被过滤
4. 如果总收益仍为负，考虑：
   - 进一步提高量价背离阈值
   - 专注SOL单品种交易
   - 延长测试周期到90天

### Q3: 如何判断量价背离过滤是否生效？
A:
```bash
# 查看方案A中有量价背离的交易
cd backtest_results/plan_a_30m
grep "量价背离" *.csv

# 查看方案B中（应该减少）
cd ../../multi_timeframe/30m
grep "量价背离" *.csv

# 对比交易数量变化
```

### Q4: 回测太慢怎么办？
A:
- 30m周期回测60天数据，预计5-10分钟
- 如果超过20分钟，检查网络连接（需要从Binance拉取数据）
- 可以先测试单个品种：修改 `run_multi_timeframe_backtest.py` 中的 `symbols` 列表

## 📚 相关文档

- [方案B优化说明.md](方案B优化说明.md) - 详细的优化逻辑和代码修改
- [方案A多周期回测结果分析.md](方案A多周期回测结果分析.md) - 方案B的优化基础
- [config/strategy_params.py](config/strategy_params.py:237) - 方案B参数配置说明

## 🎉 成功标准

方案B被认为成功当且仅当：

1. ✅ **总收益 ≥ 0%**（实现盈利）
2. ✅ 至少2个品种盈利（当前SOL已盈利，需要BTC或ETH之一盈利）
3. ✅ 盈亏比改善（至少1个品种 >1）
4. ✅ 交易频率合理（总计12-16笔）

如果达到以上标准，可以考虑：
- 延长测试周期到90天验证稳定性
- 开始小资金实盘测试（建议SOL/USDT）
- 进一步优化仓位分配

---

**版本**: v5.0 (方案B)
**更新时间**: 2025-10-28
**适用周期**: 30m（已验证最优）
**预期总收益**: 0% ~ +2% ✨
