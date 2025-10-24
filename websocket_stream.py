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
        self.proxy = proxy

        # 配置
        config = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # 现货市场
                'defaultMarket': 'spot'
            }
        }

        if proxy:
            config['proxies'] = {
                'http': proxy,
                'https': proxy
            }

        # 先尝试使用普通 ccxt（更稳定）
        try:
            exchange_class = getattr(ccxt, exchange_name)
            self.exchange = exchange_class(config)
            logger.info(f"✅ 初始化 {exchange_name} (轮询模式)")
            self.has_pro = False
        except AttributeError:
            raise ValueError(f"不支持的交易所: {exchange_name}")

        # 检查是否有 pro 版本可用
        try:
            exchange_class_pro = getattr(ccxt.pro, exchange_name)
            self.exchange_pro = exchange_class_pro(config)
            self.has_pro = True
            logger.info(f"✅ ccxt.pro 可用")
        except (AttributeError, ImportError):
            self.exchange_pro = None
            self.has_pro = False
            logger.info(f"ℹ️  ccxt.pro 不可用，将使用轮询模式")

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

        # 尝试使用 WebSocket（如果有 pro 版本）
        use_websocket = False

        if self.has_pro and self.exchange_pro:
            try:
                # 测试 WebSocket 是否真的支持
                test_ohlcv = await self.exchange_pro.watch_ohlcv(symbol, timeframe)
                use_websocket = True
                logger.info(f"✅ 使用 WebSocket 实时模式")
            except Exception as ws_error:
                if 'not supported' in str(ws_error).lower():
                    logger.info(f"ℹ️  WebSocket 不支持 OHLCV，使用轮询模式")
                    use_websocket = False
                else:
                    logger.warning(f"⚠️  WebSocket 测试失败: {ws_error}")
                    use_websocket = False

        try:
            if use_websocket:
                # WebSocket 模式
                logger.info(f"📡 开始 WebSocket 监听...")
                while self.running:
                    try:
                        ohlcv = await self.exchange_pro.watch_ohlcv(symbol, timeframe)

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
                logger.info(f"📊 轮询模式（每 {interval} 秒）")

                last_timestamp = 0

                while self.running:
                    try:
                        # 使用普通 ccxt exchange（现货市场）
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

    async def watch_ticker(
        self,
        symbol: str,
        callback: Optional[Callable] = None
    ):
        """
        监听实时ticker（价格、成交量等）

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        self.running = True

        logger.info(f"📡 开始监听 {symbol} 实时ticker")

        # 尝试 WebSocket ticker
        use_websocket = False

        if self.has_pro and self.exchange_pro:
            try:
                # 测试 ticker WebSocket
                test_ticker = await self.exchange_pro.watch_ticker(symbol)
                use_websocket = True
                logger.info(f"✅ 使用 ticker WebSocket")
            except Exception as e:
                if 'not supported' in str(e).lower():
                    logger.info(f"ℹ️  ticker WebSocket 不支持，使用轮询")
                    use_websocket = False
                else:
                    logger.warning(f"⚠️  ticker WebSocket 测试失败: {e}")
                    use_websocket = False

        try:
            if use_websocket:
                # WebSocket 模式（实时）
                logger.info(f"📡 ticker WebSocket 实时模式")
                while self.running:
                    try:
                        ticker = await self.exchange_pro.watch_ticker(symbol)

                        if ticker and callback:
                            await callback(ticker)

                    except Exception as e:
                        logger.error(f"❌ ticker WebSocket 错误: {e}")
                        await asyncio.sleep(5)
            else:
                # 轮询模式（快速轮询ticker）
                logger.info(f"📊 ticker 轮询模式（每 1 秒）")

                while self.running:
                    try:
                        ticker = self.exchange.fetch_ticker(symbol)

                        if ticker and callback:
                            await callback(ticker)

                        # ticker 轮询间隔：1秒
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"❌ ticker 轮询错误: {e}")
                        await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"❌ ticker 监听失败: {e}")
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

        # 关闭 pro 连接
        if self.exchange_pro and hasattr(self.exchange_pro, 'close'):
            try:
                await self.exchange_pro.close()
            except:
                pass

        # 关闭普通连接
        if hasattr(self.exchange, 'close'):
            try:
                await self.exchange.close()
            except:
                pass

        logger.info("🔌 连接已关闭")

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
