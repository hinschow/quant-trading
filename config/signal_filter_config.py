"""
信号过滤配置 - v7.3
灵活的指标开关和权重调整系统

解决问题：
- 胜率太低（18-20%）
- 信号过多且质量差
- 指标太多导致混乱

方案：
A. 保守精确（推荐）：高阈值+核心指标，追求质量
B. 核心简化：只用最可靠的5个指标
C. 灵活自定义：完全自定义每个指标的启用和权重
"""

# ==================== 预设方案 ====================
# 使用哪个方案？ 'CONSERVATIVE' / 'SIMPLIFIED' / 'BALANCED' / 'CUSTOM'
ACTIVE_PRESET = 'BALANCED'  # 默认使用平衡方案

# ==================== 方案A：保守精确（推荐）====================
CONSERVATIVE_CONFIG = {
    "name": "保守精确（高质量）",
    "description": "提高阈值，只用核心指标，追求胜率>40%",

    # 信号阈值配置
    "thresholds": {
        "trend_buy": 60,         # 趋势买入：60分（原40）
        "trend_sell": 60,        # 趋势卖出：60分（原40）
        "mean_reversion_buy": 50,   # 震荡买入：50分（原30）
        "mean_reversion_sell": 50,  # 震荡卖出：50分（原30）
    },

    # 指标启用配置
    "indicators": {
        # 趋势指标（必须）
        "ema": {
            "enabled": True,
            "weight": {
                "cross": 50,           # EMA金叉/死叉：50分
                "in_trend": 20,        # 处于趋势：20分
                "strong_trend": 10,    # 强劲趋势：+10分
            }
        },
        "macd": {
            "enabled": True,
            "weight": {
                "cross": 40,           # MACD金叉/死叉：40分
                "aligned": 15,         # MACD排列：15分
            }
        },
        "adx": {
            "enabled": True,
            "weight": {
                "trending": 10,        # 趋势明确：10分
                "strong_trending": 5,  # 极强趋势：+5分
            }
        },

        # 震荡指标（二选一）
        "rsi": {
            "enabled": True,
            "weight": {
                "healthy": 15,         # RSI健康：15分
                "very_strong": 10,     # RSI强劲：10分
            }
        },
        "kdj": {
            "enabled": False,          # ❌ 禁用KDJ（信号太多）
            "weight": {
                "oversold": 20,
                "overbought": 20,
            }
        },

        # 成交量指标（必须）
        "volume": {
            "enabled": True,
            "weight": {
                "confirmation": 15,    # 成交量确认：15分
            }
        },
        "obv": {
            "enabled": True,           # ✅ 启用但加强惩罚
            "weight": {
                "rising": 15,          # OBV上升：15分
            },
            "divergence_penalty": {    # 量价背离惩罚（加强）
                "severe": 40,          # 严重背离：-40分（原-30）
                "moderate": 30,        # 中度背离：-30分（原-20）
                "mild": 20,            # 轻微背离：-20分（原-10）
                "weak": 10,            # 微弱背离：-10分（原-5）
            }
        },
        "vwap": {
            "enabled": False,          # ❌ 禁用VWAP（贡献小）
            "weight": {
                "above": 5,
                "below": 5,
            }
        },

        # 市场情绪指标（可选）
        "funding_rate": {
            "enabled": True,           # ✅ 保留资金费率
            "weight": {                # 权重已在hyperliquid_client.py定义
                "enabled": True
            }
        },
        "smart_money": {
            "enabled": True,           # ✅ 保留聪明钱包追踪
            "weight": {                # 权重已在hyperliquid_client.py定义
                "enabled": True
            }
        },
    },

    # 市场状态过滤
    "market_regime_filter": {
        "STRONG_TREND": True,     # ✅ 允许在强趋势交易
        "TREND": True,            # ✅ 允许在趋势交易
        "RANGE": False,           # ❌ 禁止在震荡市交易（胜率太低）
        "SQUEEZE": False,         # ❌ 禁止在挤压市交易
        "NEUTRAL": False,         # ❌ 禁止在中性市交易
    },

    # 额外过滤条件
    "extra_filters": {
        "min_adx": 30,            # 最低ADX要求：30（强趋势）
        "require_volume_confirmation": True,   # 必须成交量确认
        "max_rsi_for_buy": 75,    # 买入时RSI上限：75
        "min_rsi_for_sell": 25,   # 卖出时RSI下限：25
    }
}

# ==================== 方案B：核心简化 ====================
SIMPLIFIED_CONFIG = {
    "name": "核心简化（5指标）",
    "description": "只用最可靠的5个核心指标",

    "thresholds": {
        "trend_buy": 50,
        "trend_sell": 50,
        "mean_reversion_buy": 40,
        "mean_reversion_sell": 40,
    },

    "indicators": {
        "ema": {
            "enabled": True,
            "weight": {"cross": 50, "in_trend": 20, "strong_trend": 10}
        },
        "macd": {
            "enabled": True,
            "weight": {"cross": 40, "aligned": 15}
        },
        "adx": {
            "enabled": True,
            "weight": {"trending": 10, "strong_trending": 5}
        },
        "rsi": {
            "enabled": True,
            "weight": {"healthy": 15, "very_strong": 10}
        },
        "kdj": {
            "enabled": False,  # ❌ 禁用
        },
        "volume": {
            "enabled": True,
            "weight": {"confirmation": 15}
        },
        "obv": {
            "enabled": False,  # ❌ 禁用OBV（量价背离太复杂）
        },
        "vwap": {
            "enabled": False,  # ❌ 禁用
        },
        "funding_rate": {
            "enabled": True,
        },
        "smart_money": {
            "enabled": False,  # ❌ 禁用（数据可能不稳定）
        },
    },

    "market_regime_filter": {
        "STRONG_TREND": True,
        "TREND": True,
        "RANGE": False,
        "SQUEEZE": False,
        "NEUTRAL": False,
    },

    "extra_filters": {
        "min_adx": 25,
        "require_volume_confirmation": True,
        "max_rsi_for_buy": 70,
        "min_rsi_for_sell": 30,
    }
}

# ==================== 方案C：平衡方案（新增）====================
BALANCED_CONFIG = {
    "name": "平衡方案（推荐）",
    "description": "阈值适中，允许震荡市交易，适合大部分情况",

    # 信号阈值配置（比保守方案低，比简化方案高）
    "thresholds": {
        "trend_buy": 50,         # 趋势买入：50分（保守60，简化50）
        "trend_sell": 50,        # 趋势卖出：50分
        "mean_reversion_buy": 40,   # 震荡买入：40分（保守50，简化40）
        "mean_reversion_sell": 40,  # 震荡卖出：40分
    },

    # 指标启用配置（核心指标+OBV）
    "indicators": {
        "ema": {
            "enabled": True,
            "weight": {"cross": 50, "in_trend": 20, "strong_trend": 10}
        },
        "macd": {
            "enabled": True,
            "weight": {"cross": 40, "aligned": 15}
        },
        "adx": {
            "enabled": True,
            "weight": {"trending": 10, "strong_trending": 5}
        },
        "rsi": {
            "enabled": True,
            "weight": {"healthy": 15, "very_strong": 10}
        },
        "kdj": {
            "enabled": False,  # ❌ 禁用KDJ（信号太多）
        },
        "volume": {
            "enabled": True,
            "weight": {"confirmation": 15}
        },
        "obv": {
            "enabled": True,   # ✅ 启用OBV
            "weight": {"rising": 15},
            "divergence_penalty": {  # 中等惩罚
                "severe": 35,
                "moderate": 25,
                "mild": 15,
                "weak": 8,
            }
        },
        "vwap": {
            "enabled": False,  # ❌ 禁用VWAP
        },
        "funding_rate": {
            "enabled": True,
        },
        "smart_money": {
            "enabled": True,   # ✅ 启用聪明钱包
        },
    },

    # 市场状态过滤（允许震荡市）
    "market_regime_filter": {
        "STRONG_TREND": True,   # ✅ 允许强趋势
        "TREND": True,          # ✅ 允许趋势
        "RANGE": True,          # ✅ 允许震荡市（关键差异）
        "SQUEEZE": False,       # ❌ 禁止挤压市
        "NEUTRAL": False,       # ❌ 禁止中性市
    },

    # 额外过滤（适中）
    "extra_filters": {
        "min_adx": 20,          # 最低ADX：20（保守30，简化25）
        "require_volume_confirmation": False,  # 不强制要求成交量确认
        "max_rsi_for_buy": 75,  # 买入RSI上限：75
        "min_rsi_for_sell": 25, # 卖出RSI下限：25
    }
}

# ==================== 方案D：灵活自定义 ====================
CUSTOM_CONFIG = {
    "name": "灵活自定义",
    "description": "完全自定义配置（复制上面的配置并修改）",

    # 你可以在这里完全自定义...
    "thresholds": {
        "trend_buy": 50,         # 根据需要调整
        "trend_sell": 50,
        "mean_reversion_buy": 40,
        "mean_reversion_sell": 40,
    },

    "indicators": {
        # 自行配置每个指标...
        "ema": {"enabled": True, "weight": {"cross": 50, "in_trend": 20, "strong_trend": 10}},
        "macd": {"enabled": True, "weight": {"cross": 40, "aligned": 15}},
        "adx": {"enabled": True, "weight": {"trending": 10, "strong_trending": 5}},
        "rsi": {"enabled": True, "weight": {"healthy": 15, "very_strong": 10}},
        "kdj": {"enabled": True, "weight": {"oversold": 20, "overbought": 20}},
        "volume": {"enabled": True, "weight": {"confirmation": 15}},
        "obv": {"enabled": True, "weight": {"rising": 15},
                "divergence_penalty": {"severe": 30, "moderate": 20, "mild": 10, "weak": 5}},
        "vwap": {"enabled": False, "weight": {"above": 5, "below": 5}},
        "funding_rate": {"enabled": True},
        "smart_money": {"enabled": True},
    },

    "market_regime_filter": {
        "STRONG_TREND": True,
        "TREND": True,
        "RANGE": True,
        "SQUEEZE": True,
        "NEUTRAL": False,
    },

    "extra_filters": {
        "min_adx": 25,
        "require_volume_confirmation": False,
        "max_rsi_for_buy": 80,
        "min_rsi_for_sell": 20,
    }
}

# ==================== 方案选择器 ====================
def get_active_config():
    """获取当前激活的配置"""
    if ACTIVE_PRESET == 'CONSERVATIVE':
        return CONSERVATIVE_CONFIG
    elif ACTIVE_PRESET == 'SIMPLIFIED':
        return SIMPLIFIED_CONFIG
    elif ACTIVE_PRESET == 'BALANCED':
        return BALANCED_CONFIG
    elif ACTIVE_PRESET == 'CUSTOM':
        return CUSTOM_CONFIG
    else:
        raise ValueError(f"未知的预设方案: {ACTIVE_PRESET}")

def print_config_summary():
    """打印配置摘要"""
    config = get_active_config()
    print(f"\n{'='*80}")
    print(f"当前信号配置: {config['name']}")
    print(f"{'='*80}")
    print(f"说明: {config['description']}")
    print()

    print("【阈值设置】")
    for key, value in config['thresholds'].items():
        print(f"  {key}: {value}分")
    print()

    print("【启用指标】")
    enabled_count = 0
    for name, settings in config['indicators'].items():
        if settings.get('enabled', True):
            enabled_count += 1
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")
    print(f"\n  总计: {enabled_count}/10 个指标启用")
    print()

    print("【市场状态过滤】")
    for regime, allowed in config['market_regime_filter'].items():
        status = "✅ 允许" if allowed else "❌ 禁止"
        print(f"  {regime}: {status}")
    print()

    print("【额外过滤】")
    for key, value in config['extra_filters'].items():
        print(f"  {key}: {value}")
    print(f"{'='*80}\n")

# ==================== 快速切换函数 ====================
def switch_to_conservative():
    """切换到保守精确方案"""
    global ACTIVE_PRESET
    ACTIVE_PRESET = 'CONSERVATIVE'
    print("✅ 已切换到：保守精确方案")
    print_config_summary()

def switch_to_simplified():
    """切换到核心简化方案"""
    global ACTIVE_PRESET
    ACTIVE_PRESET = 'SIMPLIFIED'
    print("✅ 已切换到：核心简化方案")
    print_config_summary()

def switch_to_balanced():
    """切换到平衡方案"""
    global ACTIVE_PRESET
    ACTIVE_PRESET = 'BALANCED'
    print("✅ 已切换到：平衡方案")
    print_config_summary()

def switch_to_custom():
    """切换到自定义方案"""
    global ACTIVE_PRESET
    ACTIVE_PRESET = 'CUSTOM'
    print("✅ 已切换到：自定义方案")
    print_config_summary()

# ==================== 测试 ====================
if __name__ == '__main__':
    print_config_summary()
