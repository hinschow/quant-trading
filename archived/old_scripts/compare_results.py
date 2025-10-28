#!/usr/bin/env python3
"""
回测结果对比脚本
对比优化前后的表现
"""

import pandas as pd
import sys
import os

def load_results(suffix=''):
    """加载回测结果"""
    results = {}
    symbols = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']

    for symbol in symbols:
        filename = f'backtest_trades_{symbol}_1h{suffix}.csv'
        if os.path.exists(filename):
            results[symbol] = pd.read_csv(filename)
        else:
            print(f"⚠️  文件不存在: {filename}")

    return results

def analyze_performance(df, symbol):
    """分析单个品种的表现"""
    if df is None or len(df) == 0:
        return None

    sell_trades = df[df['type'] == 'SELL'].copy()
    sell_trades = sell_trades[sell_trades['profit'].notna()]

    if len(sell_trades) == 0:
        return None

    winning_trades = sell_trades[sell_trades['profit'] > 0]
    losing_trades = sell_trades[sell_trades['profit'] < 0]

    total_trades = len(df[df['type'] == 'BUY'])
    win_rate = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
    total_profit = sell_trades['profit'].sum()
    total_profit_pct = ((sell_trades['value'].iloc[-1] - 10000) / 10000) * 100
    final_value = sell_trades['value'].iloc[-1]

    avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0
    profit_factor = abs(winning_trades['profit'].sum() / losing_trades['profit'].sum()) if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0 else float('inf')

    cumulative_returns = (sell_trades['value'] / 10000 - 1) * 100
    running_max = cumulative_returns.expanding().max()
    drawdown = cumulative_returns - running_max
    max_drawdown = drawdown.min()

    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_profit_pct': total_profit_pct,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'final_value': final_value,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
    }

def print_comparison(old_results, new_results):
    """打印对比结果"""
    print("=" * 100)
    print("回测结果对比分析")
    print("=" * 100)
    print()

    # 单品种对比
    print(f"{'品种':<12} {'版本':<8} {'交易次数':<10} {'胜率':<10} {'收益率':<12} {'盈亏比':<10} {'最大回撤':<12}")
    print("-" * 100)

    all_old = []
    all_new = []

    for symbol in ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']:
        display_symbol = symbol.replace('_', '/')

        if symbol in old_results:
            old_perf = old_results[symbol]
            all_old.append(old_perf)
            print(f"{display_symbol:<12} {'原版本':<8} {old_perf['total_trades']:<10} {old_perf['win_rate']:>8.2f}%  {old_perf['total_profit_pct']:>+10.2f}%  {old_perf['profit_factor']:>8.2f}  {old_perf['max_drawdown']:>10.2f}%")

        if symbol in new_results:
            new_perf = new_results[symbol]
            all_new.append(new_perf)

            # 计算改善
            if symbol in old_results:
                old_perf = old_results[symbol]
                trade_diff = new_perf['total_trades'] - old_perf['total_trades']
                winrate_diff = new_perf['win_rate'] - old_perf['win_rate']
                profit_diff = new_perf['total_profit_pct'] - old_perf['total_profit_pct']
                pf_diff = new_perf['profit_factor'] - old_perf['profit_factor']
                dd_diff = new_perf['max_drawdown'] - old_perf['max_drawdown']

                trade_icon = "📉" if trade_diff < 0 else "📈"
                winrate_icon = "✅" if winrate_diff > 0 else "❌"
                profit_icon = "✅" if profit_diff > 0 else "❌"
                pf_icon = "✅" if pf_diff > 0 else "❌"
                dd_icon = "✅" if dd_diff > 0 else "❌"  # 回撤减少是好事

                print(f"{display_symbol:<12} {'优化版':<8} {new_perf['total_trades']:<10} {new_perf['win_rate']:>8.2f}%  {new_perf['total_profit_pct']:>+10.2f}%  {new_perf['profit_factor']:>8.2f}  {new_perf['max_drawdown']:>10.2f}%")
                print(f"{'改善':<12} {'':<8} {trade_diff:>+9} {trade_icon} {winrate_diff:>+7.2f}% {winrate_icon} {profit_diff:>+9.2f}% {profit_icon} {pf_diff:>+7.2f} {pf_icon} {dd_diff:>+9.2f}% {dd_icon}")
            else:
                print(f"{display_symbol:<12} {'优化版':<8} {new_perf['total_trades']:<10} {new_perf['win_rate']:>8.2f}%  {new_perf['total_profit_pct']:>+10.2f}%  {new_perf['profit_factor']:>8.2f}  {new_perf['max_drawdown']:>10.2f}%")

        print("-" * 100)

    # 整体对比
    if all_old and all_new:
        print()
        print("=" * 100)
        print("整体组合对比")
        print("=" * 100)

        old_total_value = sum(r['final_value'] for r in all_old)
        new_total_value = sum(r['final_value'] for r in all_new)
        old_total_return = ((old_total_value - 30000) / 30000) * 100
        new_total_return = ((new_total_value - 30000) / 30000) * 100
        old_avg_winrate = sum(r['win_rate'] for r in all_old) / len(all_old)
        new_avg_winrate = sum(r['win_rate'] for r in all_new) / len(all_new)

        print()
        print(f"{'指标':<20} {'原版本':<20} {'优化版':<20} {'改善':<20}")
        print("-" * 100)
        print(f"{'总投入':<20} {'30,000 USDT':<20} {'30,000 USDT':<20} {'-':<20}")
        print(f"{'总资产':<20} {f'{old_total_value:,.2f} USDT':<20} {f'{new_total_value:,.2f} USDT':<20} {f'{new_total_value - old_total_value:+,.2f} USDT':<20}")
        print(f"{'总收益率':<20} {f'{old_total_return:+.2f}%':<20} {f'{new_total_return:+.2f}%':<20} {f'{new_total_return - old_total_return:+.2f}%':<20}")
        print(f"{'平均胜率':<20} {f'{old_avg_winrate:.2f}%':<20} {f'{new_avg_winrate:.2f}%':<20} {f'{new_avg_winrate - old_avg_winrate:+.2f}%':<20}")

        # 评估
        print()
        print("=" * 100)
        print("优化效果评估")
        print("=" * 100)
        print()

        improvements = []
        if new_total_return > old_total_return:
            improvements.append(f"✅ 总收益率提升 {new_total_return - old_total_return:+.2f}%")
        else:
            improvements.append(f"❌ 总收益率下降 {new_total_return - old_total_return:+.2f}%")

        if new_avg_winrate > old_avg_winrate:
            improvements.append(f"✅ 平均胜率提升 {new_avg_winrate - old_avg_winrate:+.2f}%")
        else:
            improvements.append(f"❌ 平均胜率下降 {new_avg_winrate - old_avg_winrate:+.2f}%")

        # 统计改善的品种数
        improved_count = sum(1 for symbol in ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']
                            if symbol in old_results and symbol in new_results
                            and new_results[symbol]['total_profit_pct'] > old_results[symbol]['total_profit_pct'])

        improvements.append(f"📊 {improved_count}/3 个品种收益改善")

        for improvement in improvements:
            print(f"  {improvement}")

        print()
        if new_total_return > old_total_return and new_avg_winrate > old_avg_winrate:
            print("🎉 优化成功！建议采用新配置")
        elif new_total_return > old_total_return:
            print("⚠️  收益改善但胜率未达预期，建议进一步调整")
        else:
            print("❌ 优化效果不佳，建议重新评估参数或恢复原配置")

def main():
    print()

    # 检查参数
    if len(sys.argv) > 1:
        old_suffix = ''
        new_suffix = sys.argv[1]
    else:
        old_suffix = ''
        new_suffix = '_v4'

    # 加载原版本结果
    print(f"加载原版本结果 (后缀: '{old_suffix}')...")
    old_data = load_results(old_suffix)
    old_results = {}
    for symbol, df in old_data.items():
        perf = analyze_performance(df, symbol)
        if perf:
            old_results[symbol] = perf

    print(f"加载优化版结果 (后缀: '{new_suffix}')...")
    new_data = load_results(new_suffix)
    new_results = {}
    for symbol, df in new_data.items():
        perf = analyze_performance(df, symbol)
        if perf:
            new_results[symbol] = perf

    print()

    if not old_results and not new_results:
        print("❌ 未找到任何回测结果文件")
        print()
        print("使用方法：")
        print("  1. 默认对比: python3 compare_results.py")
        print("     对比 backtest_trades_*_1h.csv 和 backtest_trades_*_1h_v4.csv")
        print()
        print("  2. 指定后缀: python3 compare_results.py _v4")
        return

    # 打印对比
    print_comparison(old_results, new_results)
    print()

if __name__ == '__main__':
    main()
