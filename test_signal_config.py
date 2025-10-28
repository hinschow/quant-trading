#!/usr/bin/env python3
"""
测试信号配置系统
对比原版和v7.3版本的信号质量

使用方法：
  python3 test_signal_config.py
  python3 test_signal_config.py BTC/USDT  # 测试指定交易对
"""

import sys
from data_collector import DataCollector
from strategy_engine import StrategyEngine
from strategy_engine_v73 import StrategyEngineV73
from config.signal_filter_config import get_active_config, print_config_summary


def compare_signals(symbol='BTC/USDT', timeframe='1h', limit=500):
    """
    对比原版和v7.3的信号差异

    Args:
        symbol: 交易对
        timeframe: 时间周期
        limit: K线数量
    """
    print(f"\n{'='*80}")
    print(f"信号配置对比测试: {symbol} @ {timeframe}")
    print(f"{'='*80}\n")

    # 获取数据
    print("📊 获取历史数据...")
    collector = DataCollector('binance')
    df = collector.fetch_ohlcv(symbol, timeframe, limit)
    print(f"✅ 获取{len(df)}根K线数据\n")

    # 创建两个引擎
    print("🚀 初始化策略引擎...")
    engine_original = StrategyEngine(use_hyperliquid=False, use_smart_money=False)
    engine_v73 = StrategyEngineV73(use_hyperliquid=False, use_smart_money=False)
    print()

    # 打印当前配置
    print_config_summary()

    # 生成信号
    print(f"{'='*80}")
    print("原版引擎（v7.2）信号")
    print(f"{'='*80}")
    signal_original = engine_original.generate_signal(df, symbol)
    print_signal(signal_original)

    print(f"\n{'='*80}")
    print("优化引擎（v7.3）信号")
    print(f"{'='*80}")
    signal_v73 = engine_v73.generate_signal(df, symbol)
    print_signal(signal_v73)

    # 对比差异
    print(f"\n{'='*80}")
    print("差异对比")
    print(f"{'='*80}")
    compare_two_signals(signal_original, signal_v73)


def print_signal(signal: dict):
    """打印信号详情"""
    print(f"市场状态:  {signal.get('market_regime', 'N/A')}")
    print(f"策略类型:  {signal.get('type', 'N/A')}")
    print(f"操作建议:  {signal['action']}")
    print(f"信号强度:  {signal['strength']}/100")

    if 'market_data' in signal:
        market = signal['market_data']
        print(f"\n市场数据:")
        print(f"  价格:    ${market.get('price', 0):,.2f}")
        print(f"  RSI:     {market.get('rsi', 0):.1f}")
        print(f"  ADX:     {market.get('adx', 0):.1f}")
        print(f"  MACD:    {market.get('macd', 0):.4f}")

    print(f"\n信号理由 ({len(signal.get('reasons', []))}):")
    for i, reason in enumerate(signal.get('reasons', []), 1):
        print(f"  {i}. {reason}")


def compare_two_signals(original: dict, v73: dict):
    """对比两个信号的差异"""
    # 操作差异
    if original['action'] != v73['action']:
        print(f"⚠️  操作建议变化:")
        print(f"  原版: {original['action']}")
        print(f"  v7.3: {v73['action']}")
    else:
        print(f"✅ 操作建议一致: {original['action']}")

    # 强度差异
    strength_diff = v73['strength'] - original['strength']
    print(f"\n信号强度变化:")
    print(f"  原版: {original['strength']}/100")
    print(f"  v7.3: {v73['strength']}/100")
    print(f"  差值: {strength_diff:+d}")

    # 理由差异
    original_reasons = set(original.get('reasons', []))
    v73_reasons = set(v73.get('reasons', []))

    added_reasons = v73_reasons - original_reasons
    removed_reasons = original_reasons - v73_reasons

    if added_reasons:
        print(f"\n➕ v7.3新增理由:")
        for reason in added_reasons:
            print(f"  • {reason}")

    if removed_reasons:
        print(f"\n➖ v7.3移除理由:")
        for reason in removed_reasons:
            print(f"  • {reason}")

    if not added_reasons and not removed_reasons:
        print(f"\n✅ 理由完全一致")


def scan_recent_signals(symbol='BTC/USDT', timeframe='1h', bars=100):
    """
    扫描最近N根K线，统计信号差异

    Args:
        symbol: 交易对
        timeframe: 时间周期
        bars: 扫描K线数量
    """
    print(f"\n{'='*80}")
    print(f"信号扫描: {symbol} @ {timeframe} (最近{bars}根K线)")
    print(f"{'='*80}\n")

    # 获取数据
    collector = DataCollector('binance')
    df = collector.fetch_ohlcv(symbol, timeframe, bars + 200)  # +200确保指标有效

    # 创建引擎
    engine_original = StrategyEngine(use_hyperliquid=False, use_smart_money=False)
    engine_v73 = StrategyEngineV73(use_hyperliquid=False, use_smart_money=False)

    # 统计
    original_stats = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    v73_stats = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    action_changes = []

    print("🔍 扫描中...")
    for i in range(200, len(df)):
        current_df = df.iloc[:i+1].copy()

        # 生成信号
        signal_original = engine_original.generate_signal(current_df, symbol)
        signal_v73 = engine_v73.generate_signal(current_df, symbol)

        # 统计
        original_stats[signal_original['action']] += 1
        v73_stats[signal_v73['action']] += 1

        # 记录变化
        if signal_original['action'] != signal_v73['action']:
            action_changes.append({
                'bar': i,
                'timestamp': current_df.index[-1],
                'original': signal_original['action'],
                'v73': signal_v73['action'],
                'original_strength': signal_original['strength'],
                'v73_strength': signal_v73['strength']
            })

    # 打印统计结果
    print(f"\n{'='*80}")
    print("信号统计")
    print(f"{'='*80}")

    print(f"\n原版引擎（v7.2）:")
    print(f"  买入:  {original_stats['BUY']:>3} ({original_stats['BUY']/bars*100:.1f}%)")
    print(f"  卖出:  {original_stats['SELL']:>3} ({original_stats['SELL']/bars*100:.1f}%)")
    print(f"  观望:  {original_stats['HOLD']:>3} ({original_stats['HOLD']/bars*100:.1f}%)")
    print(f"  总计:  {sum(original_stats.values())}")

    print(f"\n优化引擎（v7.3）:")
    print(f"  买入:  {v73_stats['BUY']:>3} ({v73_stats['BUY']/bars*100:.1f}%)")
    print(f"  卖出:  {v73_stats['SELL']:>3} ({v73_stats['SELL']/bars*100:.1f}%)")
    print(f"  观望:  {v73_stats['HOLD']:>3} ({v73_stats['HOLD']/bars*100:.1f}%)")
    print(f"  总计:  {sum(v73_stats.values())}")

    # 信号减少比例
    original_active = original_stats['BUY'] + original_stats['SELL']
    v73_active = v73_stats['BUY'] + v73_stats['SELL']
    reduction_pct = (original_active - v73_active) / original_active * 100 if original_active > 0 else 0

    print(f"\n差异:")
    print(f"  原版活跃信号:  {original_active}次")
    print(f"  v7.3活跃信号:  {v73_active}次")
    print(f"  信号减少:      {reduction_pct:.1f}%")

    # 打印部分变化详情
    if action_changes:
        print(f"\n信号变化示例（前10个）:")
        for i, change in enumerate(action_changes[:10], 1):
            print(f"  {i}. {change['timestamp']} | "
                  f"{change['original']}({change['original_strength']}) → "
                  f"{change['v73']}({change['v73_strength']})")
        if len(action_changes) > 10:
            print(f"  ... 还有 {len(action_changes)-10} 个变化")

    print(f"\n{'='*80}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='测试信号配置系统')
    parser.add_argument('symbol', nargs='?', default='BTC/USDT',
                        help='交易对 (默认: BTC/USDT)')
    parser.add_argument('-t', '--timeframe', default='1h',
                        help='时间周期 (默认: 1h)')
    parser.add_argument('--scan', action='store_true',
                        help='扫描模式：统计最近100根K线的信号差异')

    args = parser.parse_args()

    if args.scan:
        # 扫描模式
        scan_recent_signals(args.symbol, args.timeframe)
    else:
        # 对比模式
        compare_signals(args.symbol, args.timeframe)


if __name__ == '__main__':
    main()
