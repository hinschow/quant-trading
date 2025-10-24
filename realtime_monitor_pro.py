#!/usr/bin/env python3
"""
增强版实时监控器
同时监听：实时价格（ticker）+ K线信号
在单一界面整合显示
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import Dict, Optional
from collections import deque
import logging

from websocket_stream import WebSocketStream
from realtime_engine import RealtimeSignalEngine
from data_collector import DataCollector

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealtimeMonitorPro:
    """增强版实时监控器 - 双流整合"""

    def __init__(
        self,
        symbol: str,
        timeframe: str = '15m',
        exchange: str = 'binance',
        proxy: str = None
    ):
        """
        初始化增强版监控器

        Args:
            symbol: 交易对（自动识别现货或合约）
            timeframe: K线时间周期（用于信号）
            exchange: 交易所
            proxy: 代理地址
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange_name = exchange
        self.proxy = proxy

        # 自动检测市场类型
        self.market_type = self._detect_market_type(symbol)

        # 两个 WebSocket 流
        self.ticker_stream = WebSocketStream(exchange, proxy, self.market_type)  # ticker流
        self.kline_stream = WebSocketStream(exchange, proxy, self.market_type)   # K线流

        # 实时信号引擎
        self.engine = RealtimeSignalEngine(symbol, timeframe)
        self.engine.on_signal_change = self.on_signal_change

        # 实时数据
        self.latest_ticker: Optional[Dict] = None
        self.latest_signal: Optional[Dict] = None

        # 价格历史（用于趋势显示）
        self.price_history = deque(maxlen=20)  # 最近20次价格

        # 统计
        self.ticker_count = 0
        self.kline_count = 0
        self.signal_changes = 0
        self.start_time = datetime.now()

        # 显示控制
        self.last_detail_time = datetime.now()
        self.detail_interval = 30  # 每30秒显示一次详细信息

        # 价格精度（动态检测）
        self.price_precision = 2  # 默认2位小数

        # 市场类型说明
        market_name = {'spot': '现货', 'future': '合约/永续'}[self.market_type]

        print(f"\n{'='*80}")
        print(f"🚀 增强版实时交易信号监控 (双流整合)")
        print(f"{'='*80}")
        print(f"交易对: {symbol}")
        print(f"市场类型: {market_name}")
        print(f"💹 实时价格流: ticker (秒级更新)")
        print(f"📊 K线信号流: {timeframe} (信号计算)")
        print(f"交易所: {exchange}")
        print(f"代理: {proxy or '无'}")
        print(f"{'='*80}\n")

    @staticmethod
    def _detect_market_type(symbol: str) -> str:
        """
        自动检测交易对的市场类型

        Args:
            symbol: 交易对

        Returns:
            'spot' 或 'future'
        """
        # 合约交易对格式：BTC/USDT:USDT（有冒号）
        # 现货交易对格式：BTC/USDT（无冒号）
        if ':' in symbol:
            return 'future'
        else:
            return 'spot'

    async def start(self):
        """启动双流监控"""
        try:
            # 1. 获取历史数据初始化
            print(f"📥 正在获取历史数据...")
            collector = DataCollector(self.exchange_name, self.proxy, self.market_type)
            historical_df = collector.fetch_ohlcv(self.symbol, self.timeframe, limit=500)

            # 2. 初始化信号引擎
            print(f"⚙️  正在初始化信号引擎...")
            self.engine.initialize(historical_df)

            # 3. 显示初始信号
            self._display_initial_signal()

            print(f"\n📡 开始双流监听...")
            print(f"{'='*80}\n")

            # 4. 同时启动两个流
            await asyncio.gather(
                self._run_ticker_stream(),  # 实时价格流
                self._run_kline_stream(),   # K线信号流
                return_exceptions=True
            )

        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断")
        except Exception as e:
            print(f"\n\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

    async def _run_ticker_stream(self):
        """运行ticker流（实时价格）"""
        try:
            await self.ticker_stream.watch_ticker(
                self.symbol,
                self.on_ticker
            )
        except Exception as e:
            logger.error(f"❌ ticker流错误: {e}")

    async def _run_kline_stream(self):
        """运行K线流（信号计算）"""
        try:
            await self.kline_stream.watch_ohlcv(
                self.symbol,
                self.timeframe,
                self.on_kline
            )
        except Exception as e:
            logger.error(f"❌ K线流错误: {e}")

    def _detect_price_precision(self, price: float) -> int:
        """
        动态检测价格精度

        Args:
            price: 价格

        Returns:
            建议的小数位数
        """
        if price >= 1000:
            return 2  # $10,000.00
        elif price >= 100:
            return 2  # $100.00
        elif price >= 10:
            return 3  # $10.000
        elif price >= 1:
            return 4  # $1.0000
        elif price >= 0.1:
            return 4  # $0.1000
        elif price >= 0.01:
            return 4  # $0.0100
        elif price >= 0.001:
            return 5  # $0.00100
        elif price >= 0.0001:
            return 6  # $0.000100
        elif price >= 0.00001:
            return 7  # $0.0000100
        else:
            return 8  # $0.00000100

    def _format_price(self, price: float, precision: int = None) -> str:
        """
        格式化价格显示

        Args:
            price: 价格
            precision: 指定精度（None则自动检测）

        Returns:
            格式化后的价格字符串
        """
        if precision is None:
            precision = self._detect_price_precision(price)

        # 使用千分位分隔符
        if price >= 1000:
            return f"{price:,.{precision}f}"
        else:
            return f"{price:.{precision}f}"

    async def on_ticker(self, ticker: Dict):
        """
        ticker回调（实时价格）

        Args:
            ticker: ticker数据
        """
        self.ticker_count += 1
        self.latest_ticker = ticker

        # 记录价格历史并动态检测精度
        if 'last' in ticker:
            price = ticker['last']
            self.price_history.append({
                'time': datetime.now(),
                'price': price
            })
            # 更新价格精度
            self.price_precision = self._detect_price_precision(price)

        # 实时显示更新
        self._display_realtime_status()

        # 定期显示详细信息
        now = datetime.now()
        if (now - self.last_detail_time).total_seconds() >= self.detail_interval:
            self._display_detailed_update()
            self.last_detail_time = now

    async def on_kline(self, kline: Dict):
        """
        K线回调（信号计算）

        Args:
            kline: K线数据
        """
        self.kline_count += 1

        # 传递给引擎处理
        await self.engine.on_kline(kline)

        # 更新最新信号
        self.latest_signal = self.engine.get_signal()

    def on_signal_change(self, signal: Dict):
        """
        信号变化回调

        Args:
            signal: 新信号
        """
        self.signal_changes += 1

        print(f"\n\n{'='*80}")
        print(f"🔔 交易信号变化！ ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
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
        print(f"📊 初始交易信号")
        print(f"{'='*80}")

        self._display_signal(signal)

        print(f"{'='*80}")

    def _display_signal(self, signal: Dict):
        """显示信号详情（简化版）"""
        market_data = signal['market_data']
        action = signal['action']
        strength = signal['strength']
        regime = signal['market_regime']
        trading_plan = signal.get('trading_plan', {})

        # 市场状态
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

        print(f"\n【市场状态】 {regime_desc.get(regime, regime)}")
        print(f"\n【交易信号】 {action_icon.get(action, action)} {action}")
        print(f"  信号强度: {strength}/100 {'█' * (strength // 10)}{'░' * (10 - strength // 10)}")

        # 显示交易计划（重点）
        if action != 'HOLD' and trading_plan.get('entry_price'):
            print(f"\n{'='*60}")
            print(f"📋 交易计划")
            print(f"{'='*60}")

            entry = trading_plan['entry_price']
            stop_loss = trading_plan['stop_loss_price']
            take_profit = trading_plan['take_profit_price']

            if action == 'BUY':
                print(f"  🟢 买入价格:  ${self._format_price(entry)}")
                print(f"  🎯 止盈目标:  ${self._format_price(take_profit)}  (+{trading_plan['take_profit_pct']:.1f}%)")
                print(f"  🛑 止损价格:  ${self._format_price(stop_loss)}  (-{trading_plan['stop_loss_pct']:.1f}%)")
            else:  # SELL
                print(f"  🔴 卖出价格:  ${self._format_price(entry)}")
                print(f"  🎯 止盈目标:  ${self._format_price(take_profit)}  (-{trading_plan['take_profit_pct']:.1f}%)")
                print(f"  🛑 止损价格:  ${self._format_price(stop_loss)}  (+{trading_plan['stop_loss_pct']:.1f}%)")

            print(f"\n  💰 风险回报比: 1:{trading_plan['risk_reward_ratio']:.2f}")
            print(f"{'='*60}")

        # 显示理由
        if signal['reasons']:
            print(f"\n【信号理由】")
            for reason in signal['reasons']:
                print(f"  • {reason}")

        # 显示关键指标
        print(f"\n【关键指标】")
        print(f"  RSI: {market_data['rsi']:.1f}  |  ADX: {market_data['adx']:.1f}")

    def _display_realtime_status(self):
        """显示实时状态（单行更新）"""
        if not self.latest_ticker:
            return

        ticker = self.latest_ticker
        price = ticker.get('last', 0)

        # 价格变化
        price_change = ''
        if len(self.price_history) >= 2:
            prev_price = self.price_history[-2]['price']
            if price > prev_price:
                price_change = '↗️'
            elif price < prev_price:
                price_change = '↘️'
            else:
                price_change = '→'

        # 24小时变化
        change_pct = ticker.get('percentage', 0)
        change_color = '🟢' if change_pct >= 0 else '🔴'

        # 信号状态
        signal_str = '⚪ 观望'
        trading_info = ''

        if self.latest_signal:
            action = self.latest_signal['action']
            regime = self.latest_signal['market_regime']
            trading_plan = self.latest_signal.get('trading_plan', {})

            action_icon = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(action, action)
            regime_emoji = {
                'STRONG_TREND': '🔥',
                'TREND': '📈',
                'RANGE': '↔️',
                'SQUEEZE': '💥',
                'NEUTRAL': '😐'
            }.get(regime, '📊')

            signal_str = f"{regime_emoji} {action_icon} {action}"

            # 如果有交易信号，显示止盈止损
            if action != 'HOLD' and trading_plan.get('entry_price'):
                tp = trading_plan['take_profit_price']
                sl = trading_plan['stop_loss_price']
                trading_info = f" | 🎯 {self._format_price(tp)} | 🛑 {self._format_price(sl)}"

        # 格式化价格（动态精度）
        price_str = self._format_price(price)

        # 构建状态行
        status_line = (
            f"\r{datetime.now().strftime('%H:%M:%S')} | "
            f"💹 ${price_str:>12} {price_change} | "
            f"{change_color} {change_pct:>+5.2f}% | "
            f"{signal_str:<15}{trading_info}"
        )

        # 单行更新
        print(status_line, end='', flush=True)

    def _display_detailed_update(self):
        """显示详细更新（每30秒）"""
        if not self.latest_ticker or not self.latest_signal:
            return

        ticker = self.latest_ticker
        signal = self.latest_signal
        market_data = signal['market_data']
        trading_plan = signal.get('trading_plan', {})

        print(f"\n\n{'─'*80}")
        print(f"📊 详细更新 ({datetime.now().strftime('%H:%M:%S')})")
        print(f"{'─'*80}")

        # 价格信息（使用动态精度）
        current_price = ticker.get('last', 0)
        high_price = ticker.get('high', 0)
        low_price = ticker.get('low', 0)

        print(f"【当前价格】")
        print(f"  💹 ${self._format_price(current_price)}")
        print(f"  24h: 最高 ${self._format_price(high_price)} | 最低 ${self._format_price(low_price)}")

        # 交易计划（如果有信号）
        action = signal['action']
        if action != 'HOLD' and trading_plan.get('entry_price'):
            print(f"\n【交易计划】")
            entry = trading_plan['entry_price']
            tp = trading_plan['take_profit_price']
            sl = trading_plan['stop_loss_price']

            if action == 'BUY':
                print(f"  🟢 买入: ${self._format_price(entry)}")
                print(f"  🎯 止盈: ${self._format_price(tp)} (+{trading_plan['take_profit_pct']:.1f}%)")
                print(f"  🛑 止损: ${self._format_price(sl)} (-{trading_plan['stop_loss_pct']:.1f}%)")
            else:
                print(f"  🔴 卖出: ${self._format_price(entry)}")
                print(f"  🎯 止盈: ${self._format_price(tp)}")
                print(f"  🛑 止损: ${self._format_price(sl)}")

        # 关键指标
        print(f"\n【关键指标】")
        print(f"  RSI: {market_data['rsi']:.1f}  |  ADX: {market_data['adx']:.1f}")

        print(f"{'─'*80}\n")

    async def cleanup(self):
        """清理资源"""
        print(f"\n\n{'='*80}")
        print(f"📊 监控统计")
        print(f"{'='*80}")

        runtime = (datetime.now() - self.start_time).total_seconds()
        print(f"运行时间: {runtime:.0f} 秒")
        print(f"价格更新: {self.ticker_count} 次")
        print(f"K线更新: {self.kline_count} 次")
        print(f"信号变化: {self.signal_changes} 次")

        if self.ticker_count > 0 and runtime > 0:
            update_rate = self.ticker_count / runtime
            print(f"平均更新: {update_rate:.1f} 次/秒")

        print(f"{'='*80}")
        print(f"👋 再见！")

        await self.ticker_stream.close()
        await self.kline_stream.close()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='增强版实时交易信号监控（双流整合）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监听现货BTC（实时价格 + 15分钟信号）
  python realtime_monitor_pro.py BTC/USDT -t 15m --proxy http://127.0.0.1:7890

  # 监听合约ETH（实时价格 + 1小时信号）- 自动识别
  python realtime_monitor_pro.py ETH/USDT:USDT -t 1h --proxy http://127.0.0.1:7890

  # 监听只在合约市场的币种 - 自动识别
  python realtime_monitor_pro.py PEPE/USDT:USDT -t 15m --proxy http://127.0.0.1:7890

特点:
  - 💹 实时价格流（秒级更新）
  - 📊 K线信号流（准确的买卖建议）
  - 🔄 自动识别现货和合约市场（无需手动指定）
  - 📈 价格趋势显示
  - 🔔 信号变化提醒
  - 📉 技术指标实时更新

交易对格式:
  - 现货: BTC/USDT (无冒号)
  - 合约: BTC/USDT:USDT (有 :USDT 后缀)
  - 系统会自动识别市场类型
        """
    )

    parser.add_argument('symbol', help='交易对，如 BTC/USDT (现货) 或 BTC/USDT:USDT (合约)')
    parser.add_argument('-t', '--timeframe', default='15m',
                        help='K线周期 (1m, 5m, 15m, 1h, 4h), 默认: 15m')
    parser.add_argument('-e', '--exchange', default='binance',
                        help='交易所, 默认: binance')
    parser.add_argument('--proxy', help='代理地址，如 http://127.0.0.1:7890')

    args = parser.parse_args()

    # 创建监控器
    monitor = RealtimeMonitorPro(
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
