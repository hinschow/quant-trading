"""
交易所交易对信息获取模块
从 Binance API 获取价格精度、数量精度等信息
"""

import ccxt
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ExchangeInfo:
    """交易所信息缓存器"""

    def __init__(self, exchange_name: str = 'binance', proxy: Optional[str] = None):
        """
        初始化交易所信息

        Args:
            exchange_name: 交易所名称
            proxy: 代理地址
        """
        self.exchange_name = exchange_name
        self.proxy = proxy

        # 缓存
        self._symbol_info_cache = {}  # {symbol: info}
        self._loaded = False

        # 初始化交易所
        config = {
            'enableRateLimit': True,
            'timeout': 30000,
        }

        if proxy:
            config['proxies'] = {
                'http': proxy,
                'https': proxy,
            }

        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class(config)

    def _load_markets(self):
        """加载市场信息（懒加载）"""
        if self._loaded:
            return

        try:
            logger.info("📡 正在加载交易所市场信息...")
            self.exchange.load_markets()
            self._loaded = True
            logger.info(f"✅ 已加载 {len(self.exchange.markets)} 个交易对信息")
        except Exception as e:
            logger.error(f"❌ 加载市场信息失败: {e}")
            self._loaded = False

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        获取交易对信息

        Args:
            symbol: 交易对（如 BTC/USDT:USDT）

        Returns:
            交易对信息字典，包含精度等信息
        """
        # 检查缓存
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]

        # 确保市场已加载
        self._load_markets()

        try:
            if symbol in self.exchange.markets:
                market = self.exchange.markets[symbol]

                # 提取关键信息
                info = {
                    'symbol': symbol,
                    'price_precision': market.get('precision', {}).get('price', 2),
                    'amount_precision': market.get('precision', {}).get('amount', 3),
                    'min_amount': market.get('limits', {}).get('amount', {}).get('min', 0.001),
                    'min_cost': market.get('limits', {}).get('cost', {}).get('min', 10),
                    'type': market.get('type', 'spot'),  # spot, future, swap
                    'active': market.get('active', True),
                }

                # 缓存
                self._symbol_info_cache[symbol] = info

                logger.debug(f"✅ {symbol} 价格精度: {info['price_precision']} 位")

                return info
            else:
                logger.warning(f"⚠️  未找到交易对: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取交易对信息失败 {symbol}: {e}")
            return None

    def get_price_precision(self, symbol: str) -> int:
        """
        获取价格精度（小数位数）

        Args:
            symbol: 交易对

        Returns:
            价格精度（默认2位）
        """
        info = self.get_symbol_info(symbol)
        if info:
            return info['price_precision']
        else:
            # 默认精度（备用）
            logger.warning(f"⚠️  {symbol} 使用默认精度 2 位")
            return 2

    def get_amount_precision(self, symbol: str) -> int:
        """
        获取数量精度

        Args:
            symbol: 交易对

        Returns:
            数量精度（默认3位）
        """
        info = self.get_symbol_info(symbol)
        if info:
            return info['amount_precision']
        else:
            return 3

    def format_price(self, symbol: str, price: float) -> str:
        """
        根据交易对规则格式化价格

        Args:
            symbol: 交易对
            price: 价格

        Returns:
            格式化后的价格字符串
        """
        precision = self.get_price_precision(symbol)

        # 使用千分位分隔符（价格>1000时）
        if price >= 1000:
            return f"{price:,.{precision}f}"
        else:
            return f"{price:.{precision}f}"

    def format_amount(self, symbol: str, amount: float) -> str:
        """
        根据交易对规则格式化数量

        Args:
            symbol: 交易对
            amount: 数量

        Returns:
            格式化后的数量字符串
        """
        precision = self.get_amount_precision(symbol)

        if amount >= 1000:
            return f"{amount:,.{precision}f}"
        else:
            return f"{amount:.{precision}f}"


# ==================== 全局实例（单例模式） ====================

_exchange_info_instances = {}  # {(exchange, proxy): ExchangeInfo}


def get_exchange_info(exchange: str = 'binance', proxy: Optional[str] = None) -> ExchangeInfo:
    """
    获取交易所信息实例（单例）

    Args:
        exchange: 交易所名称
        proxy: 代理地址

    Returns:
        ExchangeInfo实例
    """
    key = (exchange, proxy)

    if key not in _exchange_info_instances:
        _exchange_info_instances[key] = ExchangeInfo(exchange, proxy)

    return _exchange_info_instances[key]


# ==================== 便捷函数 ====================

def get_price_precision(symbol: str, exchange: str = 'binance', proxy: Optional[str] = None) -> int:
    """
    快速获取价格精度

    Args:
        symbol: 交易对
        exchange: 交易所
        proxy: 代理

    Returns:
        价格精度
    """
    info = get_exchange_info(exchange, proxy)
    return info.get_price_precision(symbol)


def format_price(symbol: str, price: float, exchange: str = 'binance', proxy: Optional[str] = None) -> str:
    """
    快速格式化价格

    Args:
        symbol: 交易对
        price: 价格
        exchange: 交易所
        proxy: 代理

    Returns:
        格式化的价格字符串
    """
    info = get_exchange_info(exchange, proxy)
    return info.format_price(symbol, price)


if __name__ == '__main__':
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    # 测试获取精度
    info = ExchangeInfo('binance')

    symbols = [
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        '1000RATS/USDT:USDT',
        'SUI/USDT:USDT',
    ]

    print("\n=== 交易对精度信息 ===")
    for symbol in symbols:
        precision = info.get_price_precision(symbol)
        test_price = 123.456789
        formatted = info.format_price(symbol, test_price)
        print(f"{symbol:25} | 精度: {precision} 位 | 示例: {formatted}")
