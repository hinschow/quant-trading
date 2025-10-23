"""
风险管理参数配置
基于 v3.1 稳健收益版
"""

# ==================== 账户级风险限制 ====================
ACCOUNT_RISK_LIMITS = {
    # 仓位限制
    "max_total_position_pct": 0.50,      # 总仓位不超过账户 50%
    "max_single_position_pct": 0.20,     # 单币种不超过账户 20%
    "max_positions": 5,                  # 最多同时持有 5 个币种
    "min_position_size_usdt": 50,        # 最小开仓金额 50 USDT

    # 亏损限制
    "max_daily_loss_pct": 0.03,          # 单日最大亏损 3%
    "max_weekly_loss_pct": 0.08,         # 单周最大亏损 8%
    "max_monthly_loss_pct": 0.15,        # 单月最大亏损 15%
    "max_drawdown_pct": 0.10,            # 最大回撤 10%（触发熔断）

    # 单笔交易风险
    "max_trade_risk_pct": 0.01,          # 单笔交易风险不超过账户 1%
    "min_risk_reward_ratio": 1.8,        # 最小盈亏比 1.8:1

    # 连续亏损控制
    "max_consecutive_losses": 3,         # 连续亏损 3 次后降低仓位
    "loss_reduction_factor": 0.5,        # 降低仓位至 50%
}

# ==================== 币种级风险限制 ====================
SYMBOL_RISK_LIMITS = {
    # 流动性要求
    "min_24h_volume_usdt": 50_000_000,   # 24小时交易量 > 5000万 U
    "max_spread_pct": 0.002,             # 最大买卖价差 0.2%
    "min_orderbook_depth_usdt": 100_000, # 订单簿深度 > 10万 U（前5档）

    # 波动率限制
    "max_atr_pct": 0.08,                 # ATR 不超过价格 8%
    "max_price_change_1h": 0.10,         # 1小时涨跌幅不超过 10%
    "max_price_change_24h": 0.30,        # 24小时涨跌幅不超过 30%

    # 持仓时间
    "max_holding_hours": 72,             # 最长持仓 72 小时
    "warn_holding_hours": 48,            # 48 小时发出持仓告警
}

# ==================== 动态仓位管理（改进凯利公式）====================
POSITION_SIZING = {
    # 基础方法
    "method": "kelly_half",              # fixed, kelly, kelly_half, volatility

    # 凯利公式参数
    "kelly": {
        "use_half_kelly": True,          # 使用半凯利（更保守）
        "max_position_pct": 0.15,        # 凯利公式最大仓位上限 15%
        "min_win_rate": 0.40,            # 最低胜率要求
        "default_win_rate": 0.50,        # 默认胜率（历史数据不足时）
        "default_profit_factor": 2.0,    # 默认盈亏比
    },

    # 固定仓位
    "fixed": {
        "position_pct": 0.10,            # 固定 10% 仓位
    },

    # 波动率调整仓位
    "volatility": {
        "target_volatility": 0.15,       # 目标组合波动率 15%
        "lookback_period": 30,           # 回溯 30 天计算波动率
    },
}

# ==================== 止损止盈参数 ====================
STOP_LOSS_TAKE_PROFIT = {
    # ATR 动态止损
    "use_atr_stops": True,
    "atr_period": 14,
    "atr_multiplier": 1.5,               # 止损 = 入场价 ± ATR × 1.5

    # 固定百分比止损（备用）
    "fixed_stop_loss_pct": 0.015,        # 1.5%
    "fixed_take_profit_pct": 0.03,       # 3%

    # 移动止损
    "trailing_stop_enabled": True,
    "trailing_stop_trigger_pct": 0.02,   # 盈利 2% 后启动
    "trailing_stop_distance_pct": 0.01,  # 回撤 1% 触发（或移至成本价）

    # 时间止损
    "time_stop_enabled": True,
    "time_stop_hours": {
        "trend_following": 72,           # 趋势跟踪 72 小时
        "mean_reversion": 24,            # 均值回归 24 小时
        "breakout": 24,                  # 突破策略 24 小时
    }
}

# ==================== 熔断机制 ====================
CIRCUIT_BREAKER = {
    # 熔断级别
    "levels": {
        "normal": {
            "max_drawdown": 0.05,        # 回撤 < 5%
            "action": "normal",          # 正常交易
        },
        "warning": {
            "max_drawdown": 0.08,        # 回撤 5-8%
            "action": "reduce_position", # 降低仓位
            "position_reduction": 0.5,   # 降至 50%
        },
        "critical": {
            "max_drawdown": 0.10,        # 回撤 8-10%
            "action": "stop_new_trades", # 禁止开新仓
        },
        "emergency": {
            "max_drawdown": 0.12,        # 回撤 > 10%
            "action": "close_all",       # 全部平仓
            "pause_hours": 48,           # 暂停交易 48 小时
        }
    },

    # 单日亏损熔断
    "daily_loss_circuit_breaker": {
        "enabled": True,
        "loss_threshold_pct": 0.05,      # 单日亏损 > 5% 触发
        "action": "close_all",
        "pause_hours": 24,
    },

    # 连续亏损熔断
    "consecutive_loss_circuit_breaker": {
        "enabled": True,
        "max_consecutive": 5,            # 连续亏损 5 笔
        "action": "reduce_position",
        "position_reduction": 0.3,       # 降至 30%
        "review_hours": 12,              # 12 小时后恢复
    }
}

# ==================== 异常检测与处理 ====================
ANOMALY_DETECTION = {
    # 价格异常
    "price_spike": {
        "enabled": True,
        "deviation_threshold": 0.10,     # 价格偏离均价 10%
        "atr_multiplier": 3.0,           # 或偏离 > 3×ATR
        "action": "pause_trading",       # 暂停交易
        "pause_minutes": 30,
    },

    # 成交量异常
    "volume_spike": {
        "enabled": True,
        "multiplier": 5.0,               # 成交量 > 均量 × 5
        "action": "alert",               # 仅告警，不暂停
    },

    # API 异常
    "api_failure": {
        "max_retries": 3,                # 最大重试次数
        "retry_delay": 2,                # 重试间隔（秒）
        "switch_to_backup": True,        # 失败后切换备用交易所
        "emergency_close": True,         # 无法恢复则紧急平仓
    },

    # 数据延迟
    "data_latency": {
        "max_latency_ms": 1000,          # 最大延迟 1000ms
        "action": "alert",
    },

    # 订单异常
    "order_anomaly": {
        "max_failed_orders": 5,          # 连续失败 5 次
        "action": "pause_trading",
        "pause_hours": 1,
    }
}

# ==================== 风险报告 ====================
RISK_REPORTING = {
    # 实时监控指标
    "real_time_metrics": [
        "current_drawdown",
        "daily_pnl",
        "total_position_value",
        "risk_exposure",
        "var_95",                        # Value at Risk (95% 置信度)
    ],

    # 报告频率
    "report_frequency": {
        "real_time_alert": True,         # 实时告警
        "hourly_summary": False,
        "daily_summary": True,           # 每日总结
        "weekly_report": True,           # 每周报告
    },

    # 告警阈值
    "alert_thresholds": {
        "drawdown_warning": 0.05,        # 回撤 5% 告警
        "drawdown_critical": 0.08,       # 回撤 8% 严重告警
        "daily_loss_warning": 0.03,      # 单日亏损 3% 告警
        "position_concentration": 0.30,   # 单币种占比 > 30% 告警
    }
}

# ==================== 动态风险调整 ====================
DYNAMIC_RISK_ADJUSTMENT = {
    # 是否启用动态风险调整
    "enabled": True,

    # 市场环境评估
    "market_condition_metrics": {
        "volatility_regime": {
            "low": 0.10,                 # VIX < 10%
            "medium": 0.20,              # VIX 10-20%
            "high": 0.30,                # VIX > 20%
        },
        "trend_strength": {
            "weak": 20,                  # ADX < 20
            "moderate": 30,              # ADX 20-30
            "strong": 40,                # ADX > 30
        }
    },

    # 风险参数调整系数
    "adjustment_factors": {
        # 高波动环境
        "high_volatility": {
            "position_size_multiplier": 0.7,    # 仓位降至 70%
            "max_positions": 3,                 # 最多 3 个仓位
            "stop_loss_multiplier": 1.2,        # 止损放宽 20%
        },
        # 低波动环境
        "low_volatility": {
            "position_size_multiplier": 1.2,    # 仓位提升至 120%
            "max_positions": 6,                 # 最多 6 个仓位
            "stop_loss_multiplier": 0.9,        # 止损收紧 10%
        },
        # 强趋势环境
        "strong_trend": {
            "position_size_multiplier": 1.3,    # 仓位提升至 130%
            "trailing_stop_enabled": True,
        },
        # 震荡市
        "ranging_market": {
            "position_size_multiplier": 0.8,    # 仓位降至 80%
            "max_holding_hours": 12,            # 缩短持仓时间
        }
    },

    # 绩效反馈调整
    "performance_based_adjustment": {
        "enabled": True,
        "review_period_days": 30,              # 评估过去 30 天表现

        # 表现良好（夏普 > 2.5）
        "good_performance": {
            "position_size_multiplier": 1.2,
            "max_total_position_pct": 0.60,
        },

        # 表现不佳（夏普 < 1.0）
        "poor_performance": {
            "position_size_multiplier": 0.5,
            "max_total_position_pct": 0.30,
            "review_strategy": True,
        }
    }
}
