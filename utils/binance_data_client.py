"""
Binance数据客户端
用于获取资金费率和持仓量（作为Hyperliquid的备用数据源）
"""

import requests
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BinanceDataClient:
    """Binance数据采集客户端（备用数据源）"""

    def __init__(self, base_url: str = "https://fapi.binance.com"):
        """
        初始化Binance客户端

        Args:
            base_url: Binance Futures API基础URL
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/fapi/v1"

        # 交易对映射：标准化格式转换为Binance格式
        self.symbol_map = {
            'BTC/USDT': 'BTCUSDT',
            'ETH/USDT': 'ETHUSDT',
            'SOL/USDT': 'SOLUSDT',
            'BTCUSDT': 'BTCUSDT',
            'ETHUSDT': 'ETHUSDT',
            'SOLUSDT': 'SOLUSDT',
        }

        logger.info("✅ Binance数据客户端初始化完成")

    def _convert_symbol(self, symbol: str) -> str:
        """
        将标准格式转换为Binance格式

        Args:
            symbol: 标准格式的交易对（如 'BTC/USDT'）

        Returns:
            Binance格式的交易对（如 'BTCUSDT'）
        """
        return self.symbol_map.get(symbol, symbol.replace('/', ''))

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        获取Binance资金费率

        资金费率说明：
        - 正费率：多头支付空头（市场看多）
        - 负费率：空头支付多头（市场看空）
        - 每8小时结算一次（0:00, 8:00, 16:00 UTC）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            资金费率（小数形式），获取失败返回None
        """
        binance_symbol = self._convert_symbol(symbol)

        try:
            # Binance API: GET /fapi/v1/premiumIndex
            url = f"{self.api_url}/premiumIndex"
            params = {'symbol': binance_symbol}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'lastFundingRate' in data:
                funding_rate = float(data['lastFundingRate'])
                logger.debug(f"📊 Binance {symbol} 资金费率: {funding_rate:.4%}")
                return funding_rate
            else:
                logger.warning(f"⚠️  Binance未返回 {symbol} 的资金费率")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取Binance资金费率失败: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"❌ 解析Binance数据失败: {e}")
            return None

    def get_open_interest(self, symbol: str) -> Optional[float]:
        """
        获取Binance持仓量（OpenInterest）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            持仓量（USDT计价），获取失败返回None
        """
        binance_symbol = self._convert_symbol(symbol)

        try:
            # Binance API: GET /fapi/v1/openInterest
            url = f"{self.api_url}/openInterest"
            params = {'symbol': binance_symbol}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'openInterest' in data:
                # openInterest返回的是币本位数量，需要乘以价格转换为USDT
                oi_amount = float(data['openInterest'])

                # 获取当前价格
                price = self.get_mark_price(symbol)
                if price is None:
                    logger.warning(f"⚠️  无法获取 {symbol} 价格，无法计算持仓量")
                    return None

                oi_usdt = oi_amount * price
                logger.debug(f"📊 Binance {symbol} 持仓量: {oi_usdt:.2f} USDT")
                return oi_usdt
            else:
                logger.warning(f"⚠️  Binance未返回 {symbol} 的持仓量")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取Binance持仓量失败: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"❌ 解析Binance数据失败: {e}")
            return None

    def get_mark_price(self, symbol: str) -> Optional[float]:
        """
        获取Binance标记价格

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            标记价格，获取失败返回None
        """
        binance_symbol = self._convert_symbol(symbol)

        try:
            # Binance API: GET /fapi/v1/premiumIndex
            url = f"{self.api_url}/premiumIndex"
            params = {'symbol': binance_symbol}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'markPrice' in data:
                mark_price = float(data['markPrice'])
                return mark_price
            else:
                logger.warning(f"⚠️  Binance未返回 {symbol} 的标记价格")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取Binance标记价格失败: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"❌ 解析Binance数据失败: {e}")
            return None

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        获取Binance市场数据（资金费率 + OI + 价格）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            市场数据字典 {'funding_rate': float, 'open_interest': float, 'price': float, 'timestamp': float}
            获取失败返回None
        """
        try:
            funding_rate = self.get_funding_rate(symbol)
            if funding_rate is None:
                return None

            open_interest = self.get_open_interest(symbol)
            if open_interest is None:
                return None

            mark_price = self.get_mark_price(symbol)
            if mark_price is None:
                return None

            market_data = {
                'funding_rate': funding_rate,
                'open_interest': open_interest,
                'price': mark_price,
                'timestamp': time.time()
            }

            logger.debug(f"📊 Binance {symbol} 市场数据获取完成")
            return market_data

        except Exception as e:
            logger.error(f"❌ 获取Binance市场数据失败: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建客户端
    client = BinanceDataClient()

    # 测试获取资金费率
    print("\n" + "="*60)
    print("测试1：获取资金费率")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        funding_rate = client.get_funding_rate(symbol)
        if funding_rate is not None:
            print(f"{symbol:12} 资金费率: {funding_rate:7.4%}")

    # 测试获取持仓量
    print("\n" + "="*60)
    print("测试2：获取持仓量")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        oi = client.get_open_interest(symbol)
        if oi is not None:
            print(f"{symbol:12} 持仓量: ${oi:,.0f}")

    # 测试获取完整市场数据
    print("\n" + "="*60)
    print("测试3：获取完整市场数据")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        market_data = client.get_market_data(symbol)
        if market_data:
            print(f"{symbol:12} 费率:{market_data['funding_rate']:7.4%}  "
                  f"OI:${market_data['open_interest']:,.0f}  "
                  f"价格:${market_data['price']:,.2f}")
