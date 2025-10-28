"""
策略参数配置 - 优化版 v7.2 (方案D-Stage2.2: 量价背离分级 + Hyperliquid资金费率 + 聪明钱包追踪)
基于Stage2回测分析优化：集成Hyperliquid资金费率和聪明钱包追踪作为市场情绪调整因子

Stage2成果：
- 总收益：+3.04%（vs Stage1的+5.66%）
- 交易数：14笔（vs Stage1的12笔，+17%）
- BTC显著改善：-3.37% → -0.43%（+2.95%）
- ETH异常恶化：+0.55% → -5.02%（-5.56%，需观察）
- SOL保持稳定：+8.49%

Stage2核心改进验证：
✅ 量价背离分级惩罚系统按预期工作
✅ BTC新增2笔交易都盈利（轻微背离+0.65%，微弱背离+2.59%）
✅ 新增交易质量高（100%盈利率）

Stage2.1优化（资金费率）：
1. 集成Hyperliquid资金费率API
2. 资金费率调整规则：
   - 极度贪婪（>1.5%）：-15分
   - 贪婪（>1%）：-10分
   - 偏热（>0.5%）：-5分
   - 正常（-0.5~0.5%）：0分
   - 偏冷（<-0.5%）：+5分
   - 恐慌（<-1%）：+10分
   - 极度恐慌（<-1.5%）：+15分

Stage2.2优化（聪明钱包追踪）：
1. 集成Hyperliquid OpenInterest追踪
2. 聪明钱包信号调整规则：
   - OI↑ + 价格↑（大户做多）：+20分（阈值：OI增长>5%，价格上涨>2%）
   - OI↑ + 价格↓（大户做空）：-20分（阈值：OI增长>5%，价格下跌>2%）
   - OI↓ + 价格↑（获利了结）：-10分（阈值：OI减少>3%，价格上涨>2%）
   - OI↓ + 价格↓（止损离场）：+5分（阈值：OI减少>3%，价格下跌>2%）
3. 数据持久化：自动保存OI和资金费率历史数据，支持连续运行
4. 时间窗口：1小时OI变化

预期效果：
- 资金费率：过滤5-10%过热信号，增加5-10%反弹机会
- 聪明钱包：跟随大户方向，避免反向操作
- 综合效果：总收益从+3.04%提升到+5~7%，胜率提升10%
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

# ==================== 交易对配置 ====================
# 用户可自定义要交易的交易对列表
# 系统会自动尝试从Hyperliquid获取数据，如果不可用则回退到Binance
TRADING_SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'SOL/USDT',
    'SNX/USDT',
    'BNB/USDT',
    'SUI/USDT',
    '1000RATS/USDT',
    'M/USDT',
]

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

# ==================== 品种差异化参数（方案D-Stage1）====================
# 针对不同品种的特性调整参数 - 第1阶段：降低阈值增加交易机会
SYMBOL_SPECIFIC_PARAMS = {
    "BTC/USDT": {
        # BTC 方案D-Stage1：进一步降低阈值，显著增加交易机会
        "stop_loss_pct": 0.03,                  # 3% 止损
        "take_profit_pct": 0.05,                # 5% 止盈
        "min_signal_strength": 55,              # 从60降到55 ⬇️（预期2笔→5-6笔）
        "adx_threshold": 25,                    # 从30降到25 ⬇️（放宽趋势要求）
        "min_signal_with_divergence": 75,       # 保持75（有背离时的最低强度）
        "filter_divergence_enabled": True,      # 保持启用量价背离过滤
    },
    "ETH/USDT": {
        # ETH 方案D-Stage1：适度降低阈值，增加交易机会
        "stop_loss_pct": 0.03,                  # 3% 止损
        "take_profit_pct": 0.05,                # 5% 止盈
        "min_signal_strength": 60,              # 从65降到60 ⬇️（预期5笔→7-8笔）
        "adx_threshold": 25,                    # 从30降到25 ⬇️（放宽趋势要求）
        "min_signal_with_divergence": 75,       # 保持75
        "filter_divergence_enabled": True,      # 保持启用
    },
    "SOL/USDT": {
        # SOL 方案D-Stage1：保守降低阈值，保持盈利能力
        "stop_loss_pct": 0.025,                 # 2.5% 止损
        "take_profit_pct": 0.045,               # 4.5% 止盈
        "min_signal_strength": 55,              # 从60降到55 ⬇️（保守增加机会）
        "adx_threshold": 25,                    # 从30降到25 ⬇️（适应30m周期）
        "min_signal_with_divergence": 80,       # 保持80（SOL更严格）
        "filter_divergence_enabled": True,      # 保持启用
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

# ==================== 方案D-Stage1 优化说明 ====================
"""
方案D-Stage1 优化逻辑总结（渐进式灵活化第1阶段）：

基于方案B回测结果分析：
- 方案B总收益：+4.52%（已实现盈利✅）
- BTC：-3.37%（2笔交易，样本太少❌）
- ETH：-0.31%（5笔交易，接近盈亏平衡⚠️）
- SOL：+8.21%（4笔交易，盈利能力强✅）
- 总交易数：11笔（样本量偏小⚠️）

核心问题：
1. 交易机会太少，特别是BTC只有2笔
2. 总样本量11笔统计不够显著
3. 指标要求过于严格，错过部分有效信号

方案D-Stage1 改进（渐进式第1阶段）：

1. 降低ADX要求：30 → 25
   - 理由：30m周期的ADX普遍低于1h周期
   - 很多有效趋势ADX在25-28之间
   - 预期：增加30-40%交易机会

2. 降低信号强度阈值：
   - BTC: 60 → 55（目标：2笔 → 5-6笔，+150%）
   - ETH: 65 → 60（目标：5笔 → 7-8笔，+40-60%）
   - SOL: 60 → 55（目标：4笔 → 6-8笔，+50-100%）

3. 保持量价背离过滤：
   - min_signal_with_divergence保持75/80
   - 继续过滤低质量假突破信号
   - 风险控制不放松

4. 保持止损止盈参数：
   - 不改变风险管理策略
   - 避免引入过大风险

预期效果（方案D-Stage1 vs 方案B）：
- 总交易数：11笔 → 14-18笔（+27-64%）
- BTC：2笔 → 5-6笔，-3.37% → -1%~+1%
- ETH：5笔 → 7-8笔，-0.31% → +1%~+3%
- SOL：4笔 → 6-8笔，+8.21% → +6%~+10%
- 总收益：+4.52% → +5%~+7%

风险控制：
- 仅降低阈值，不改变其他逻辑
- 保持量价背离过滤
- 如果第1阶段成功，再实施第2阶段（量价背离分级、权重调整）
- 如果第1阶段效果不佳，回退到方案B

下一阶段计划：
- Stage2: 量价背离分级惩罚（-10/-20/-30）
- Stage3: 指标权重重构 + 趋势延续信号
"""
