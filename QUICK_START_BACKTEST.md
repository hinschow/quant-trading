# 快速开始 - 回测验证

**目标**: 用历史数据快速验证策略的有效性

**预计时间**: 10-15分钟

---

## 🚀 第一步：安装依赖

```bash
cd /home/andre/code/quant-trading

# 安装Python依赖
pip3 install -r requirements.txt
```

**依赖列表**:
- pandas, numpy（数据处理）
- ccxt（交易所API）
- ta-lib（技术指标）
- python-dotenv, pyyaml（配置管理）

---

## 📊 第二步：查看当前配置

```bash
# 查看预设配置方案
python3 config_manager.py --show-presets
```

**当前配置**（均衡型）:
- 止损: 1.5%
- 止盈: 3%
- ADX阈值: 30
- 信号阈值: 30分

---

## 🧪 第三步：运行快速测试

```bash
# 一键测试（推荐）
chmod +x test_backtest.sh
./test_backtest.sh
```

**或者手动测试**:

```bash
# 回测BTC/USDT 1小时周期（500根K线）
python3 backtest_engine.py BTC/USDT -t 1h --limit 500
```

---

## 📈 第四步：查看回测结果

回测完成后，你会看到类似的输出：

```
================================================================================
📊 回测结果
================================================================================

【基本信息】
  初始资金:      $    10,000.00
  最终权益:      $    12,500.00
  总收益:        $     2,500.00 (+25.00%)
  年化收益率:            30.00%
  最大回撤:              -5.50%

【交易统计】
  总交易次数:                15
  盈利次数:                  10
  亏损次数:                   5
  胜率:                  66.67%

【盈亏分析】
  平均盈利:      $      350.00
  平均亏损:      $      150.00
  盈亏比:                2.33:1

【风险指标】
  夏普比率:              2.80

【综合评价】
  综合得分:              85.0/100
  评级:          ⭐⭐⭐⭐⭐ 优秀
```

---

## 🎯 第五步：解读结果

### 关键指标含义

| 指标 | 含义 | 好的标准 | 例子 |
|-----|------|---------|------|
| **总收益率** | 赚了多少 | >15% | 25% ✅ |
| **年化收益率** | 一年能赚多少 | 15-25% | 30% ✅ |
| **最大回撤** | 最大亏损幅度 | ≤8% | -5.5% ✅ |
| **胜率** | 赚钱交易的比例 | ≥55% | 66.67% ✅ |
| **盈亏比** | 盈利/亏损比 | ≥1.8:1 | 2.33:1 ✅ |
| **夏普比率** | 风险调整后收益 | ≥2.5 | 2.80 ✅ |

### 评级标准

- **⭐⭐⭐⭐⭐ (80-100分)**: 优秀，建议实盘
- **⭐⭐⭐⭐ (60-80分)**: 良好，可以实盘
- **⭐⭐⭐ (40-60分)**: 一般，需要优化
- **⭐⭐ (20-40分)**: 较差，调整参数
- **⭐ (0-20分)**: 很差，重新设计

---

## 🔧 第六步：根据结果调整参数

### 场景A: 结果很好（80+分）

**恭喜！策略表现优秀。**

建议：
1. 回测更多币种验证普适性
2. 回测不同时间周期
3. 准备进入模拟交易阶段

```bash
# 回测其他币种
python3 backtest_engine.py ETH/USDT -t 1h
python3 backtest_engine.py BNB/USDT -t 1h
python3 backtest_engine.py SOL/USDT -t 1h
```

### 场景B: 收益不错但回撤大（>10%）

**问题**: 利润可观但风险太高

**解决方案**: 收紧止损
```bash
nano config/strategy_params.py
```

修改：
```python
TREND_FOLLOWING_PARAMS["stop_loss_pct"] = 0.01  # 1.5% → 1%
MEAN_REVERSION_PARAMS["stop_loss_pct"] = 0.01
```

重新回测验证：
```bash
python3 backtest_engine.py BTC/USDT -t 1h --limit 500
```

### 场景C: 交易太少（<5次）

**问题**: 信号太保守，错过很多机会

**解决方案**: 降低信号阈值
```bash
nano config/strategy_params.py
```

修改：
```python
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 28  # 30 → 28
```

或者编辑 `strategy_engine.py`：
```bash
nano strategy_engine.py
```

找到第289行和426行，修改：
```python
if buy_strength >= 25:  # 原来是30
```

### 场景D: 胜率太低（<40%）

**问题**: 假信号太多，频繁止损

**解决方案**: 提高信号质量
```bash
nano config/strategy_params.py
```

修改：
```python
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 35  # 30 → 35
```

或者在 `strategy_engine.py` 中提高阈值：
```python
if buy_strength >= 40:  # 原来是30
```

---

## 📊 第七步：多币种批量回测

创建批量回测脚本：

```bash
nano batch_backtest.sh
```

内容：
```bash
#!/bin/bash
# 批量回测主流币种

echo "开始批量回测..."

for symbol in BTC/USDT ETH/USDT BNB/USDT SOL/USDT ADA/USDT
do
    echo ""
    echo "=================================================="
    echo "回测 $symbol"
    echo "=================================================="
    python3 backtest_engine.py $symbol -t 1h --limit 500
    sleep 2
done

echo ""
echo "✅ 批量回测完成！"
```

运行：
```bash
chmod +x batch_backtest.sh
./batch_backtest.sh
```

---

## 📁 第八步：分析交易记录

回测会自动生成CSV文件：

```bash
# 查看交易记录
cat backtest_trades_BTC_USDT_1h.csv

# 或用Excel/LibreOffice打开
libreoffice backtest_trades_BTC_USDT_1h.csv
```

**CSV字段说明**:
- `type`: BUY（买入）或 SELL（卖出）
- `timestamp`: 交易时间
- `price`: 交易价格
- `profit`: 单笔盈亏（卖出时）
- `profit_pct`: 盈亏百分比
- `signal_strength`: 信号强度

---

## 🎛️ 第九步：尝试不同预设配置

### 保守型配置

```bash
nano config/strategy_params.py
```

修改：
```python
TREND_FOLLOWING_PARAMS["stop_loss_pct"] = 0.01       # 1%
TREND_FOLLOWING_PARAMS["take_profit_pct"] = 0.025    # 2.5%
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 35
```

回测：
```bash
python3 backtest_engine.py BTC/USDT -t 1h --limit 500
```

### 激进型配置

```python
TREND_FOLLOWING_PARAMS["stop_loss_pct"] = 0.02       # 2%
TREND_FOLLOWING_PARAMS["take_profit_pct"] = 0.05     # 5%
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 25
```

---

## 🔍 第十步：实时监控验证

回测满意后，可以用实时监控验证信号：

```bash
# 实时监控BTC（需要代理）
python3 realtime_monitor_pro.py BTC/USDT -t 15m --proxy http://127.0.0.1:7890
```

**观察要点**:
- 信号是否及时
- 止盈止损价格是否合理
- 市场状态识别是否准确

---

## 📝 回测检查清单

完成以下检查，确保策略可靠：

- [ ] BTC/USDT 回测通过（得分≥60）
- [ ] ETH/USDT 回测通过
- [ ] 至少3个币种回测平均得分≥60
- [ ] 最大回撤 ≤ 10%
- [ ] 胜率 ≥ 45%
- [ ] 交易次数适中（5-20次）
- [ ] 实时监控信号正常

---

## 🚦 下一步行动

### ✅ 如果回测通过

1. 回测更多币种（10+个）
2. 回测不同时间周期（1h, 4h, 1d）
3. 回测不同市场阶段（牛市、熊市、震荡）
4. 准备实现模拟交易功能

### ⚠️ 如果回测不理想

1. 分析失败交易的共同特征
2. 调整参数配置
3. 考虑简化策略（关闭某些指标）
4. 重新回测验证

---

## 💡 常见问题

### Q: 回测结果波动很大怎么办？

**A**: 可能是数据量太少或市场环境特殊。建议：
- 增加数据量：`--limit 2000`
- 回测多个时间段
- 回测多个币种取平均

### Q: 如何知道参数是否过拟合？

**A**:
1. 回测多个币种，看是否普遍有效
2. 回测不同时间段，看是否稳定
3. 不要过度优化参数

### Q: 止损太频繁怎么办？

**A**:
1. 放宽止损：`stop_loss_pct = 0.02`
2. 提高信号质量：增加 `adx_trend_threshold`
3. 增加信号确认：提高信号阈值

### Q: 信号太少怎么办？

**A**:
1. 降低ADX阈值：`adx_trend_threshold = 25`
2. 降低信号阈值：修改 `strategy_engine.py`
3. 扩大RSI范围：`rsi_oversold = 30`

---

## 📚 参考文档

- **参数详细说明**: [`PARAMETER_GUIDE.md`](PARAMETER_GUIDE.md)
- **项目实施状态**: [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md)
- **项目总体说明**: [`README.md`](README.md)

---

## 🎯 成功标准

回测达到以下标准，可以进入下一阶段：

| 指标 | 最低标准 | 理想标准 |
|-----|---------|---------|
| 综合得分 | ≥60 | ≥80 |
| 年化收益率 | ≥15% | ≥25% |
| 最大回撤 | ≤10% | ≤8% |
| 胜率 | ≥45% | ≥55% |
| 盈亏比 | ≥1.5:1 | ≥1.8:1 |
| 夏普比率 | ≥2.0 | ≥2.5 |

---

**祝您回测顺利！** 🚀

如有问题，请查看文档或调整参数后重新测试。
