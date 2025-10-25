"""
市场情绪指标模块
获取资金费率、持仓量等情绪数据
"""

import ccxt
import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketSentiment:
    """市场情绪数据获取器（带智能缓存）"""

    def __init__(self, exchange_name: str = 'binance', proxy: Optional[str] = None):
        """
        初始化市场情绪数据获取器

        Args:
            exchange_name: 交易所名称
            proxy: 代理地址
        """
        self.exchange_name = exchange_name

        # 初始化交易所（用于合约数据）
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'future'},
            'timeout': 30000,
        }

        if proxy:
            config['proxies'] = {
                'http': proxy,
                'https': proxy,
            }

        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class(config)

        # 缓存机制（减少API调用）
        self.funding_cache = {}  # {symbol: (rate, timestamp)}
        self.oi_cache = {}       # {symbol: (oi_data, timestamp)}

        # 缓存TTL（秒）
        self.funding_ttl = 8 * 3600  # 8小时（资金费率每8小时更新一次）
        self.oi_ttl = 5 * 60         # 5分钟（OI数据缓存5分钟）

        logger.info(f"✅ 市场情绪模块初始化完成: {exchange_name} (已启用智能缓存)")

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        获取当前资金费率（带缓存优化）

        资金费率解读：
        - > 0.1%: 多头极度FOMO，顶部信号
        - > 0.05%: 多头强势，注意回调
        - -0.05% ~ 0.05%: 中性
        - < -0.05%: 空头极度恐慌，底部信号

        Args:
            symbol: 交易对（如 BTC/USDT:USDT）

        Returns:
            资金费率（百分比，如 0.01 表示 0.01%）
        """
        try:
            # 检查是否为合约交易对
            if ':' not in symbol:
                logger.debug(f"⚠️  {symbol} 是现货市场，无资金费率")
                return None

            # 检查缓存（资金费率每8小时更新一次）
            if symbol in self.funding_cache:
                rate, timestamp = self.funding_cache[symbol]
                age = time.time() - timestamp

                if age < self.funding_ttl:
                    logger.debug(f"📦 使用缓存的资金费率: {symbol} ({rate:.4f}%, 缓存时长: {age/60:.1f}分钟)")
                    return rate

            # 缓存过期或不存在，重新获取
            logger.debug(f"🔄 从API更新资金费率: {symbol}")
            funding_rate = self.exchange.fetch_funding_rate(symbol)

            if funding_rate and 'fundingRate' in funding_rate:
                rate = float(funding_rate['fundingRate']) * 100  # 转为百分比

                # 更新缓存
                self.funding_cache[symbol] = (rate, time.time())

                logger.debug(f"📊 {symbol} 资金费率: {rate:.4f}% (已缓存)")
                return rate
            else:
                logger.warning(f"⚠️  无法获取 {symbol} 资金费率")
                return None

        except Exception as e:
            logger.error(f"❌ 获取资金费率失败 {symbol}: {e}")
            return None

    def get_open_interest(self, symbol: str) -> Optional[Dict]:
        """
        获取持仓量（OI）及变化（带缓存优化）

        持仓量解读：
        - OI增加 + 价格上涨 = 真突破（新多头进场）
        - OI减少 + 价格上涨 = 假突破（空头止损）
        - OI增加 + 价格下跌 = 真下跌（新空头进场）
        - OI减少 + 价格下跌 = 假下跌（多头止损）

        Args:
            symbol: 交易对（如 BTC/USDT:USDT）

        Returns:
            {
                'oi': 当前持仓量,
                'oi_value': 持仓量价值(USDT),
                'oi_change_1h': 1小时变化率(%),
                'oi_change_24h': 24小时变化率(%)
            }
        """
        try:
            # 检查是否为合约交易对
            if ':' not in symbol:
                logger.debug(f"⚠️  {symbol} 是现货市场，无持仓量")
                return None

            # 检查缓存（OI数据缓存5分钟）
            if symbol in self.oi_cache:
                oi_data, timestamp = self.oi_cache[symbol]
                age = time.time() - timestamp

                if age < self.oi_ttl:
                    logger.debug(f"📦 使用缓存的OI数据: {symbol} (缓存时长: {age:.0f}秒)")
                    return oi_data

            # 缓存过期或不存在，重新获取
            logger.debug(f"🔄 从API更新持仓量: {symbol}")

            # 获取当前持仓量
            current_oi = self.exchange.fetch_open_interest(symbol)

            if not current_oi or 'openInterestAmount' not in current_oi:
                logger.warning(f"⚠️  无法获取 {symbol} 持仓量")
                return None

            oi_amount = float(current_oi['openInterestAmount'])
            oi_value = float(current_oi.get('openInterestValue', 0))

            # 尝试获取历史持仓量计算变化率
            oi_change_1h = self._calculate_oi_change(symbol, hours=1)
            oi_change_24h = self._calculate_oi_change(symbol, hours=24)

            result = {
                'oi': oi_amount,
                'oi_value': oi_value,
                'oi_change_1h': oi_change_1h,
                'oi_change_24h': oi_change_24h,
            }

            # 更新缓存
            self.oi_cache[symbol] = (result, time.time())

            logger.debug(f"📊 {symbol} OI: {oi_amount:.0f}, 24h变化: {oi_change_24h:.1f}% (已缓存)")

            return result

        except Exception as e:
            logger.error(f"❌ 获取持仓量失败 {symbol}: {e}")
            return None

    def _calculate_oi_change(self, symbol: str, hours: int = 24) -> Optional[float]:
        """
        计算持仓量变化率

        Args:
            symbol: 交易对
            hours: 时间范围（小时）

        Returns:
            变化率（百分比）
        """
        try:
            # 获取历史持仓量（如果交易所支持）
            # 注意：不是所有交易所都支持历史OI查询
            # Binance支持通过fetch_open_interest_history

            if hasattr(self.exchange, 'fetch_open_interest_history'):
                since = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)

                oi_history = self.exchange.fetch_open_interest_history(
                    symbol,
                    timeframe='1h',
                    since=since,
                    limit=hours + 1
                )

                if oi_history and len(oi_history) >= 2:
                    old_oi = float(oi_history[0]['openInterestAmount'])
                    new_oi = float(oi_history[-1]['openInterestAmount'])

                    if old_oi > 0:
                        change_pct = ((new_oi - old_oi) / old_oi) * 100
                        return change_pct

            return None

        except Exception as e:
            logger.debug(f"⚠️  无法计算OI变化 {symbol}: {e}")
            return None

    def get_long_short_ratio(self, symbol: str) -> Optional[Dict]:
        """
        获取多空比（散户账户比例）

        多空比解读：
        - > 2.0: 散户极度看多，可能见顶
        - > 1.5: 散户偏多
        - 0.5 ~ 1.5: 中性
        - < 0.5: 散户极度看空，可能见底

        Args:
            symbol: 交易对（如 BTC/USDT:USDT）

        Returns:
            {
                'long_account': 多头账户比例(%),
                'short_account': 空头账户比例(%),
                'long_short_ratio': 多空比
            }
        """
        try:
            # 检查是否为合约交易对
            if ':' not in symbol:
                logger.debug(f"⚠️  {symbol} 是现货市场，无多空比")
                return None

            # 注意：这个功能需要特定的API
            # Binance有专门的endpoints: /futures/data/topLongShortAccountRatio
            # 但ccxt可能不直接支持，需要使用exchange.publicGetFuturesData...

            # 由于API限制，这里先返回None
            # 如果需要实现，需要直接调用REST API
            logger.debug(f"⚠️  多空比数据需要专门API，暂未实现")
            return None

        except Exception as e:
            logger.error(f"❌ 获取多空比失败 {symbol}: {e}")
            return None

    def get_sentiment_summary(self, symbol: str) -> Dict:
        """
        获取完整的市场情绪摘要

        Args:
            symbol: 交易对

        Returns:
            情绪数据字典
        """
        sentiment = {}

        # 获取资金费率
        funding_rate = self.get_funding_rate(symbol)
        if funding_rate is not None:
            sentiment['funding_rate'] = funding_rate
            sentiment['funding_signal'] = self._interpret_funding_rate(funding_rate)

        # 获取持仓量
        oi_data = self.get_open_interest(symbol)
        if oi_data:
            sentiment.update(oi_data)
            sentiment['oi_signal'] = self._interpret_oi_change(
                oi_data.get('oi_change_24h')
            )

        # 获取多空比
        ls_ratio = self.get_long_short_ratio(symbol)
        if ls_ratio:
            sentiment.update(ls_ratio)

        return sentiment

    @staticmethod
    def _interpret_funding_rate(rate: float) -> str:
        """解读资金费率"""
        if rate > 0.1:
            return 'EXTREME_LONG'  # 极度看多
        elif rate > 0.05:
            return 'BULLISH'  # 偏多
        elif rate < -0.05:
            return 'EXTREME_SHORT'  # 极度看空
        elif rate < -0.02:
            return 'BEARISH'  # 偏空
        else:
            return 'NEUTRAL'  # 中性

    @staticmethod
    def _interpret_oi_change(change_pct: Optional[float]) -> str:
        """解读持仓量变化"""
        if change_pct is None:
            return 'UNKNOWN'

        if change_pct > 15:
            return 'STRONG_INCREASE'  # 强烈增加
        elif change_pct > 5:
            return 'INCREASE'  # 增加
        elif change_pct < -15:
            return 'STRONG_DECREASE'  # 强烈减少
        elif change_pct < -5:
            return 'DECREASE'  # 减少
        else:
            return 'STABLE'  # 稳定

    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        current_time = time.time()

        # 统计资金费率缓存
        funding_valid = 0
        funding_expired = 0
        for symbol, (rate, timestamp) in self.funding_cache.items():
            if current_time - timestamp < self.funding_ttl:
                funding_valid += 1
            else:
                funding_expired += 1

        # 统计OI缓存
        oi_valid = 0
        oi_expired = 0
        for symbol, (data, timestamp) in self.oi_cache.items():
            if current_time - timestamp < self.oi_ttl:
                oi_valid += 1
            else:
                oi_expired += 1

        return {
            'funding_rate': {
                'valid': funding_valid,
                'expired': funding_expired,
                'total': funding_valid + funding_expired,
                'ttl_hours': self.funding_ttl / 3600,
            },
            'open_interest': {
                'valid': oi_valid,
                'expired': oi_expired,
                'total': oi_valid + oi_expired,
                'ttl_minutes': self.oi_ttl / 60,
            }
        }

    def clear_cache(self, symbol: Optional[str] = None):
        """
        清除缓存

        Args:
            symbol: 如果指定，只清除该交易对的缓存；否则清除全部
        """
        if symbol:
            # 清除指定交易对的缓存
            if symbol in self.funding_cache:
                del self.funding_cache[symbol]
                logger.info(f"🗑️  已清除 {symbol} 的资金费率缓存")

            if symbol in self.oi_cache:
                del self.oi_cache[symbol]
                logger.info(f"🗑️  已清除 {symbol} 的OI缓存")
        else:
            # 清除所有缓存
            funding_count = len(self.funding_cache)
            oi_count = len(self.oi_cache)

            self.funding_cache.clear()
            self.oi_cache.clear()

            logger.info(f"🗑️  已清除全部缓存 (资金费率: {funding_count}, OI: {oi_count})")


# 便捷函数
def get_funding_rate(symbol: str, exchange: str = 'binance', proxy: Optional[str] = None) -> Optional[float]:
    """
    快速获取资金费率

    Args:
        symbol: 交易对
        exchange: 交易所
        proxy: 代理

    Returns:
        资金费率（百分比）
    """
    sentiment = MarketSentiment(exchange, proxy)
    return sentiment.get_funding_rate(symbol)


def get_open_interest(symbol: str, exchange: str = 'binance', proxy: Optional[str] = None) -> Optional[Dict]:
    """
    快速获取持仓量

    Args:
        symbol: 交易对
        exchange: 交易所
        proxy: 代理

    Returns:
        持仓量数据
    """
    sentiment = MarketSentiment(exchange, proxy)
    return sentiment.get_open_interest(symbol)


if __name__ == '__main__':
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    sentiment = MarketSentiment('binance')

    # 测试资金费率
    print("\n=== 测试资金费率 ===")
    funding = sentiment.get_funding_rate('BTC/USDT:USDT')
    print(f"BTC资金费率: {funding}%")

    # 测试持仓量
    print("\n=== 测试持仓量 ===")
    oi = sentiment.get_open_interest('BTC/USDT:USDT')
    print(f"BTC持仓量: {oi}")

    # 测试完整摘要
    print("\n=== 市场情绪摘要 ===")
    summary = sentiment.get_sentiment_summary('BTC/USDT:USDT')
    for key, value in summary.items():
        print(f"{key}: {value}")
