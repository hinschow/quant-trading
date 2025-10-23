-- 数据库初始化脚本
-- 量化交易系统 v3.2

-- ==================== K线数据表 ====================
CREATE TABLE IF NOT EXISTS klines (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp BIGINT NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange, symbol, timeframe, timestamp)
);

-- 索引优化
CREATE INDEX idx_klines_symbol_timeframe ON klines(symbol, timeframe);
CREATE INDEX idx_klines_timestamp ON klines(timestamp);

-- ==================== 订单表 ====================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- BUY/SELL
    type VARCHAR(20) NOT NULL,  -- MARKET/LIMIT/STOP_LOSS/TAKE_PROFIT
    price DECIMAL(20, 8),
    amount DECIMAL(20, 8) NOT NULL,
    filled DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(20) NOT NULL,  -- OPEN/FILLED/CANCELED/REJECTED
    strategy VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ==================== 交易记录表 ====================
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- LONG/SHORT
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    amount DECIMAL(20, 8) NOT NULL,
    pnl DECIMAL(20, 8),
    pnl_pct DECIMAL(10, 4),
    commission DECIMAL(20, 8) DEFAULT 0,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    holding_hours INT,
    exit_reason VARCHAR(50),  -- TAKE_PROFIT/STOP_LOSS/SIGNAL/TIMEOUT
    market_regime VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);

-- ==================== 持仓表 ====================
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    side VARCHAR(10) NOT NULL,  -- LONG/SHORT
    amount DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    unrealized_pnl_pct DECIMAL(10, 4),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    strategy VARCHAR(50) NOT NULL,
    market_regime VARCHAR(20),
    opened_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 性能指标表 ====================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    losing_trades INT DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    total_commission DECIMAL(20, 8) DEFAULT 0,
    win_rate DECIMAL(5, 4),
    profit_factor DECIMAL(10, 4),
    avg_win DECIMAL(20, 8),
    avg_loss DECIMAL(20, 8),
    max_win DECIMAL(20, 8),
    max_loss DECIMAL(20, 8),
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    account_balance DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 风险事件表 ====================
CREATE TABLE IF NOT EXISTS risk_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- CIRCUIT_BREAKER/DAILY_LOSS/POSITION_LIMIT
    level VARCHAR(20) NOT NULL,       -- INFO/WARNING/ERROR/CRITICAL
    message TEXT NOT NULL,
    data JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_level ON risk_events(level);
CREATE INDEX idx_risk_events_created_at ON risk_events(created_at);

-- ==================== 市场状态记录表 ====================
CREATE TABLE IF NOT EXISTS market_regimes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    regime VARCHAR(20) NOT NULL,  -- STRONG_TREND/TREND/RANGE/SQUEEZE/NEUTRAL
    adx DECIMAL(10, 4),
    bbw_ratio DECIMAL(10, 4),
    confidence DECIMAL(5, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_market_regimes_symbol ON market_regimes(symbol);
CREATE INDEX idx_market_regimes_timestamp ON market_regimes(timestamp);

-- ==================== 信号记录表 ====================
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal VARCHAR(10) NOT NULL,  -- BUY/SELL/HOLD
    strength DECIMAL(5, 4),
    price DECIMAL(20, 8),
    indicators JSONB,
    executed BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_executed ON signals(executed);

-- ==================== 账户余额历史表 ====================
CREATE TABLE IF NOT EXISTS balance_history (
    id SERIAL PRIMARY KEY,
    balance DECIMAL(20, 8) NOT NULL,
    equity DECIMAL(20, 8) NOT NULL,
    available DECIMAL(20, 8) NOT NULL,
    locked DECIMAL(20, 8) DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_balance_history_timestamp ON balance_history(timestamp);

-- ==================== 创建视图：交易统计 ====================
CREATE OR REPLACE VIEW v_trading_statistics AS
SELECT
    symbol,
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END), 2) as avg_win,
    ROUND(AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END), 2) as avg_loss,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct
FROM trades
WHERE exit_time IS NOT NULL
GROUP BY symbol, strategy;

-- ==================== 初始化系统配置表 ====================
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT INTO system_config (key, value, description) VALUES
('system_version', '3.2.0', '系统版本'),
('initialized_at', NOW()::TEXT, '初始化时间'),
('default_exchange', 'binance', '默认交易所')
ON CONFLICT (key) DO NOTHING;

-- ==================== 授权 ====================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trader;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trader;
