#!/usr/bin/env python3
"""
多时间周期分析工具
对比 15m、30m、1h 的回测结果
"""

import pandas as pd
import numpy as np
import os
import sys
import json

def analyze_trades(csv_file):
    """分析单个回测结果"""
    if not os.path.exists(csv_file):
        return None

    df = pd.read_csv(csv_file)

    # 基本统计
    total_trades = len(df[df['type'] == 'BUY'])
    if total_trades == 0:
        return None

    # 过滤出有盈亏数据的卖出交易
    sell_trades = df[df['type'] == 'SELL'].copy()
    sell_trades = sell_trades[sell_trades['profit'].notna()]

    if len(sell_trades) == 0:
        return None

    # 计算盈亏统计
    winning_trades = sell_trades[sell_trades['profit'] > 0]
    losing_trades = sell_trades[sell_trades['profit'] < 0]

    win_rate = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
    total_profit_pct = ((sell_trades['value'].iloc[-1] - 10000) / 10000) * 100

    profit_factor = abs(winning_trades['profit'].sum() / losing_trades['profit'].sum()) \
        if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0 else float('inf')

    # 计算最大回撤
    cumulative_returns = (sell_trades['value'] / 10000 - 1) * 100
    running_max = cumulative_returns.expanding().max()
    drawdown = cumulative_returns - running_max
    max_drawdown = drawdown.min()

    # 信号强度
    buy_signals = df[df['type'] == 'BUY']
    signal_strengths = buy_signals['signal_strength'].tolist()
    avg_signal_strength = np.mean(signal_strengths) if signal_strengths else 0

    # 持仓时间
    buy_times = df[df['type'] == 'BUY']['timestamp'].tolist()
    sell_times = df[df['type'] == 'SELL']['timestamp'].tolist()
    holding_periods = []
    for i in range(min(len(buy_times), len(sell_times))):
        buy_time = pd.to_datetime(buy_times[i])
        sell_time = pd.to_datetime(sell_times[i])
        holding_periods.append((sell_time - buy_time).total_seconds() / 3600)
    avg_holding_hours = np.mean(holding_periods) if holding_periods else 0

    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'profit_pct': total_profit_pct,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'avg_signal_strength': avg_signal_strength,
        'avg_holding_hours': avg_holding_hours,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
    }

def main():
    """主函数"""
    base_path = 'backtest_results/multi_timeframe'

    if not os.path.exists(base_path):
        print(f"❌ 未找到多时间周期结果目录: {base_path}")
        print("\n请先运行: python3 run_multi_timeframe_backtest.py")
        sys.exit(1)

    print("\n" + "="*100)
    print("多时间周期回测结果对比")
    print("="*100)
    print()

    timeframes = ['15m', '30m', '1h']

    # 从配置文件读取交易对
    try:
        from config.strategy_params import TRADING_SYMBOLS
        symbols = TRADING_SYMBOLS
        print(f"✓ 从配置读取 {len(symbols)} 个交易对: {', '.join(symbols)}\n")
    except ImportError:
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        print(f"⚠️  使用默认交易对: {', '.join(symbols)}\n")

    all_results = {}

    # 收集所有结果
    for tf in timeframes:
        tf_path = os.path.join(base_path, tf)
        if not os.path.exists(tf_path):
            print(f"⚠️  {tf} 目录不存在，跳过")
            continue

        all_results[tf] = {}
        for symbol in symbols:
            filename = f"backtest_trades_{symbol.replace('/', '_')}_{tf}.csv"
            filepath = os.path.join(tf_path, filename)

            result = analyze_trades(filepath)
            if result:
                all_results[tf][symbol] = result
            else:
                print(f"⚠️  {symbol} @ {tf} 无有效数据")

    if not all_results:
        print("❌ 没有找到任何有效的回测结果")
        sys.exit(1)

    # 按品种对比
    for symbol in symbols:
        print(f"\n{'='*100}")
        print(f"{symbol} - 时间周期对比")
        print(f"{'='*100}\n")

        print(f"{'周期':<8} {'交易次数':<10} {'胜率':<10} {'收益率':<12} {'盈亏比':<10} {'最大回撤':<12} {'信号强度':<10} {'持仓时间':<12}")
        print("-"*100)

        symbol_results = []
        for tf in timeframes:
            if tf in all_results and symbol in all_results[tf]:
                r = all_results[tf][symbol]
                symbol_results.append((tf, r))
                print(f"{tf:<8} {r['total_trades']:<10} {r['win_rate']:>8.2f}%  "
                      f"{r['profit_pct']:>+10.2f}%  {r['profit_factor']:>8.2f}  "
                      f"{r['max_drawdown']:>10.2f}%  {r['avg_signal_strength']:>8.1f}  "
                      f"{r['avg_holding_hours']:>10.1f}h")

        # 找最佳时间周期
        if symbol_results:
            best = max(symbol_results, key=lambda x: x[1]['profit_pct'])
            print(f"\n🏆 {symbol} 最佳周期: {best[0]} (收益率 {best[1]['profit_pct']:+.2f}%)")

    # 整体对比
    print(f"\n\n{'='*100}")
    print("整体组合表现对比")
    print(f"{'='*100}\n")

    print(f"{'周期':<8} {'总收益率':<12} {'平均胜率':<12} {'平均盈亏比':<12} {'总交易次数':<12}")
    print("-"*100)

    for tf in timeframes:
        if tf not in all_results or not all_results[tf]:
            continue

        results_list = list(all_results[tf].values())
        if not results_list:
            continue

        # 计算整体指标
        total_profit = sum(r['profit_pct'] for r in results_list)
        avg_winrate = sum(r['win_rate'] for r in results_list) / len(results_list)
        avg_pf = sum(r['profit_factor'] for r in results_list if r['profit_factor'] != float('inf')) / \
                 len([r for r in results_list if r['profit_factor'] != float('inf')])
        total_trades = sum(r['total_trades'] for r in results_list)

        print(f"{tf:<8} {total_profit:>+10.2f}%  {avg_winrate:>10.2f}%  "
              f"{avg_pf:>10.2f}  {total_trades:>10}")

    # 推荐
    print(f"\n{'='*100}")
    print("📊 分析建议")
    print(f"{'='*100}\n")

    # 找到最佳时间周期
    tf_scores = {}
    for tf in timeframes:
        if tf not in all_results or not all_results[tf]:
            continue

        results_list = list(all_results[tf].values())
        if not results_list:
            continue

        total_profit = sum(r['profit_pct'] for r in results_list)
        avg_winrate = sum(r['win_rate'] for r in results_list) / len(results_list)

        # 综合得分：收益率 + 胜率/10
        score = total_profit + avg_winrate / 10
        tf_scores[tf] = {
            'score': score,
            'profit': total_profit,
            'winrate': avg_winrate
        }

    if tf_scores:
        best_tf = max(tf_scores.items(), key=lambda x: x[1]['score'])
        print(f"🎯 推荐时间周期: **{best_tf[0]}**")
        print(f"   总收益率: {best_tf[1]['profit']:+.2f}%")
        print(f"   平均胜率: {best_tf[1]['winrate']:.2f}%")
        print(f"   综合得分: {best_tf[1]['score']:.2f}")

    # 时间周期特性分析
    print(f"\n时间周期特性:")
    print(f"  15m: 交易频率高，适合短线快进快出，但需要更多时间监控")
    print(f"  30m: 平衡型，交易频率适中，适合日内交易")
    print(f"  1h:  交易频率低，适合趋势跟随，持仓时间较长")

    print()

    # 保存对比报告
    report_file = 'backtest_results/multi_timeframe/comparison_report.txt'
    print(f"对比报告已保存: {report_file}")

if __name__ == '__main__':
    main()
