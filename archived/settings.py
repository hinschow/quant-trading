"""
全局配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== 基础配置 ====================
PROJECT_NAME = "Quant Trading System v3.2"
VERSION = "3.2.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, paper, production

# ==================== 交易所配置 ====================
EXCHANGES = {
    "binance": {
        "api_key": os.getenv("BINANCE_API_KEY", ""),
        "api_secret": os.getenv("BINANCE_API_SECRET", ""),
        "testnet": ENVIRONMENT != "production",
        "options": {
            "defaultType": "spot",  # spot, future
            "adjustForTimeDifference": True,
        }
    },
    "okx": {
        "api_key": os.getenv("OKX_API_KEY", ""),
        "api_secret": os.getenv("OKX_API_SECRET", ""),
        "password": os.getenv("OKX_PASSWORD", ""),
        "testnet": ENVIRONMENT != "production",
    },
    "bybit": {
        "api_key": os.getenv("BYBIT_API_KEY", ""),
        "api_secret": os.getenv("BYBIT_API_SECRET", ""),
        "testnet": ENVIRONMENT != "production",
    }
}

# 默认交易所
DEFAULT_EXCHANGE = "binance"

# ==================== 交易对配置 ====================
TRADING_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
]

# ==================== 时间周期配置 ====================
TIMEFRAMES = {
    "primary": "1h",      # 主要交易周期
    "secondary": "4h",    # 次要确认周期
    "fast": "15m",        # 快速周期（可选）
}

# ==================== 数据库配置 ====================
DATABASE = {
    "postgres": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "quant_trading"),
        "user": os.getenv("POSTGRES_USER", "trader"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    },
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0)),
        "password": os.getenv("REDIS_PASSWORD", ""),
    }
}

# ==================== 账户配置 ====================
ACCOUNT = {
    "initial_balance": float(os.getenv("INITIAL_BALANCE", 10000)),  # USDT
    "currency": "USDT",
}

# ==================== 日志配置 ====================
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO"),  # DEBUG, INFO, WARNING, ERROR
    "file": "logs/trading.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 10,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# ==================== 监控配置 ====================
MONITORING = {
    "telegram": {
        "enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    },
    "prometheus": {
        "enabled": True,
        "port": int(os.getenv("PROMETHEUS_PORT", 8000)),
    },
    "email": {
        "enabled": False,
        "smtp_server": os.getenv("SMTP_SERVER", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "sender": os.getenv("EMAIL_SENDER", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "recipients": os.getenv("EMAIL_RECIPIENTS", "").split(","),
    }
}

# ==================== 回测配置 ====================
BACKTEST = {
    "start_date": "2022-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "commission": 0.0005,  # 0.05% Taker fee
    "slippage": 0.001,     # 0.1% 滑点
}

# ==================== 其他配置 ====================
# 数据更新频率（秒）
DATA_UPDATE_INTERVAL = 60

# API 请求重试次数
API_RETRY_TIMES = 3

# API 请求超时（秒）
API_TIMEOUT = 10

# 价格精度（小数位）
PRICE_PRECISION = 8

# 数量精度（小数位）
QUANTITY_PRECISION = 8
