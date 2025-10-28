# 策略参数配置指南

## 📋 目录

1. [参数配置概览](#参数配置概览)
2. [市场状态识别参数](#市场状态识别参数)
3. [趋势跟踪策略参数](#趋势跟踪策略参数)
4. [均值回归策略参数](#均值回归策略参数)
5. [市场情绪参数](#市场情绪参数)
6. [参数调整建议](#参数调整建议)
7. [回测优化参数](#回测优化参数)

---

## 参数配置概览

所有策略参数都集中在 `config/strategy_params.py` 文件中，采用Python字典格式，方便修改和调整。

**配置文件位置**: [`config/strategy_params.py`](config/strategy_params.py)

**当前版本**: v3.2（基于 v3.1 + BOLL 增强）

---

## 市场状态识别参数

### `MARKET_REGIME_PARAMS`

用于识别当前市场处于哪种状态（强趋势、趋势、震荡、挤压、中性）。

```python
MARKET_REGIME_PARAMS = {
    # ADX 参数（平均趋向指数）
    "adx_period": 14,                # ADX 计算周期
    "adx_trend_threshold": 30,       # ADX > 30 = 强趋势
    "adx_weak_trend_threshold": 25,  # ADX > 25 = 一般趋势
    "adx_range_threshold": 18,       # ADX < 18 = 震荡市

    # 布林带宽度（BBW）参数
    "bbw_period": 20,                # BBW 计算周期
    "bbw_ma_period": 20,             # BBW 均值周期
    "bbw_high_threshold": 1.2,       # BBW > 1.2 = 高波动
    "bbw_normal_threshold": 1.0,     # BBW > 1.0 = 正常波动
    "bbw_low_threshold": 0.8,        # BBW < 0.8 = 低波动
    "bbw_squeeze_threshold": 0.5,    # BBW < 0.5 = 挤压状态
}
```

### 市场状态分类逻辑

| 市场状态 | ADX条件 | BBW条件 | 使用策略 | 建议仓位 |
|---------|---------|---------|---------|---------|
| **STRONG_TREND** | ADX > 30 | BBW > 1.2 | 趋势跟踪 | 100% |
| **TREND** | ADX > 25 | BBW > BBW_MA | 趋势跟踪 | 80% |
| **RANGE** | ADX < 18 | BBW < BBW_MA | 均值回归 | 60% |
| **SQUEEZE** | - | BBW < 0.5 | 突破等待 | 30% |
| **NEUTRAL** | 其他 | 其他 | 观望 | 0% |

**调整建议**:
- 如果信号太少 → 降低 `adx_trend_threshold` (30 → 28)
- 如果假信号太多 → 提高 `adx_trend_threshold` (30 → 32)
- 震荡市检测太敏感 → 降低 `adx_range_threshold` (18 → 15)

---

## 趋势跟踪策略参数

### `TREND_FOLLOWING_PARAMS`

用于趋势市场（STRONG_TREND 和 TREND 状态）。

```python
TREND_FOLLOWING_PARAMS = {
    # EMA 参数（指数移动平均线）
    "ema_fast": 50,                  # 快速 EMA 周期
    "ema_slow": 200,                 # 慢速 EMA 周期

    # MACD 参数
    "macd_fast": 12,                 # MACD 快线
    "macd_slow": 26,                 # MACD 慢线
    "macd_signal": 9,                # MACD 信号线

    # ADX 参数
    "adx_period": 14,                # ADX 周期
    "adx_threshold": 30,             # ADX 确认阈值

    # 成交量确认
    "volume_ma_period": 20,          # 成交量均线周期
    "volume_multiplier": 1.3,        # 成交量倍数（确认突破）

    # 布林带参数
    "bb_period": 20,                 # 布林带周期
    "bb_std": 2.0,                   # 标准差倍数

    # 止盈止损
    "stop_loss_pct": 0.015,          # 1.5% 止损
    "take_profit_pct": 0.03,         # 3% 止盈
    "trailing_stop_trigger": 0.02,   # 盈利 2% 启动移动止损
    "trailing_stop_pct": 0.0,        # 移动到成本价（保本）

    # 时间止损
    "max_holding_hours": 72,         # 最长持仓 72 小时
}
```

### 信号强度计算逻辑

**买入信号**（总分100）:
- EMA金叉（50上穿200）: **+50分**
- 处于上升趋势（EMA50 > EMA200）: **+20分**
- 价格高于EMA200超过5%: **+10分**
- EMA向上发散（EMA50比EMA200高3%）: **+10分**
- MACD金叉: **+40分**
- MACD多头排列: **+15分**
- RSI健康（40-80）: **+15分**
- RSI强劲（>70且在上涨）: **+10分**
- OBV上升确认: **+15分**
- ADX>25（趋势明确）: **+10分**
- ADX>40（极强趋势）: **+5分**

**信号阈值**: 总分 ≥ 30 才发出买入信号

**调整建议**:
- 如果信号太频繁 → 提高阈值 (30 → 40)
- 如果错过很多机会 → 降低阈值 (30 → 25)
- 止损太紧 → 提高 `stop_loss_pct` (0.015 → 0.02)
- 止盈太远 → 降低 `take_profit_pct` (0.03 → 0.025)

---

## 均值回归策略参数

### `MEAN_REVERSION_PARAMS`

用于震荡市场（RANGE 状态）。

```python
MEAN_REVERSION_PARAMS = {
    # RSI 参数（相对强弱指标）
    "rsi_period": 14,                # RSI 周期
    "rsi_oversold": 25,              # RSI < 25 = 超卖
    "rsi_overbought": 75,            # RSI > 75 = 超买
    "rsi_neutral": 50,               # RSI 中性值

    # KDJ 参数（震荡市场专用）
    "kdj_fastk_period": 9,           # RSV周期
    "kdj_slowk_period": 3,           # K值平滑周期
    "kdj_slowd_period": 3,           # D值平滑周期
    "kdj_oversold": 20,              # KDJ < 20 = 超卖
    "kdj_overbought": 80,            # KDJ > 80 = 超买
    "kdj_enabled": True,             # 是否启用KDJ指标

    # 布林带参数
    "bb_period": 20,                 # 布林带周期
    "bb_std": 2.5,                   # 2.5倍标准差（更保守）

    # ATR 波动率过滤
    "atr_period": 14,                # ATR 周期
    "atr_ma_period": 50,             # ATR 均值周期
    "atr_multiplier": 1.5,           # ATR > 均值×1.5 暂停入场

    # ADX 过滤
    "adx_period": 14,                # ADX 周期
    "adx_max_threshold": 25,         # ADX < 25 才做均值回归

    # 止盈止损
    "stop_loss_pct": 0.015,          # 1.5% 止损
    "take_profit_type": "bb_middle", # 止盈方式：bb_middle 或 rsi_neutral

    # 时间止损
    "max_holding_hours": 24,         # 最长持仓 24 小时
}
```

### 信号强度计算逻辑

**买入信号**（总分100）:
- RSI偏低（<35）: **(35-RSI)×2 分** (最多20分)
- 价格接近布林下轨（<30%位置）: **(0.3-位置)×100 分** (最多30分)
- KDJ超卖区（K<20, D<20）: **+15分**
- KDJ金叉（K上穿D）: **+20分**

**信号阈值**: 总分 ≥ 30 才发出买入信号

**调整建议**:
- RSI阈值太严格 → 提高 `rsi_oversold` (25 → 30)
- 布林带太保守 → 降低 `bb_std` (2.5 → 2.0)
- 关闭KDJ → 设置 `kdj_enabled: False`

---

## 市场情绪参数

### `SENTIMENT_PARAMS`

整合资金费率和持仓量（OI）数据，动态调整信号强度。

```python
SENTIMENT_PARAMS = {
    # 资金费率参数
    "funding_rate_enabled": True,    # 是否启用资金费率
    "funding_rate_extreme_long": 0.1,    # 0.1% = 极度看多（顶部风险）
    "funding_rate_bullish": 0.05,        # 0.05% = 偏多
    "funding_rate_extreme_short": -0.05, # -0.05% = 极度看空（底部信号）
    "funding_rate_bearish": -0.02,       # -0.02% = 偏空

    # 持仓量（OI）参数
    "open_interest_enabled": True,   # 是否启用持仓量
    "oi_increase_threshold": 10,     # OI增加 10% = 新资金进场
    "oi_decrease_threshold": -5,     # OI减少 -5% = 资金流出
    "oi_strong_increase": 15,        # OI增加 15% = 强力确认
    "oi_strong_decrease": -15,       # OI减少 -15% = 强力下跌
}
```

### 情绪调整逻辑

**买入信号调整**:
- 资金费率极度负值（<-0.05%）→ **+15分** （底部信号）
- 资金费率偏空（<-0.02%）→ **+10分**
- 资金费率过高（>0.1%）→ **-20分** （顶部风险）
- OI强增加（>15%）→ **+20分** （真突破）
- OI增加（>10%）→ **+10分**
- OI下降（<-5%）→ **-15分** （假突破）

**调整建议**:
- 暂时关闭情绪分析 → 设置 `funding_rate_enabled: False` 和 `open_interest_enabled: False`
- 调整阈值以适应不同市场环境

---

## 量价分析参数

### `VOLUME_PARAMS`

```python
VOLUME_PARAMS = {
    # OBV 参数（能量潮）
    "obv_enabled": True,             # 是否启用OBV
    "obv_ma_period": 20,             # OBV移动平均周期
    "obv_divergence_threshold": 5,   # 量价背离阈值（%）

    # VWAP 参数（成交量加权平均价）
    "vwap_enabled": True,            # 是否启用VWAP
    "vwap_deviation_threshold": 0.02,# VWAP偏离阈值（2%）
}
```

---

## 参数调整建议

### 🎯 快速调整指南

#### 1. 信号太少 / 错过机会

```python
# 降低进场阈值
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 28  # 30 → 28
MEAN_REVERSION_PARAMS["rsi_oversold"] = 30  # 25 → 30
```

#### 2. 假信号太多 / 频繁止损

```python
# 提高进场阈值
MARKET_REGIME_PARAMS["adx_trend_threshold"] = 32  # 30 → 32
TREND_FOLLOWING_PARAMS["stop_loss_pct"] = 0.02  # 0.015 → 0.02

# 或在 strategy_engine.py 中提高信号强度阈值
# 第289行: if buy_strength >= 40:  # 原来是30
```

#### 3. 止损太频繁

```python
# 放宽止损
TREND_FOLLOWING_PARAMS["stop_loss_pct"] = 0.02  # 1.5% → 2%
MEAN_REVERSION_PARAMS["stop_loss_pct"] = 0.02
```

#### 4. 止盈太早 / 利润太少

```python
# 提高止盈目标
TREND_FOLLOWING_PARAMS["take_profit_pct"] = 0.05  # 3% → 5%
```

#### 5. 关闭某些指标（简化策略）

```python
# 关闭KDJ
MEAN_REVERSION_PARAMS["kdj_enabled"] = False

# 关闭OBV
VOLUME_PARAMS["obv_enabled"] = False

# 关闭市场情绪
SENTIMENT_PARAMS["funding_rate_enabled"] = False
SENTIMENT_PARAMS["open_interest_enabled"] = False
```

---

## 回测优化参数

### `OPTIMIZATION_RANGES`

用于参数优化时的搜索范围。

```python
OPTIMIZATION_RANGES = {
    "trend_following": {
        "ema_fast": [20, 30, 40, 50, 60],
        "ema_slow": [150, 180, 200, 220],
        "adx_threshold": [25, 28, 30, 32],
        "stop_loss_pct": [0.01, 0.015, 0.02],
        "take_profit_pct": [0.025, 0.03, 0.035],
    },
    "mean_reversion": {
        "rsi_oversold": [20, 25, 30],
        "rsi_overbought": [70, 75, 80],
        "bb_std": [2.0, 2.5, 3.0],
        "stop_loss_pct": [0.01, 0.015, 0.02],
    }
}
```

**用途**: 回测系统会遍历这些参数组合，找出最优配置。

---

## 📊 参数配置总结

### 当前参数特点

1. **保守稳健**: 止损1.5%，止盈3%，风险回报比1:2
2. **多指标确认**: 整合趋势、震荡、量价、情绪多维度
3. **自适应**: 根据市场状态自动切换策略
4. **可扩展**: 所有参数都在配置文件中，方便调整

### 推荐配置方案

#### 激进型（追求高收益）
- `stop_loss_pct`: 0.02 (2%)
- `take_profit_pct`: 0.05 (5%)
- 信号阈值: 25分
- `adx_trend_threshold`: 25

#### 保守型（追求稳定）
- `stop_loss_pct`: 0.01 (1%)
- `take_profit_pct`: 0.025 (2.5%)
- 信号阈值: 40分
- `adx_trend_threshold`: 35

#### 当前配置（均衡型）✅
- `stop_loss_pct`: 0.015 (1.5%)
- `take_profit_pct`: 0.03 (3%)
- 信号阈值: 30分
- `adx_trend_threshold`: 30

---

## 🔧 如何修改参数

1. **编辑配置文件**
   ```bash
   nano config/strategy_params.py
   ```

2. **修改参数值**（Python字典格式）
   ```python
   TREND_FOLLOWING_PARAMS = {
       "stop_loss_pct": 0.02,  # 修改这里
       # ...
   }
   ```

3. **保存并重启程序**
   - 无需重启整个系统
   - 只需重新运行策略引擎

4. **验证修改**
   ```bash
   python signal_analyzer.py BTC/USDT -t 1h
   ```

---

## 📝 注意事项

1. **修改前备份**: 复制一份原始配置以便恢复
2. **小幅调整**: 每次只调整一个参数，观察效果
3. **回测验证**: 修改后务必先回测，再实盘
4. **记录结果**: 记录每次修改和对应的回测结果

---

**更新时间**: 2025-10-27
**版本**: v3.2
**维护者**: Claude + 用户
