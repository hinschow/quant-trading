#!/usr/bin/env python3
"""
信号分析工具 - 命令行版本
用于分析交易对并给出买卖建议
"""

import argparse
import sys
from datetime import datetime
from typing import List
from data_collector import DataCollector
from strategy_engine import StrategyEngine
import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误
    format='%(message)s'
)


class SignalAnalyzer:
    """信号分析器"""

    def __init__(self, exchange: str = 'binance'):
        """初始化分析器"""
        self.collector = DataCollector(exchange)
        self.engine = StrategyEngine()

    def analyze_symbol(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 500
    ) -> dict:
        """
        分析单个交易对

        Args:
            symbol: 交易对，如 BTC/USDT
            timeframe: 时间周期
            limit: K线数量

        Returns:
            分析结果
        """
        # 获取数据
        df = self.collector.fetch_ohlcv(symbol, timeframe, limit)

        # 生成信号
        signal = self.engine.generate_signal(df)

        # 获取当前价格
        current_price = self.collector.get_current_price(symbol)

        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'current_price': current_price,
            'signal': signal,
            'data_points': len(df),
            'data_range': (df.index[0], df.index[-1])
        }

    def analyze_multiple(
        self,
        symbols: List[str],
        timeframe: str = '1h'
    ) -> List[dict]:
        """
        分析多个交易对

        Args:
            symbols: 交易对列表
            timeframe: 时间周期

        Returns:
            分析结果列表
        """
        results = []
        for symbol in symbols:
            try:
                result = self.analyze_symbol(symbol, timeframe)
                results.append(result)
            except Exception as e:
                print(f"❌ 分析 {symbol} 失败: {e}")
        return results

    def print_analysis(self, result: dict):
        """
        打印分析结果

        Args:
            result: 分析结果
        """
        signal = result['signal']
        market_data = signal['market_data']

        # 表头
        print("\n" + "="*80)
        print(f"📊 {result['symbol']} - {result['timeframe']} 交易信号分析")
        print("="*80)

        # 基本信息
        print(f"\n【基本信息】")
        print(f"  当前价格: ${result['current_price']:,.2f}")
        print(f"  数据范围: {result['data_range'][0]} ~ {result['data_range'][1]}")
        print(f"  数据点数: {result['data_points']}")

        # 市场状态
        print(f"\n【市场状态】")
        regime_desc = {
            'STRONG_TREND': '🔥 强趋势 (高ADX + 高波动)',
            'TREND': '📈 趋势 (ADX中等)',
            'RANGE': '↔️  震荡 (低ADX + 低波动)',
            'SQUEEZE': '💥 挤压 (波动极低，待突破)',
            'NEUTRAL': '😐 中性'
        }
        print(f"  状态: {regime_desc.get(signal['market_regime'], signal['market_regime'])}")
        print(f"  策略: {signal['type']}")

        # 核心指标
        print(f"\n【核心指标】")
        print(f"  EMA50:  ${market_data['ema_50']:,.2f}")
        print(f"  EMA200: ${market_data['ema_200']:,.2f}")
        print(f"  趋势:   {'🟢 多头' if market_data['ema_50'] > market_data['ema_200'] else '🔴 空头'}")
        print(f"\n  RSI:    {market_data['rsi']:.1f} ", end='')
        if market_data['rsi'] < 30:
            print("(超卖 🟢)")
        elif market_data['rsi'] > 70:
            print("(超买 🔴)")
        else:
            print("(中性)")

        print(f"  MACD:   {market_data['macd']:.2f}")
        print(f"  Signal: {market_data['macd_signal']:.2f}")
        print(f"  ADX:    {market_data['adx']:.1f} ", end='')
        if market_data['adx'] > 30:
            print("(强趋势)")
        elif market_data['adx'] > 20:
            print("(趋势)")
        else:
            print("(震荡)")

        print(f"  BBW:    {market_data['bbw']:.4f}")

        # 布林带
        print(f"\n【布林带】")
        print(f"  上轨: ${market_data['bb_upper']:,.2f}")
        print(f"  当前: ${result['current_price']:,.2f}")
        print(f"  下轨: ${market_data['bb_lower']:,.2f}")

        # 价格相对位置
        bb_position = (result['current_price'] - market_data['bb_lower']) / \
                      (market_data['bb_upper'] - market_data['bb_lower']) * 100
        print(f"  位置: {bb_position:.1f}% (0%=下轨, 100%=上轨)")

        # 交易信号
        print(f"\n【交易信号】")

        # 动作图标
        action_icon = {
            'BUY': '🟢 买入',
            'SELL': '🔴 卖出',
            'HOLD': '⚪ 观望'
        }

        print(f"  操作: {action_icon.get(signal['action'], signal['action'])}")
        print(f"  强度: {signal['strength']}/100", end='')

        # 强度条
        strength_bar = '█' * (signal['strength'] // 10) + '░' * (10 - signal['strength'] // 10)
        print(f" [{strength_bar}]")

        # 理由
        print(f"\n  理由:")
        if signal['reasons']:
            for reason in signal['reasons']:
                print(f"    • {reason}")
        else:
            print(f"    • 无明确信号")

        # 建议
        print(f"\n【操作建议】")
        if signal['action'] == 'BUY' and signal['strength'] >= 60:
            print(f"  ✅ 建议买入")
            print(f"  📍 入场价格: ${result['current_price']:,.2f}")
            print(f"  🎯 止损位置: ${result['current_price'] * 0.97:,.2f} (-3%)")
            print(f"  🎯 目标位置: ${result['current_price'] * 1.05:,.2f} (+5%)")

        elif signal['action'] == 'SELL' and signal['strength'] >= 60:
            print(f"  ⚠️  建议卖出/做空")
            print(f"  📍 出场价格: ${result['current_price']:,.2f}")
            print(f"  🎯 止损位置: ${result['current_price'] * 1.03:,.2f} (+3%)")
            print(f"  🎯 目标位置: ${result['current_price'] * 0.95:,.2f} (-5%)")

        elif signal['action'] == 'BUY' or signal['action'] == 'SELL':
            print(f"  ⚠️  信号较弱 (强度 {signal['strength']}/100)")
            print(f"  💡 建议谨慎，等待更强信号")

        else:
            print(f"  ⚪ 暂时观望，等待机会")
            print(f"  💡 关注关键价位突破")

        print("\n" + "="*80)

    def print_summary(self, results: List[dict], show_all: bool = False):
        """
        打印多个交易对的汇总

        Args:
            results: 分析结果列表
            show_all: 是否显示所有结果（否则只显示有信号的）
        """
        print("\n" + "="*80)
        print(f"📊 交易信号汇总 (共 {len(results)} 个交易对)")
        print("="*80)

        # 按信号强度排序
        results.sort(key=lambda x: x['signal']['strength'], reverse=True)

        # 分类
        buy_signals = [r for r in results if r['signal']['action'] == 'BUY']
        sell_signals = [r for r in results if r['signal']['action'] == 'SELL']
        hold_signals = [r for r in results if r['signal']['action'] == 'HOLD']

        # 买入信号
        if buy_signals:
            print(f"\n🟢 买入信号 ({len(buy_signals)}个):")
            print(f"{'交易对':<15} {'价格':<12} {'强度':<8} {'市场状态':<15} {'理由'}")
            print("-" * 80)
            for r in buy_signals:
                if show_all or r['signal']['strength'] >= 40:
                    reasons = ', '.join(r['signal']['reasons'][:2])
                    print(f"{r['symbol']:<15} ${r['current_price']:<11,.2f} "
                          f"{r['signal']['strength']:<7}/100 "
                          f"{r['signal']['market_regime']:<15} {reasons}")

        # 卖出信号
        if sell_signals:
            print(f"\n🔴 卖出信号 ({len(sell_signals)}个):")
            print(f"{'交易对':<15} {'价格':<12} {'强度':<8} {'市场状态':<15} {'理由'}")
            print("-" * 80)
            for r in sell_signals:
                if show_all or r['signal']['strength'] >= 40:
                    reasons = ', '.join(r['signal']['reasons'][:2])
                    print(f"{r['symbol']:<15} ${r['current_price']:<11,.2f} "
                          f"{r['signal']['strength']:<7}/100 "
                          f"{r['signal']['market_regime']:<15} {reasons}")

        # 观望
        if show_all and hold_signals:
            print(f"\n⚪ 观望 ({len(hold_signals)}个):")
            for r in hold_signals[:5]:  # 只显示前5个
                print(f"  {r['symbol']:<15} ${r['current_price']:<11,.2f} "
                      f"{r['signal']['market_regime']}")

        print("\n" + "="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='量化交易信号分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析单个交易对
  python signal_analyzer.py BTC/USDT

  # 指定时间周期
  python signal_analyzer.py BTC/USDT -t 4h

  # 分析多个交易对
  python signal_analyzer.py BTC/USDT ETH/USDT BNB/USDT

  # 扫描所有USDT交易对
  python signal_analyzer.py --scan USDT

  # 只显示强信号（强度>=60）
  python signal_analyzer.py --scan USDT --min-strength 60
        """
    )

    parser.add_argument('symbols', nargs='*', help='交易对列表，如 BTC/USDT ETH/USDT')
    parser.add_argument('-t', '--timeframe', default='1h',
                        help='时间周期 (1m, 5m, 15m, 1h, 4h, 1d), 默认: 1h')
    parser.add_argument('-e', '--exchange', default='binance',
                        help='交易所, 默认: binance')
    parser.add_argument('--scan', help='扫描所有交易对，如 USDT')
    parser.add_argument('--min-strength', type=int, default=0,
                        help='最小信号强度过滤, 默认: 0')
    parser.add_argument('--all', action='store_true',
                        help='显示所有结果（包括观望）')

    args = parser.parse_args()

    # 创建分析器
    analyzer = SignalAnalyzer(args.exchange)

    try:
        # 扫描模式
        if args.scan:
            print(f"\n🔍 扫描所有 {args.scan} 交易对...")
            symbols = analyzer.collector.get_supported_symbols(args.scan)
            # 只分析前20个（避免太慢）
            symbols = symbols[:20]
            print(f"📊 将分析 {len(symbols)} 个交易对...\n")

            results = analyzer.analyze_multiple(symbols, args.timeframe)

            # 过滤信号强度
            if args.min_strength > 0:
                results = [r for r in results if r['signal']['strength'] >= args.min_strength]

            analyzer.print_summary(results, args.all)

        # 指定交易对模式
        elif args.symbols:
            if len(args.symbols) == 1:
                # 单个交易对 - 详细分析
                result = analyzer.analyze_symbol(args.symbols[0], args.timeframe)
                analyzer.print_analysis(result)
            else:
                # 多个交易对 - 汇总
                results = analyzer.analyze_multiple(args.symbols, args.timeframe)
                analyzer.print_summary(results, args.all)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
