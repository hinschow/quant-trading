"""
WebSocket 数据流
实时接收交易所K线数据
"""

import ccxt
import asyncio
import logging
from typing import Callable, Optional, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketStream:
    """WebSocket 数据流管理器"""

    def __init__(self, exchange_name: str = 'binance', proxy: Optional[str] = None):
        """
        初始化WebSocket流

        Args:
            exchange_name: 交易所名称
            proxy: 代理地址
        """
        self.exchange_name = exchange_name

        # 初始化交易所（pro版本支持WebSocket）
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }

        if proxy:
            config['proxies'] = {
                'http': proxy,
                'https': proxy
            }

        try:
            # 使用 ccxt.pro 的异步WebSocket支持
            exchange_class = getattr(ccxt.pro, exchange_name)
            self.exchange = exchange_class(config)
            logger.info(f"✅ 初始化 {exchange_name} WebSocket")
        except AttributeError:
            # 如果不支持 pro，回退到普通轮询
            logger.warning(f"⚠️  {exchange_name} 不支持 WebSocket，使用轮询模式")
            exchange_class = getattr(ccxt, exchange_name)
            self.exchange = exchange_class(config)

        self.running = False
        self.callbacks: Dict[str, Callable] = {}

    async def watch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1m',
        callback: Optional[Callable] = None
    ):
        """
        监听K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            callback: 回调函数
        """
        self.running = True

        logger.info(f"📡 开始监听 {symbol} {timeframe} K线")

        # 尝试使用 WebSocket，失败则降级到轮询
        use_websocket = False

        try:
            if hasattr(self.exchange, 'watch_ohlcv'):
                # 测试 WebSocket 是否真的支持
                try:
                    test_ohlcv = await self.exchange.watch_ohlcv(symbol, timeframe)
                    use_websocket = True
                    logger.info(f"✅ 使用 WebSocket 模式")
                except Exception as ws_error:
                    if 'not supported' in str(ws_error):
                        logger.warning(f"⚠️  {self.exchange_name} 不支持 OHLCV WebSocket")
                        use_websocket = False
                    else:
                        raise
        except AttributeError:
            use_websocket = False

        if use_websocket:
            # WebSocket 模式
            logger.info(f"📡 WebSocket 实时模式")
            while self.running:
                try:
                    ohlcv = await self.exchange.watch_ohlcv(symbol, timeframe)

                    if ohlcv and len(ohlcv) > 0:
                        # 最新K线
                        latest = ohlcv[-1]
                        kline = self._format_kline(latest)

                        if callback:
                            await callback(kline)

                except Exception as e:
                    logger.error(f"❌ WebSocket 错误: {e}")
                    await asyncio.sleep(5)  # 错误后等待5秒重连

        else:
            # 轮询模式
            interval = self._get_poll_interval(timeframe)
            logger.info(f"📊 使用轮询模式（每 {interval} 秒更新）")

            last_timestamp = 0

            while self.running:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=1)

                    if ohlcv and len(ohlcv) > 0:
                        latest = ohlcv[-1]

                        # 只在新K线时触发回调
                        if latest[0] > last_timestamp:
                            last_timestamp = latest[0]
                            kline = self._format_kline(latest)

                            if callback:
                                await callback(kline)
                        else:
                            # 更新当前K线
                            kline = self._format_kline(latest)
                            if callback:
                                await callback(kline)

                    # 根据时间周期调整轮询间隔
                    await asyncio.sleep(interval)

                except Exception as e:
                    logger.error(f"❌ 轮询错误: {e}")
                    await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"❌ 监听失败: {e}")
            raise

        finally:
            await self.close()

    async def watch_trades(
        self,
        symbol: str,
        callback: Optional[Callable] = None
    ):
        """
        监听实时成交（可用于更频繁的价格更新）

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        self.running = True

        logger.info(f"📡 开始监听 {symbol} 实时成交")

        try:
            if hasattr(self.exchange, 'watch_trades'):
                while self.running:
                    try:
                        trades = await self.exchange.watch_trades(symbol)

                        if trades and len(trades) > 0:
                            for trade in trades:
                                if callback:
                                    await callback(trade)

                    except Exception as e:
                        logger.error(f"❌ WebSocket 错误: {e}")
                        await asyncio.sleep(5)
            else:
                logger.warning(f"⚠️  {self.exchange_name} 不支持实时成交流")

        except Exception as e:
            logger.error(f"❌ 监听失败: {e}")
            raise

        finally:
            await self.close()

    def _format_kline(self, ohlcv: list) -> Dict:
        """
        格式化K线数据

        Args:
            ohlcv: [timestamp, open, high, low, close, volume]

        Returns:
            格式化的K线字典
        """
        return {
            'timestamp': int(ohlcv[0]),
            'datetime': datetime.fromtimestamp(ohlcv[0] / 1000),
            'open': float(ohlcv[1]),
            'high': float(ohlcv[2]),
            'low': float(ohlcv[3]),
            'close': float(ohlcv[4]),
            'volume': float(ohlcv[5])
        }

    def _get_poll_interval(self, timeframe: str) -> int:
        """
        获取轮询间隔（秒）

        Args:
            timeframe: 时间周期

        Returns:
            轮询间隔秒数
        """
        intervals = {
            '1m': 5,      # 1分钟K线，每5秒轮询一次
            '5m': 10,     # 5分钟K线，每10秒轮询一次
            '15m': 30,    # 15分钟K线，每30秒轮询一次
            '30m': 60,    # 30分钟K线，每分钟轮询一次
            '1h': 60,     # 1小时K线，每分钟轮询一次
            '4h': 300,    # 4小时K线，每5分钟轮询一次
            '1d': 600     # 日线，每10分钟轮询一次
        }
        return intervals.get(timeframe, 60)

    async def close(self):
        """关闭连接"""
        self.running = False
        if hasattr(self.exchange, 'close'):
            await self.exchange.close()
        logger.info("🔌 WebSocket 连接已关闭")

    def stop(self):
        """停止监听"""
        self.running = False
        logger.info("⏹️  停止监听")


# 测试代码
if __name__ == '__main__':
    async def on_kline(kline):
        print(f"📊 新K线: {kline['datetime']}, "
              f"开: {kline['open']:.2f}, "
              f"高: {kline['high']:.2f}, "
              f"低: {kline['low']:.2f}, "
              f"收: {kline['close']:.2f}, "
              f"量: {kline['volume']:.2f}")

    async def main():
        stream = WebSocketStream('binance', proxy='http://127.0.0.1:7890')

        try:
            await stream.watch_ohlcv('BTC/USDT', '1m', on_kline)
        except KeyboardInterrupt:
            print("\n⏹️  用户中断")
        finally:
            await stream.close()

    # 运行
    asyncio.run(main())
