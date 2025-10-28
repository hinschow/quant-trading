"""
策略参数配置 - 优化版 v5.0 (方案B)
基于方案A多周期回测分析优化：针对BTC/ETH进一步优化，屏蔽量价背离假信号

优化重点：
1. 降低BTC信号阈值（60），增加交易机会
2. 新增量价背离信号过滤（高阈值75/80）
3. 降低ADX要求到30，适应30m周期
4. 保持ETH参数（已接近盈亏平衡）
5. 保持SOL参数（已实现盈利）
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

    # 止盈止损（方案A：保守优化）
    "stop_loss_pct": 0.03,            # 收紧至3%（从3.5%），更及时止损
    "take_profit_pct": 0.05,          # 降至5%（从7%），更现实的目标
    "trailing_stop_trigger": 0.03,    # 盈利3%后启动移动止损
    "trailing_stop_pct": 0.01,        # 移动止损保留1%利润

    # 时间止损
    "max_holding_hours": 60,          # 缩短至60小时（从96），减少风险暴露
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

# ==================== 品种差异化参数（方案B优化）====================
# 针对不同品种的特性调整参数
SYMBOL_SPECIFIC_PARAMS = {
    "BTC/USDT": {
        # BTC 方案B：降低阈值增加交易机会，增加量价背离过滤
        "stop_loss_pct": 0.03,                  # 3% 止损
        "take_profit_pct": 0.05,                # 5% 止盈
        "min_signal_strength": 60,              # 从65降到60，增加交易机会
        "adx_threshold": 30,                    # 从35降到30，适应30m周期
        "min_signal_with_divergence": 75,       # 新增：有量价背离时要求信号强度≥75
        "filter_divergence_enabled": True,      # 新增：启用量价背离过滤
    },
    "ETH/USDT": {
        # ETH 方案B：保持阈值，增加量价背离过滤
        "stop_loss_pct": 0.03,                  # 3% 止损
        "take_profit_pct": 0.05,                # 5% 止盈
        "min_signal_strength": 65,              # 保持65（已接近盈亏平衡）
        "adx_threshold": 30,                    # 从35降到30，适应30m周期
        "min_signal_with_divergence": 75,       # 新增：有量价背离时要求≥75
        "filter_divergence_enabled": True,      # 新增：启用量价背离过滤
    },
    "SOL/USDT": {
        # SOL 方案B：保持方案A参数（已盈利）
        "stop_loss_pct": 0.025,                 # 2.5% 止损
        "take_profit_pct": 0.045,               # 4.5% 止盈
        "min_signal_strength": 60,              # 保持60
        "adx_threshold": 30,                    # 保持30
        "min_signal_with_divergence": 80,       # 新增：SOL更严格，要求≥80
        "filter_divergence_enabled": True,      # 新增：启用量价背离过滤
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

# ==================== 方案B优化说明 ====================
"""
方案B优化逻辑总结：

基于方案A多周期回测结果（30m周期最优）：
- 30m周期总收益：-3.09%（已从v4.0的-8.88%改善+5.79%）
- SOL首次盈利：+1.15%（盈亏比1.12）
- ETH接近盈亏平衡：-0.76%（已从-10.20%大幅改善）
- BTC交易过少：3笔（信号阈值65太高）

方案B核心改进：

1. 量价背离过滤（关键新增）：
   - 在 strategy_engine.py 中识别 "⚠️ 量价背离(假突破风险)" 信号
   - BTC/ETH：要求信号强度≥75才接受有背离的信号（否则过滤）
   - SOL：要求信号强度≥80（更严格）
   - 目标：屏蔽方案A中BTC第2、3笔和ETH多笔的假突破交易

2. BTC参数调整（增加交易机会）：
   - min_signal_strength: 65 → 60（方案A只有3笔交易太少）
   - adx_threshold: 35 → 30（适应30m周期特性）
   - 目标：在60天内产生5-8笔交易（保持质量）

3. ETH参数微调：
   - min_signal_strength: 保持65（已接近盈亏平衡）
   - adx_threshold: 35 → 30（适应30m周期）
   - 量价背离过滤：屏蔽方案A中的假突破交易

4. SOL参数保持：
   - 所有参数不变（已实现盈利+1.15%，盈亏比1.12）
   - 仅增加量价背离过滤（min_signal_with_divergence=80）

5. 技术实现：
   - 在 generate_signal() 中应用品种参数前增加量价背离检查
   - 如果信号包含"⚠️ 量价背离"且强度 < min_signal_with_divergence，则过滤

预期改善（方案B vs 方案A-30m）：
- BTC：-3.47% → 预期 -1%~0%（增加优质交易，过滤假突破）
- ETH：-0.76% → 预期 0%~+2%（过滤假突破）
- SOL：+1.15% → 预期 +1%~+3%（保持或略微改善）
- 总收益：-3.09% → 预期 0%~+2%（首次实现盈利）
"""
