#!/usr/bin/env python3
"""
多币种监控系统
同时监控多个交易对，自动保存买卖信号
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import List, Dict
import logging

from websocket_stream import WebSocketStream
from realtime_engine import RealtimeSignalEngine
from data_collector import DataCollector
from utils.signal_logger import SignalLogger

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiCoinMonitor:
    """多币种监控器"""

    def __init__(
        self,
        symbols: List[str],
        timeframe: str = '15m',
        exchange: str = 'binance',
        proxy: str = None,
        market_type: str = 'spot'
    ):
        """
        初始化多币种监控器

        Args:
            symbols: 交易对列表
            timeframe: K线周期
            exchange: 交易所
            proxy: 代理地址
            market_type: 市场类型，'spot' (现货) 或 'future' (合约)
        """
        self.symbols = symbols
        self.timeframe = timeframe
        self.exchange_name = exchange
        self.proxy = proxy
        self.market_type = market_type

        # 每个币种的监控组件
        self.monitors = {}
        self.engines = {}
        self.streams = {}

        # 信号记录器
        self.logger = SignalLogger()

        # 最新价格
        self.latest_prices = {}
        self.latest_signals = {}

        # 统计
        self.signal_counts = {symbol: 0 for symbol in symbols}
        self.start_time = datetime.now()

        # 市场类型说明
        market_name = {'spot': '现货', 'future': '合约/永续'}[market_type]

        print(f"\n{'='*80}")
        print(f"🚀 多币种交易信号监控系统")
        print(f"{'='*80}")
        print(f"监控币种: {', '.join(symbols)}")
        print(f"市场类型: {market_name} ({market_type})")
        print(f"时间周期: {timeframe}")
        print(f"交易所: {exchange}")
        print(f"代理: {proxy or '无'}")
        print(f"{'='*80}\n")

    async def start(self):
        """启动多币种监控"""
        try:
            # 1. 为每个币种初始化组件
            print(f"📥 正在初始化各币种数据...\n")

            for symbol in self.symbols:
                await self._init_symbol(symbol)

            print(f"\n📡 开始监控所有币种...")
            print(f"{'='*80}\n")

            # 显示初始状态
            self._display_all_status()

            # 2. 启动所有币种的监控流
            tasks = []
            for symbol in self.symbols:
                task = self._monitor_symbol(symbol)
                tasks.append(task)

            # 3. 定期显示状态
            tasks.append(self._periodic_status_update())

            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断")
        except Exception as e:
            print(f"\n\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

    async def _init_symbol(self, symbol: str):
        """初始化单个币种"""
        try:
            print(f"  {symbol}: 获取历史数据...", end='', flush=True)

            # 获取历史数据
            collector = DataCollector(self.exchange_name, self.proxy, self.market_type)
            historical_df = collector.fetch_ohlcv(symbol, self.timeframe, limit=500)

            # 创建信号引擎
            engine = RealtimeSignalEngine(symbol, self.timeframe)
            engine.initialize(historical_df)

            # 设置信号变化回调
            engine.on_signal_change = lambda sig: self._on_signal_change(symbol, sig)

            # 创建数据流
            stream = WebSocketStream(self.exchange_name, self.proxy, self.market_type)

            # 保存组件
            self.engines[symbol] = engine
            self.streams[symbol] = stream

            # 获取初始信号
            signal = engine.get_signal()
            self.latest_signals[symbol] = signal

            print(f" ✅ 完成")

        except Exception as e:
            print(f" ❌ 失败: {e}")
            logger.error(f"初始化 {symbol} 失败: {e}")

    async def _monitor_symbol(self, symbol: str):
        """监控单个币种"""
        try:
            stream = self.streams.get(symbol)
            engine = self.engines.get(symbol)

            if not stream or not engine:
                return

            # 监听K线数据
            async def on_kline(kline):
                await engine.on_kline(kline)
                # 更新最新信号
                self.latest_signals[symbol] = engine.get_signal()

            await stream.watch_ohlcv(symbol, self.timeframe, on_kline)

        except Exception as e:
            logger.error(f"监控 {symbol} 错误: {e}")

    def _on_signal_change(self, symbol: str, signal: Dict):
        """
        信号变化回调

        Args:
            symbol: 交易对
            signal: 新信号
        """
        # 记录信号
        self.logger.log_signal(symbol, self.timeframe, signal, self.exchange_name)
        self.signal_counts[symbol] += 1

        # 显示信号提醒
        self._display_signal_alert(symbol, signal)

    def _display_signal_alert(self, symbol: str, signal: Dict):
        """显示信号提醒"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        action = signal['action']
        strength = signal['strength']
        trading_plan = signal.get('trading_plan', {})

        # 操作图标
        action_icon = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}[action]

        print(f"\n{'='*80}")
        print(f"🔔 {action_icon} 新信号！ - {symbol}")
        print(f"{'='*80}")
        print(f"时间: {timestamp}")
        print(f"操作: {action} (强度: {strength}/100)")

        if action != 'HOLD' and trading_plan.get('entry_price'):
            entry = trading_plan['entry_price']
            tp = trading_plan['take_profit_price']
            sl = trading_plan['stop_loss_price']

            print(f"\n📋 交易计划:")
            if action == 'BUY':
                print(f"  🟢 买入: ${entry:.2f}")
                print(f"  🎯 止盈: ${tp:.2f} (+{trading_plan['take_profit_pct']:.1f}%)")
                print(f"  🛑 止损: ${sl:.2f} (-{trading_plan['stop_loss_pct']:.1f}%)")
            else:
                print(f"  🔴 卖出: ${entry:.2f}")
                print(f"  🎯 止盈: ${tp:.2f}")
                print(f"  🛑 止损: ${sl:.2f}")

        if signal.get('reasons'):
            print(f"\n理由:")
            for reason in signal['reasons']:
                print(f"  • {reason}")

        print(f"{'='*80}\n")

        # 提示已保存
        print(f"💾 信号已保存到日志文件\n")

    def _display_all_status(self):
        """显示所有币种的当前状态"""
        print(f"\n{'─'*80}")
        print(f"📊 当前状态 ({datetime.now().strftime('%H:%M:%S')})")
        print(f"{'─'*80}")

        for symbol in self.symbols:
            signal = self.latest_signals.get(symbol)
            if not signal:
                continue

            action = signal['action']
            strength = signal['strength']
            regime = signal['market_regime']
            market_data = signal.get('market_data', {})
            price = market_data.get('price', 0)

            # 图标
            action_icon = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}[action]
            regime_emoji = {
                'STRONG_TREND': '🔥',
                'TREND': '📈',
                'RANGE': '↔️',
                'SQUEEZE': '💥',
                'NEUTRAL': '😐'
            }.get(regime, '📊')

            print(f"{symbol:12} | ${price:>10,.2f} | {regime_emoji} {regime:12} | {action_icon} {action:4} | 强度: {strength:3}/100")

        print(f"{'─'*80}\n")

    async def _periodic_status_update(self):
        """定期更新状态显示"""
        while True:
            await asyncio.sleep(60)  # 每60秒显示一次
            self._display_all_status()

    async def cleanup(self):
        """清理资源"""
        print(f"\n\n{'='*80}")
        print(f"📊 监控统计")
        print(f"{'='*80}")

        runtime = (datetime.now() - self.start_time).total_seconds()
        print(f"运行时间: {runtime:.0f} 秒")

        print(f"\n各币种信号数:")
        total_signals = 0
        for symbol, count in self.signal_counts.items():
            print(f"  {symbol}: {count} 个信号")
            total_signals += count

        print(f"\n总信号数: {total_signals}")

        # 显示日志摘要
        print(self.logger.get_summary())

        print(f"{'='*80}")
        print(f"👋 再见！")

        # 关闭所有流
        for stream in self.streams.values():
            await stream.close()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='多币种交易信号监控系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监控现货市场的 BTC 和 ETH
  python multi_monitor.py BTC/USDT ETH/USDT -t 15m --proxy http://127.0.0.1:7890

  # 监控合约市场（永续合约）
  python multi_monitor.py BTC/USDT:USDT ETH/USDT:USDT -t 15m -m future --proxy http://127.0.0.1:7890

  # 监控只在合约市场上线的币种
  python multi_monitor.py PEPE/USDT:USDT BONK/USDT:USDT -t 1h -m future --proxy http://127.0.0.1:7890

  # 使用不同交易所
  python multi_monitor.py BTC/USDT ETH/USDT -e okx -m future --proxy http://127.0.0.1:7890

特点:
  - 📊 同时监控多个交易对
  - 🔄 支持现货和合约市场
  - 💾 自动保存所有买卖信号到文件
  - 🔔 信号变化即时提醒
  - 📈 每分钟显示所有币种状态
  - 📋 包含完整的交易计划（买入价、止盈、止损）

信号保存位置:
  - CSV: signal_logs/signals_YYYYMMDD.csv
  - JSON: signal_logs/signals_YYYYMMDD.json

注意事项:
  - 现货交易对格式: BTC/USDT
  - 合约交易对格式: BTC/USDT:USDT (注意有 :USDT 后缀)
        """
    )

    parser.add_argument('symbols', nargs='+', help='交易对列表，如 BTC/USDT 或 BTC/USDT:USDT (合约)')
    parser.add_argument('-t', '--timeframe', default='15m',
                        help='K线周期 (1m, 5m, 15m, 1h, 4h), 默认: 15m')
    parser.add_argument('-e', '--exchange', default='binance',
                        help='交易所, 默认: binance')
    parser.add_argument('-m', '--market', default='spot',
                        choices=['spot', 'future'],
                        help='市场类型: spot (现货) 或 future (合约), 默认: spot')
    parser.add_argument('--proxy', help='代理地址，如 http://127.0.0.1:7890')

    args = parser.parse_args()

    # 创建监控器
    monitor = MultiCoinMonitor(
        symbols=args.symbols,
        timeframe=args.timeframe,
        exchange=args.exchange,
        proxy=args.proxy,
        market_type=args.market
    )

    # 启动
    await monitor.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
        sys.exit(0)
