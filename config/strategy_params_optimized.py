"""
策略参数配置 - 优化版 v4.0
基于回测分析优化：提高信号质量、改进止损策略、优化风险管理

优化重点：
1. 提高入场信号强度阈值（减少低质量交易）
2. 放宽止损空间（避免震荡市频繁止损）
3. 改进盈亏比设置（提高take_profit）
4. 增强趋势过滤条件
5. 针对不同品种设置差异化参数
"""

# ==================== 市场状态识别参数（优化）====================
MARKET_REGIME_PARAMS = {
    # ADX 参数 - 提高阈值，只在强趋势时交易
    "adx_period": 14,
    "adx_trend_threshold": 35,        # 提高至35（原30），只在强趋势交易
    "adx_weak_trend_threshold": 28,   # 提高至28（原25）
    "adx_range_threshold": 20,        # 提高至20（原18），避免伪趋势

    # 布林带宽度（BBW）参数
    "bbw_period": 20,
    "bbw_ma_period": 20,
    "bbw_high_threshold": 1.2,
    "bbw_normal_threshold": 1.0,
    "bbw_low_threshold": 0.8,
    "bbw_squeeze_threshold": 0.5,
}

# 市场状态与策略映射（优化仓位管理）
MARKET_REGIME_STRATEGY = {
    "STRONG_TREND": {
        "strategy": "trend_following",
        "position_multiplier": 1.0,    # 100% 仓位（仅在极强趋势）
        "aggressive": True,
    },
    "TREND": {
        "strategy": "trend_following",
        "position_multiplier": 0.7,    # 降至70%（原80%），更保守
        "aggressive": False,
    },
    "RANGE": {
        "strategy": "mean_reversion",
        "position_multiplier": 0.4,    # 降至40%（原60%），震荡市减仓
    },
    "SQUEEZE": {
        "strategy": "breakout",
        "position_multiplier": 0.2,    # 降至20%（原30%），更谨慎
    },
    "NEUTRAL": {
        "strategy": None,
        "position_multiplier": 0.0,    # 空仓观望
    }
}

# ==================== 趋势跟踪策略参数（优化）====================
TREND_FOLLOWING_PARAMS = {
    # EMA 参数
    "ema_fast": 50,
    "ema_slow": 200,

    # MACD 参数
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,

    # ADX 参数 - 提高阈值
    "adx_period": 14,
    "adx_threshold": 35,              # 提高至35（原30）

    # 成交量确认 - 加强过滤
    "volume_ma_period": 20,
    "volume_multiplier": 1.5,         # 提高至1.5（原1.3），要求更强成交量

    # 布林带参数
    "bb_period": 20,
    "bb_std": 2.0,

    # 止盈止损（关键优化）
    "stop_loss_pct": 0.035,           # 放宽至3.5%（原2.5%），避免震荡止损
    "take_profit_pct": 0.07,          # 提高至7%（原5%），提升盈亏比
    "trailing_stop_trigger": 0.04,    # 盈利4%后启动移动止损（原3%）
    "trailing_stop_pct": 0.015,       # 移动止损保留1.5%利润（原1%）

    # 时间止损
    "max_holding_hours": 96,          # 延长至96小时（原72），给趋势更多时间
}

# ==================== 均值回归策略参数（优化）====================
MEAN_REVERSION_PARAMS = {
    # RSI 参数 - 更极端的超买超卖
    "rsi_period": 14,
    "rsi_oversold": 20,               # 降至20（原25），更极端
    "rsi_overbought": 80,             # 提高至80（原75），更极端
    "rsi_neutral": 50,

    # KDJ 参数
    "kdj_fastk_period": 9,
    "kdj_slowk_period": 3,
    "kdj_slowd_period": 3,
    "kdj_oversold": 15,               # 降至15（原20），更极端
    "kdj_overbought": 85,             # 提高至85（原80），更极端
    "kdj_enabled": True,

    # 布林带参数
    "bb_period": 20,
    "bb_std": 2.5,

    # ATR 波动率过滤
    "atr_period": 14,
    "atr_ma_period": 50,
    "atr_multiplier": 1.5,

    # ADX 过滤
    "adx_period": 14,
    "adx_max_threshold": 25,

    # 止盈止损
    "stop_loss_pct": 0.02,            # 放宽至2%（原1.5%）
    "take_profit_type": "bb_middle",

    # 时间止损
    "max_holding_hours": 24,
}

# ==================== 突破策略参数 ====================
BREAKOUT_PARAMS = {
    "bbw_squeeze_threshold": 0.5,
    "squeeze_min_periods": 10,
    "breakout_volume_multiplier": 2.0, # 提高至2.0（原1.5），要求更强突破
    "breakout_body_pct": 0.008,       # 提高至0.8%（原0.5%）
    "stop_loss_pct": 0.015,           # 放宽至1.5%（原1%）
    "take_profit_pct": 0.04,          # 提高至4%（原3%）
    "max_holding_hours": 24,
}

# ==================== 信号共振确认（关键优化）====================
SIGNAL_FUSION_PARAMS = {
    "enabled": True,
    "timeframe_weights": {
        "15m": 0.2,
        "1h": 0.4,
        "4h": 0.4,
    },
    # 关键优化：提高信号强度阈值
    "min_signal_strength": 60,        # 提高至60（原0.6，即60%），过滤弱信号
    "signal_delay": 30,
}

# ==================== 交易执行参数 ====================
EXECUTION_PARAMS = {
    "order_type": "limit",
    "limit_order_offset": 0.001,
    "split_orders": True,
    "num_splits": 3,
    "split_interval": 10,
    "max_slippage_pct": 0.005,
    "slippage_warning_pct": 0.002,
    "order_timeout": 30,
}

# ==================== 量价分析参数（加强）====================
VOLUME_PARAMS = {
    "obv_enabled": True,
    "obv_ma_period": 20,
    "obv_divergence_threshold": 3,    # 降至3%（原5%），更敏感的背离检测
    "vwap_enabled": True,
    "vwap_deviation_threshold": 0.02,
}

# ==================== 市场情绪参数 ====================
SENTIMENT_PARAMS = {
    "funding_rate_enabled": True,
    "funding_rate_extreme_long": 0.1,
    "funding_rate_bullish": 0.05,
    "funding_rate_extreme_short": -0.05,
    "funding_rate_bearish": -0.02,
    "open_interest_enabled": True,
    "oi_increase_threshold": 10,
    "oi_decrease_threshold": -5,
    "oi_strong_increase": 15,
    "oi_strong_decrease": -15,
    "long_short_ratio_enabled": False,
    "long_ratio_extreme": 0.75,
    "short_ratio_extreme": 0.25,
}

# ==================== 品种差异化参数（新增）====================
# 针对不同品种的特性调整参数
SYMBOL_SPECIFIC_PARAMS = {
    "BTC/USDT": {
        # BTC 波动较小，需要更宽的止损
        "stop_loss_pct": 0.04,        # 4% 止损
        "take_profit_pct": 0.08,      # 8% 止盈
        "min_signal_strength": 65,    # 更高的信号要求
        "adx_threshold": 35,          # 只在强趋势交易
    },
    "ETH/USDT": {
        # ETH 波动性介于 BTC 和 SOL 之间
        "stop_loss_pct": 0.04,        # 4% 止损
        "take_profit_pct": 0.08,      # 8% 止盈
        "min_signal_strength": 65,    # 更高的信号要求
        "adx_threshold": 35,
    },
    "SOL/USDT": {
        # SOL 波动较大，可以使用标准参数（表现最好）
        "stop_loss_pct": 0.035,       # 3.5% 止损
        "take_profit_pct": 0.07,      # 7% 止盈
        "min_signal_strength": 55,    # 相对宽松（已证明有效）
        "adx_threshold": 30,          # 可以在一般趋势交易
    },
}

# ==================== 参数优化范围 ====================
OPTIMIZATION_RANGES = {
    "trend_following": {
        "ema_fast": [40, 50, 60],
        "ema_slow": [180, 200, 220],
        "adx_threshold": [30, 35, 40],
        "stop_loss_pct": [0.03, 0.035, 0.04],
        "take_profit_pct": [0.06, 0.07, 0.08],
    },
    "mean_reversion": {
        "rsi_oversold": [15, 20, 25],
        "rsi_overbought": [75, 80, 85],
        "bb_std": [2.0, 2.5, 3.0],
        "stop_loss_pct": [0.015, 0.02, 0.025],
    }
}

# ==================== 优化说明 ====================
"""
优化逻辑总结：

1. 入场质量优化：
   - 提高 min_signal_strength 从 0.6 到 60（趋势策略）
   - 提高 ADX 阈值从 30 到 35
   - 加强成交量确认要求
   - 目标：减少低质量交易，提高胜率

2. 止损优化：
   - 放宽止损空间：2.5% → 3.5%（BTC/ETH: 4%）
   - 避免震荡市频繁触发止损
   - 给趋势更多发展空间

3. 止盈优化：
   - 提高止盈目标：5% → 7%（BTC/ETH: 8%）
   - 改善盈亏比（当前 <1，目标 >1.5）
   - 移动止损触发点提高到4%

4. 持仓时间优化：
   - 延长最长持仓时间：72h → 96h
   - 给趋势足够的发展时间

5. 品种差异化：
   - BTC/ETH：更严格的入场条件，更宽的止损
   - SOL：保持当前参数（已证明有效）

预期改善：
- 胜率：37.55% → 45%+
- 盈亏比：<1 → >1.2
- 总收益率：-5.42% → 正收益
"""
