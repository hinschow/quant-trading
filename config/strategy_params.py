"""
策略参数配置
基于 v3.1 + BOLL 增强
"""

# ==================== 市场状态识别参数 ====================
MARKET_REGIME_PARAMS = {
    # ADX 参数
    "adx_period": 14,
    "adx_trend_threshold": 30,        # ADX > 30 强趋势
    "adx_weak_trend_threshold": 25,   # ADX > 25 一般趋势
    "adx_range_threshold": 18,        # ADX < 18 震荡市

    # 布林带宽度（BBW）参数
    "bbw_period": 20,                 # BBW 计算周期
    "bbw_ma_period": 20,              # BBW 均值周期
    "bbw_high_threshold": 1.2,        # BBW > 1.2 高波动
    "bbw_normal_threshold": 1.0,      # BBW > 1.0 正常波动
    "bbw_low_threshold": 0.8,         # BBW < 0.8 低波动
    "bbw_squeeze_threshold": 0.5,     # BBW < 0.5 挤压状态
}

# 市场状态与策略映射
MARKET_REGIME_STRATEGY = {
    "STRONG_TREND": {
        "strategy": "trend_following",
        "position_multiplier": 1.0,    # 100% 仓位
        "aggressive": True,
    },
    "TREND": {
        "strategy": "trend_following",
        "position_multiplier": 0.8,    # 80% 仓位
        "aggressive": False,
    },
    "RANGE": {
        "strategy": "mean_reversion",
        "position_multiplier": 0.6,    # 60% 仓位
    },
    "SQUEEZE": {
        "strategy": "breakout",        # 突破策略
        "position_multiplier": 0.3,    # 30% 仓位（试探性）
    },
    "NEUTRAL": {
        "strategy": None,
        "position_multiplier": 0.0,    # 空仓观望
    }
}

# ==================== 趋势跟踪策略参数 ====================
TREND_FOLLOWING_PARAMS = {
    # EMA 参数
    "ema_fast": 50,                   # 快速 EMA 周期
    "ema_slow": 200,                  # 慢速 EMA 周期

    # MACD 参数（可选）
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,

    # ADX 参数
    "adx_period": 14,
    "adx_threshold": 30,              # ADX 确认阈值

    # 成交量确认
    "volume_ma_period": 20,
    "volume_multiplier": 1.3,         # 成交量 > 20日均量 × 1.3

    # 布林带参数（用于额外确认）
    "bb_period": 20,
    "bb_std": 2.0,

    # 止盈止损
    "stop_loss_pct": 0.015,           # 1.5% 止损
    "take_profit_pct": 0.03,          # 3% 止盈
    "trailing_stop_trigger": 0.02,    # 盈利达到 2% 启动移动止损
    "trailing_stop_pct": 0.0,         # 移动到成本价（保本）

    # 时间止损
    "max_holding_hours": 72,          # 最长持仓 72 小时
}

# ==================== 均值回归策略参数 ====================
MEAN_REVERSION_PARAMS = {
    # RSI 参数
    "rsi_period": 14,
    "rsi_oversold": 25,               # RSI < 25 超卖
    "rsi_overbought": 75,             # RSI > 75 超买
    "rsi_neutral": 50,                # RSI 中性值

    # 布林带参数
    "bb_period": 20,
    "bb_std": 2.5,                    # 2.5 倍标准差（更保守）

    # ATR 波动率过滤
    "atr_period": 14,
    "atr_ma_period": 50,
    "atr_multiplier": 1.5,            # ATR > 均值×1.5 暂停入场

    # ADX 过滤（确保在震荡市）
    "adx_period": 14,
    "adx_max_threshold": 25,          # ADX < 25 才做均值回归

    # 止盈止损
    "stop_loss_pct": 0.015,           # 1.5% 止损
    "take_profit_type": "bb_middle",  # 止盈方式：bb_middle 或 rsi_neutral

    # 时间止损
    "max_holding_hours": 24,          # 最长持仓 24 小时
}

# ==================== 突破策略参数（挤压后突破）====================
BREAKOUT_PARAMS = {
    # 挤压识别
    "bbw_squeeze_threshold": 0.5,
    "squeeze_min_periods": 10,        # 至少挤压 10 个周期

    # 突破确认
    "breakout_volume_multiplier": 1.5, # 突破时成交量确认
    "breakout_body_pct": 0.005,       # 突破 K 线实体 > 0.5%

    # 止盈止损
    "stop_loss_pct": 0.01,            # 1% 止损（较紧）
    "take_profit_pct": 0.03,          # 3% 止盈

    # 时间止损
    "max_holding_hours": 24,          # 24 小时未突破则平仓
}

# ==================== 信号共振确认 ====================
SIGNAL_FUSION_PARAMS = {
    # 是否启用多周期确认
    "enabled": True,

    # 时间周期权重
    "timeframe_weights": {
        "15m": 0.2,                   # 短期信号权重
        "1h": 0.4,                    # 中期信号权重（主要）
        "4h": 0.4,                    # 中长期信号权重（主要）
    },

    # 信号强度阈值
    "min_signal_strength": 0.6,       # 加权得分 > 0.6 才执行

    # 信号确认延迟（秒）
    "signal_delay": 30,               # 等待 30 秒确认信号持续性
}

# ==================== 交易执行参数 ====================
EXECUTION_PARAMS = {
    # 订单类型偏好
    "order_type": "limit",            # limit 或 market
    "limit_order_offset": 0.001,      # 限价单偏移 0.1%（买单-0.1%，卖单+0.1%）

    # 分批建仓
    "split_orders": True,
    "num_splits": 3,                  # 分 3 批建仓
    "split_interval": 10,             # 每批间隔 10 秒

    # 滑点控制
    "max_slippage_pct": 0.005,        # 最大滑点 0.5%
    "slippage_warning_pct": 0.002,    # 滑点警告阈值 0.2%

    # 订单超时
    "order_timeout": 30,              # 订单 30 秒未成交则撤单
}

# ==================== 参数优化范围 ====================
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
