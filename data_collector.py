"""
数据抓取模块 - 从交易所获取K线数据
不需要API key，使用公开接口
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """数据采集器 - 获取历史K线数据"""

    def __init__(
        self,
        exchange_name: str = 'binance',
        proxy: Optional[str] = None,
        market_type: str = 'spot'
    ):
        """
        初始化数据采集器

        Args:
            exchange_name: 交易所名称，默认 binance
            proxy: 代理地址，如 'http://127.0.0.1:7890'
            market_type: 市场类型，'spot' (现货) 或 'future' (合约)，默认 spot
        """
        self.exchange_name = exchange_name
        self.market_type = market_type

        config = {
            'enableRateLimit': True,
            'options': {'defaultType': market_type},  # 现货或合约市场
            'timeout': 30000,  # 30秒超时
        }

        # 如果提供代理，配置代理
        if proxy:
            config['proxies'] = {
                'http': proxy,
                'https': proxy,
            }
            logger.info(f"🔗 使用代理: {proxy}")

        # 尝试多个币安域名
        if exchange_name == 'binance':
            # 币安有多个备用域名
            for i in range(1, 5):
                try:
                    if i == 1:
                        self.exchange = ccxt.binance(config)
                    else:
                        config['hostname'] = f'api{i}.binance.com'
                        self.exchange = ccxt.binance(config)

                    # 测试连接
                    self.exchange.load_markets()
                    logger.info(f"✅ 初始化 {exchange_name} 数据采集器 (域名: {config.get('hostname', 'api.binance.com')})")
                    return
                except Exception as e:
                    if i < 4:
                        logger.warning(f"⚠️  连接失败，尝试备用域名...")
                        continue
                    else:
                        logger.error(f"❌ 所有币安域名都无法连接，请检查网络或配置代理")
                        raise
        else:
            self.exchange = getattr(ccxt, exchange_name)(config)
            logger.info(f"✅ 初始化 {exchange_name} 数据采集器")

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 500,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        获取OHLCV数据（开高低收量）

        Args:
            symbol: 交易对，如 'BTC/USDT'
            timeframe: 时间周期，如 '1m', '5m', '15m', '1h', '4h', '1d'
            limit: 获取条数，默认500
            since: 起始时间戳（毫秒），None表示最近数据

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            logger.info(f"📥 获取 {symbol} {timeframe} 数据，共 {limit} 条")

            # 获取K线数据
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )

            # 转换为DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # 转换时间戳为datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

            # 设置索引
            df.set_index('datetime', inplace=True)

            logger.info(f"✅ 成功获取 {len(df)} 条数据")
            logger.info(f"📅 时间范围: {df.index[0]} 至 {df.index[-1]}")

            return df

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            raise

    def fetch_recent_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        days: int = 30
    ) -> pd.DataFrame:
        """
        获取最近N天的数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            days: 天数

        Returns:
            DataFrame
        """
        # 计算需要的K线数量
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }

        minutes = timeframe_minutes.get(timeframe, 60)
        limit = int(days * 24 * 60 / minutes)

        # 限制最大1000条（交易所限制）
        limit = min(limit, 1000)

        return self.fetch_ohlcv(symbol, timeframe, limit)

    def get_supported_symbols(self, quote: str = 'USDT') -> List[str]:
        """
        获取支持的交易对列表

        Args:
            quote: 计价货币，默认 USDT

        Returns:
            交易对列表
        """
        try:
            markets = self.exchange.load_markets()
            symbols = [
                symbol for symbol in markets.keys()
                if symbol.endswith(f'/{quote}') and markets[symbol]['active']
            ]
            logger.info(f"✅ 找到 {len(symbols)} 个 {quote} 交易对")
            return sorted(symbols)
        except Exception as e:
            logger.error(f"❌ 获取交易对失败: {e}")
            return []

    def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易对

        Returns:
            当前价格
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"❌ 获取价格失败: {e}")
            return 0.0


if __name__ == '__main__':
    # 测试代码
    collector = DataCollector('binance')

    # 获取BTC/USDT最近500根1小时K线
    df = collector.fetch_ohlcv('BTC/USDT', '1h', 500)
    print("\n📊 数据预览:")
    print(df.tail(10))

    # 获取当前价格
    price = collector.get_current_price('BTC/USDT')
    print(f"\n💰 BTC/USDT 当前价格: ${price:,.2f}")

    # 获取支持的交易对
    symbols = collector.get_supported_symbols('USDT')
    print(f"\n📋 USDT交易对数量: {len(symbols)}")
    print("前10个:", symbols[:10])
