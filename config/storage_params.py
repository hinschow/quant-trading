"""
数据存储配置参数
"""

# ==================== 数据存储配置 ====================

STORAGE_PARAMS = {
    # 存储模式
    "storage_mode": "minimal",  # minimal(极简), standard(标准), full(完整)

    # 数据库配置
    "db_path": "data/trading_signals.db",  # 数据库文件路径
    "enable_storage": True,                # 是否启用数据持久化

    # 数据保留策略（天数）
    "signal_retention_days": 90,           # 信号保留90天
    "kline_retention_days": 30,            # K线快照保留30天（如果保存）

    # 自动清理
    "auto_cleanup": True,                  # 启用自动清理过期数据
    "cleanup_on_startup": True,            # 启动时清理一次
    "cleanup_interval_hours": 24,          # 定期清理间隔（小时）

    # 信号过滤（可选，减少存储）
    "min_signal_strength": 0,              # 最低信号强度（0=保存所有）
    "save_neutral_signals": False,         # 是否保存中性信号（HOLD）

    # 数据保存内容（根据storage_mode自动配置）
    "save_signal_details": True,           # 保存信号详情
    "save_price_data": True,               # 保存价格数据
    "save_sentiment_data": True,           # 保存情绪数据（资金费率、OI）
    "save_kline_snapshot": False,          # 保存K线快照（minimal模式关闭）

    # 导出配置
    "export_format": "csv",                # 默认导出格式：csv, json, excel
    "export_dir": "data/exports/",         # 导出目录

    # 性能优化
    "batch_insert": True,                  # 批量插入（提高性能）
    "enable_compression": True,            # 启用数据压缩（SQLite PRAGMA）
    "enable_cache": True,                  # 启用查询缓存
}

# ==================== 存储模式预设 ====================

STORAGE_MODES = {
    # 极简模式（默认推荐）
    "minimal": {
        "save_signal_details": True,
        "save_price_data": True,
        "save_sentiment_data": True,
        "save_kline_snapshot": False,
        "signal_retention_days": 90,
        "description": "只保存信号数据，不保存K线快照，长期占用<5MB",
    },

    # 标准模式
    "standard": {
        "save_signal_details": True,
        "save_price_data": True,
        "save_sentiment_data": True,
        "save_kline_snapshot": True,  # 保存关键K线数据
        "signal_retention_days": 30,
        "description": "保存信号+关键价格数据，适合短期回测，占用~50MB",
    },

    # 完整模式（用于深度回测）
    "full": {
        "save_signal_details": True,
        "save_price_data": True,
        "save_sentiment_data": True,
        "save_kline_snapshot": True,
        "signal_retention_days": 365,  # 保留1年
        "description": "保存所有数据，适合长期回测和研究，占用~1-2GB/年",
    },
}

# ==================== 数据库表结构 ====================

# 信号表字段
SIGNAL_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,

    -- 信号基本信息
    action TEXT NOT NULL,              -- BUY/SELL/HOLD
    strength INTEGER NOT NULL,         -- 信号强度 0-100
    market_regime TEXT,                -- 市场状态

    -- 价格数据
    price REAL NOT NULL,
    price_change_pct REAL,

    -- 情绪数据
    funding_rate REAL,                 -- 资金费率
    open_interest REAL,                -- 持仓量
    oi_change_24h REAL,                -- OI 24小时变化

    -- 信号详情
    reasons TEXT,                      -- 触发原因（JSON数组）
    sentiment_reasons TEXT,            -- 情绪调整原因（JSON数组）

    -- 技术指标快照（可选）
    indicators TEXT,                   -- 指标数据（JSON）

    -- 索引字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    UNIQUE(timestamp, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_timestamp ON signals(timestamp);
CREATE INDEX IF NOT EXISTS idx_action ON signals(action);
CREATE INDEX IF NOT EXISTS idx_strength ON signals(strength);
"""

# K线快照表字段（可选，standard/full模式使用）
KLINE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS kline_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,

    -- OHLCV数据（最近N根K线）
    kline_data TEXT NOT NULL,          -- K线数据（JSON数组）

    -- 外键
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE,

    -- 索引
    UNIQUE(signal_id)
);

CREATE INDEX IF NOT EXISTS idx_kline_symbol ON kline_snapshots(symbol);
"""

# ==================== 统计查询SQL ====================

# 获取数据库统计信息
STATS_QUERY = """
SELECT
    COUNT(*) as total_signals,
    COUNT(DISTINCT symbol) as total_symbols,
    MIN(timestamp) as oldest_signal,
    MAX(timestamp) as newest_signal,
    AVG(strength) as avg_strength,
    SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
    SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
    SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END) as hold_signals
FROM signals;
"""

# 按币种统计
SYMBOL_STATS_QUERY = """
SELECT
    symbol,
    COUNT(*) as signal_count,
    AVG(strength) as avg_strength,
    SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_count,
    SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_count,
    MAX(timestamp) as last_signal
FROM signals
GROUP BY symbol
ORDER BY signal_count DESC;
"""
