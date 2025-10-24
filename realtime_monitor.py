#!/usr/bin/env python3
"""
实时交易信号监控
WebSocket 实时监听 + 信号生成
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import Dict
import logging

from websocket_stream import WebSocketStream
from realtime_engine import RealtimeSignalEngine
from data_collector import DataCollector

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING及以上
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """实时监控器"""

    def __init__(
        self,
        symbol: str,
        timeframe: str = '1h',
        exchange: str = 'binance',
        proxy: str = None
    ):
        """
        初始化监控器

        Args:
            symbol: 交易对
            timeframe: 时间周期
            exchange: 交易所
            proxy: 代理地址
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange_name = exchange
        self.proxy = proxy

        # WebSocket 流
        self.stream = WebSocketStream(exchange, proxy)

        # 实时信号引擎
        self.engine = RealtimeSignalEngine(symbol, timeframe)

        # 设置信号变化回调
        self.engine.on_signal_change = self.on_signal_change

        # 统计
        self.kline_count = 0
        self.signal_changes = 0
        self.start_time = datetime.now()

        print(f"\n{'='*80}")
        print(f"🚀 实时交易信号监控")
        print(f"{'='*80}")
        print(f"交易对: {symbol}")
        print(f"周期: {timeframe}")
        print(f"交易所: {exchange}")
        print(f"代理: {proxy or '无'}")
        print(f"{'='*80}\n")

    async def start(self):
        """启动监控"""
        try:
            # 1. 获取历史数据初始化
            print(f"📥 正在获取历史数据...")
            collector = DataCollector(self.exchange_name, self.proxy)
            historical_df = collector.fetch_ohlcv(self.symbol, self.timeframe, limit=500)

            # 2. 初始化引擎
            print(f"⚙️  正在初始化信号引擎...")
            self.engine.initialize(historical_df)

            # 3. 显示初始信号
            self._display_initial_signal()

            # 4. 开始WebSocket监听
            print(f"\n📡 开始实时监听...")
            print(f"{'='*80}\n")

            await self.stream.watch_ohlcv(
                self.symbol,
                self.timeframe,
                self.on_kline
            )

        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断")
        except Exception as e:
            print(f"\n\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

    async def on_kline(self, kline: Dict):
        """
        K线回调

        Args:
            kline: K线数据
        """
        self.kline_count += 1

        # 传递给引擎处理
        await self.engine.on_kline(kline)

        # 显示实时状态
        self._display_realtime_status(kline)

    def on_signal_change(self, signal: Dict):
        """
        信号变化回调

        Args:
            signal: 新信号
        """
        self.signal_changes += 1

        print(f"\n{'='*80}")
        print(f"🔔 信号变化！({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"{'='*80}")

        self._display_signal(signal)

        print(f"{'='*80}\n")

    def _display_initial_signal(self):
        """显示初始信号"""
        signal = self.engine.get_signal()

        if not signal:
            print(f"⚠️  暂无信号")
            return

        print(f"\n{'='*80}")
        print(f"📊 初始信号")
        print(f"{'='*80}")

        self._display_signal(signal)

        print(f"{'='*80}")

    def _display_signal(self, signal: Dict):
        """
        显示信号详情

        Args:
            signal: 信号字典
        """
        market_data = signal['market_data']
        action = signal['action']
        strength = signal['strength']
        regime = signal['market_regime']

        # 市场状态描述
        regime_desc = {
            'STRONG_TREND': '🔥 强趋势',
            'TREND': '📈 趋势',
            'RANGE': '↔️  震荡',
            'SQUEEZE': '💥 挤压',
            'NEUTRAL': '😐 中性'
        }

        # 操作图标
        action_icon = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '⚪'
        }

        print(f"\n【市场状态】")
        print(f"  {regime_desc.get(regime, regime)}")
        print(f"  策略: {signal['type']}")

        print(f"\n【价格信息】")
        print(f"  当前价格: ${market_data['price']:,.2f}")
        print(f"  EMA50:    ${market_data['ema_50']:,.2f}")
        print(f"  EMA200:   ${market_data['ema_200']:,.2f}")

        print(f"\n【技术指标】")
        print(f"  RSI:  {market_data['rsi']:.1f}")
        print(f"  MACD: {market_data['macd']:.2f}")
        print(f"  ADX:  {market_data['adx']:.1f}")
        print(f"  BBW:  {market_data['bbw']:.4f}")

        print(f"\n【交易信号】")
        print(f"  {action_icon.get(action, action)} 操作: {action}")
        print(f"  强度: {strength}/100 {'█' * (strength // 10)}{'░' * (10 - strength // 10)}")

        if signal['reasons']:
            print(f"\n  理由:")
            for reason in signal['reasons']:
                print(f"    • {reason}")

        # 建议
        if action == 'BUY' and strength >= 60:
            price = market_data['price']
            print(f"\n【建议】")
            print(f"  ✅ 考虑买入")
            print(f"  📍 入场: ${price:,.2f}")
            print(f"  🛡️ 止损: ${price * 0.97:,.2f} (-3%)")
            print(f"  🎯 目标: ${price * 1.05:,.2f} (+5%)")

        elif action == 'SELL' and strength >= 60:
            price = market_data['price']
            print(f"\n【建议】")
            print(f"  ⚠️  考虑卖出")
            print(f"  📍 出场: ${price:,.2f}")
            print(f"  🛡️ 止损: ${price * 1.03:,.2f} (+3%)")
            print(f"  🎯 目标: ${price * 0.95:,.2f} (-5%)")

        else:
            print(f"\n【建议】")
            print(f"  ⚪ 观望")

    def _display_realtime_status(self, kline: Dict):
        """
        显示实时状态（单行更新）

        Args:
            kline: K线数据
        """
        if not self.engine.is_ready():
            return

        stats = self.engine.get_statistics()
        signal = self.engine.get_signal()

        if not signal:
            return

        # 构建状态行
        action = signal['action']
        strength = signal['strength']
        regime = signal['market_regime']

        action_icon = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(action, action)
        regime_emoji = {'STRONG_TREND': '🔥', 'TREND': '📈', 'RANGE': '↔️', 'SQUEEZE': '💥', 'NEUTRAL': '😐'}.get(regime, '📊')

        status_line = (
            f"\r{datetime.now().strftime('%H:%M:%S')} | "
            f"价格: ${kline['close']:>10,.2f} | "
            f"{regime_emoji} {regime:<12} | "
            f"{action_icon} {action:<4} | "
            f"强度: {strength:>3}/100 | "
            f"K线: {self.kline_count:>5} | "
            f"信号变化: {self.signal_changes}"
        )

        # 更新状态行（不换行）
        print(status_line, end='', flush=True)

    async def cleanup(self):
        """清理资源"""
        print(f"\n\n{'='*80}")
        print(f"📊 监控统计")
        print(f"{'='*80}")

        runtime = (datetime.now() - self.start_time).total_seconds()
        print(f"运行时间: {runtime:.0f} 秒")
        print(f"接收K线: {self.kline_count}")
        print(f"信号变化: {self.signal_changes}")

        print(f"{'='*80}")
        print(f"👋 再见！")

        await self.stream.close()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='实时交易信号监控',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监听BTC/USDT 1小时K线
  python realtime_monitor.py BTC/USDT -t 1h --proxy http://127.0.0.1:7890

  # 监听ETH/USDT 15分钟K线
  python realtime_monitor.py ETH/USDT -t 15m

  # 监听多个交易对（需要多个终端窗口）
  python realtime_monitor.py BTC/USDT --proxy http://127.0.0.1:7890 &
  python realtime_monitor.py ETH/USDT --proxy http://127.0.0.1:7890 &
        """
    )

    parser.add_argument('symbol', help='交易对，如 BTC/USDT')
    parser.add_argument('-t', '--timeframe', default='1h',
                        help='时间周期 (1m, 5m, 15m, 1h, 4h, 1d), 默认: 1h')
    parser.add_argument('-e', '--exchange', default='binance',
                        help='交易所, 默认: binance')
    parser.add_argument('--proxy', help='代理地址，如 http://127.0.0.1:7890')

    args = parser.parse_args()

    # 创建监控器
    monitor = RealtimeMonitor(
        symbol=args.symbol,
        timeframe=args.timeframe,
        exchange=args.exchange,
        proxy=args.proxy
    )

    # 启动
    await monitor.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
        sys.exit(0)
