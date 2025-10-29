"""
外部数据源配置
包括社交媒体、新闻、链上数据等
"""

# ==================== 社交媒体情绪分析 ====================
SOCIAL_SENTIMENT_PARAMS = {
    "enabled": True,

    # Twitter/X 监控配置
    "twitter": {
        "enabled": True,
        "influencers": [
            "elonmusk",         # Tesla/SpaceX CEO, 影响力极强
            "VitalikButerin",   # Ethereum创始人
            "cz_binance",       # Binance前CEO
            "APompliano",       # 加密投资人
            "naval",            # 投资人/哲学家
            "michael_saylor",   # MicroStrategy CEO, BTC巨鲸
            "aantonop",         # Bitcoin专家
            "novogratz",        # Galaxy Digital CEO
        ],
        "keywords": {
            "positive": ["bullish", "moon", "pump", "adoption", "breakthrough", "upgrade"],
            "negative": ["bearish", "dump", "crash", "scam", "hack", "ban"],
            "neutral": ["BTC", "Bitcoin", "ETH", "Ethereum", "crypto", "blockchain"],
        },
        # API配置（需要申请）
        "api_provider": "twitter_v2",  # 或 "nitter"（免费镜像）
        "update_interval": 300,         # 5分钟更新
    },

    # 情绪得分规则
    "sentiment_scores": {
        "influencer_multiplier": 3.0,   # 名人言论权重x3
        "positive_boost": 10,           # 正面情绪 +10分
        "negative_penalty": -15,        # 负面情绪 -15分
        "critical_multiplier": 2.0,     # 关键词加倍
    },

    # LunarCrush API（专业加密社交数据）
    "lunarcrush": {
        "enabled": False,               # 需要付费API
        "api_key": "",
        "metrics": ["social_volume", "social_sentiment", "galaxy_score"],
    },
}

# ==================== 新闻事件监控 ====================
NEWS_PARAMS = {
    "enabled": True,

    # 新闻源配置
    "sources": [
        "coindesk",
        "cointelegraph",
        "theblock",
        "decrypt",
        "bitcoinmagazine",
        "cryptoslate",
    ],

    # CryptoPanic API（免费）
    "cryptopanic": {
        "enabled": True,
        "api_key": "free",              # 免费key或申请的key
        "filter": {
            "currencies": ["BTC", "ETH", "SOL", "BNB"],
            "kind": "news",             # news, media, blog
        },
        "update_interval": 600,         # 10分钟更新
    },

    # 关键词影响评分
    "keyword_impact": {
        # 重大利好
        "critical_positive": {
            "keywords": ["ETF approved", "halving", "institutional adoption",
                        "major partnership", "upgrade successful"],
            "score": 25,
        },
        # 一般利好
        "positive": {
            "keywords": ["partnership", "adoption", "positive regulation",
                        "technical upgrade", "all-time high"],
            "score": 10,
        },
        # 重大利空
        "critical_negative": {
            "keywords": ["hack", "exchange collapse", "ban", "major lawsuit",
                        "security breach", "rug pull"],
            "score": -30,
        },
        # 一般利空
        "negative": {
            "keywords": ["regulation", "concern", "warning", "delayed", "investigation"],
            "score": -10,
        },
    },

    # 新闻影响衰减
    "decay": {
        "half_life_hours": 12,          # 12小时影响减半
        "max_age_hours": 48,            # 48小时后不再计入
    },
}

# ==================== 链上数据监控 ====================
ONCHAIN_PARAMS = {
    "enabled": True,

    # 鲸鱼交易监控
    "whale_alerts": {
        "enabled": True,
        "api_provider": "whale_alert",   # whale-alert.io (有免费tier)
        "thresholds": {
            "BTC": 50,                   # 50 BTC
            "ETH": 500,                  # 500 ETH
            "USDT": 1000000,             # 100万 USDT
        },
        "impact_scores": {
            "whale_buy": 15,             # 鲸鱼买入 +15
            "whale_sell": -15,           # 鲸鱼卖出 -15
            "exchange_inflow": -10,      # 转入交易所 -10（卖压）
            "exchange_outflow": 10,      # 转出交易所 +10（囤币）
        },
    },

    # Glassnode 指标（需要付费，可选）
    "glassnode": {
        "enabled": False,
        "api_key": "",
        "metrics": [
            "exchange_net_flow",         # 交易所净流量
            "mvrv_ratio",                # 市值/实现市值
            "nupl",                      # 净未实现盈亏
        ],
    },
}

# ==================== 资金费率和持仓量（已实现）====================
MARKET_DATA_PARAMS = {
    "funding_rate": {
        "enabled": True,
        "sources": ["hyperliquid", "binance"],
        "update_interval": 300,          # 5分钟
        "impact_scores": {
            "extreme_long": -15,         # >0.1% 极度贪婪
            "long": -10,                 # >0.05%
            "neutral": 0,                # -0.02% ~ 0.02%
            "short": 10,                 # <-0.02%
            "extreme_short": 15,         # <-0.05% 极度恐慌
        },
    },

    "open_interest": {
        "enabled": True,
        "sources": ["hyperliquid", "binance"],
        "update_interval": 300,
        "impact_scores": {
            "oi_price_up_up": 20,        # OI↑ + 价格↑ (大户做多)
            "oi_price_up_down": -20,     # OI↑ + 价格↓ (大户做空)
            "oi_price_down_up": -10,     # OI↓ + 价格↑ (获利了结)
            "oi_price_down_down": 5,     # OI↓ + 价格↓ (止损离场)
        },
    },
}

# ==================== 整合权重配置 ====================
EXTERNAL_DATA_WEIGHTS = {
    "technical_signals": 0.50,       # 技术指标权重 50%
    "social_sentiment": 0.15,        # 社交媒体 15%
    "news_impact": 0.15,             # 新闻事件 15%
    "market_data": 0.15,             # 资金费率+OI 15%
    "onchain_data": 0.05,            # 链上数据 5%
}

# ==================== 数据刷新策略 ====================
REFRESH_STRATEGY = {
    "realtime": {                    # 实时监控
        "social": 300,               # 5分钟
        "news": 600,                 # 10分钟
        "market_data": 180,          # 3分钟
        "onchain": 600,              # 10分钟
    },
    "backtest": {                    # 回测模式
        "enabled": False,            # 回测时禁用外部数据
    },
}

# ==================== 告警阈值 ====================
ALERT_THRESHOLDS = {
    "sentiment_spike": {
        "positive": 30,              # 情绪得分 > 30 触发利好告警
        "negative": -30,             # 情绪得分 < -30 触发利空告警
    },
    "whale_activity": {
        "large_transaction": True,    # 大额交易告警
        "exchange_flow": True,        # 交易所异常流动告警
    },
    "news_critical": True,            # 重大新闻立即告警
}
