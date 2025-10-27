#!/usr/bin/env python3
"""
回测结果分析脚本 v2
支持从 backtest_results/ 目录读取结果
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

def find_result_files(version=None):
    """查找回测结果文件"""
    # 优先从 backtest_results 目录查找
    search_paths = [
        'backtest_results/latest',
        'backtest_results/v4_optimized',
        'backtest_results/v3_original',
        '.'
    ]

    if version:
        search_paths.insert(0, f'backtest_results/{version}')

    for base_path in search_paths:
        if os.path.exists(base_path):
            files = [f for f in os.listdir(base_path) if f.startswith('backtest_trades_') and f.endswith('.csv')]
            if files:
                return base_path, files

    return None, []

def analyze_trades(csv_file, symbol):
    """分析单个交易对的回测结果"""
    df = pd.read_csv(csv_file)

    # 基本统计
    total_trades = len(df[df['type'] == 'BUY'])

    # 过滤出有盈亏数据的卖出交易
    sell_trades = df[df['type'] == 'SELL'].copy()
    sell_trades = sell_trades[sell_trades['profit'].notna()]

    if len(sell_trades) == 0:
        return None

    # 计算盈亏统计
    winning_trades = sell_trades[sell_trades['profit'] > 0]
    losing_trades = sell_trades[sell_trades['profit'] < 0]

    total_profit = sell_trades['profit'].sum()
    total_profit_pct = ((sell_trades['value'].iloc[-1] - 10000) / 10000) * 100

    win_rate = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0

    avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0

    max_win = winning_trades['profit'].max() if len(winning_trades) > 0 else 0
    max_loss = losing_trades['profit'].min() if len(losing_trades) > 0 else 0

    # 计算最大回撤
    cumulative_returns = (sell_trades['value'] / 10000 - 1) * 100
    running_max = cumulative_returns.expanding().max()
    drawdown = cumulative_returns - running_max
    max_drawdown = drawdown.min()

    # 计算盈亏比
    profit_factor = abs(winning_trades['profit'].sum() / losing_trades['profit'].sum()) if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0 else float('inf')

    # 计算平均持仓时间
    buy_times = df[df['type'] == 'BUY']['timestamp'].tolist()
    sell_times = df[df['type'] == 'SELL']['timestamp'].tolist()

    holding_periods = []
    for i in range(min(len(buy_times), len(sell_times))):
        buy_time = pd.to_datetime(buy_times[i])
        sell_time = pd.to_datetime(sell_times[i])
        holding_periods.append((sell_time - buy_time).total_seconds() / 3600)

    avg_holding_hours = np.mean(holding_periods) if holding_periods else 0

    # 交易时间范围
    start_date = df['timestamp'].iloc[0]
    end_date = df['timestamp'].iloc[-1]

    # 最终资金
    final_value = sell_trades['value'].iloc[-1]

    # 信号强度统计
    buy_signals = df[df['type'] == 'BUY']
    signal_strengths = buy_signals['signal_strength'].tolist()
    avg_signal_strength = np.mean(signal_strengths) if signal_strengths else 0
    min_signal_strength = min(signal_strengths) if signal_strengths else 0
    max_signal_strength = max(signal_strengths) if signal_strengths else 0

    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_profit': total_profit,
        'total_profit_pct': total_profit_pct,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_win': max_win,
        'max_loss': max_loss,
        'max_drawdown': max_drawdown,
        'profit_factor': profit_factor,
        'avg_holding_hours': avg_holding_hours,
        'final_value': final_value,
        'start_date': start_date,
        'end_date': end_date,
        'avg_signal_strength': avg_signal_strength,
        'min_signal_strength': min_signal_strength,
        'max_signal_strength': max_signal_strength,
    }

def print_analysis(results):
    """打印分析结果"""
    print("=" * 80)
    print(f"回测分析报告 - {results['symbol']}")
    print("=" * 80)
    print(f"\n📅 回测周期: {results['start_date']} 至 {results['end_date']}")
    print(f"\n💰 资金表现:")
    print(f"   初始资金: 10,000.00 USDT")
    print(f"   最终资金: {results['final_value']:,.2f} USDT")
    print(f"   总收益: {results['total_profit']:+,.2f} USDT ({results['total_profit_pct']:+.2f}%)")
    print(f"   最大回撤: {results['max_drawdown']:.2f}%")

    print(f"\n📊 交易统计:")
    print(f"   总交易次数: {results['total_trades']}")
    print(f"   盈利交易: {results['winning_trades']} 次")
    print(f"   亏损交易: {results['losing_trades']} 次")
    print(f"   胜率: {results['win_rate']:.2f}%")

    print(f"\n💵 盈亏分析:")
    print(f"   平均盈利: {results['avg_win']:,.2f} USDT")
    print(f"   平均亏损: {results['avg_loss']:,.2f} USDT")
    print(f"   最大单笔盈利: {results['max_win']:,.2f} USDT")
    print(f"   最大单笔亏损: {results['max_loss']:,.2f} USDT")
    print(f"   盈亏比: {results['profit_factor']:.2f}")

    print(f"\n⏱️  持仓时间:")
    print(f"   平均持仓: {results['avg_holding_hours']:.1f} 小时")

    print(f"\n🎯 信号质量:")
    print(f"   平均信号强度: {results['avg_signal_strength']:.1f}")
    print(f"   最低信号强度: {results['min_signal_strength']:.0f}")
    print(f"   最高信号强度: {results['max_signal_strength']:.0f}")

    # 评级
    print(f"\n🎯 策略评级:")
    rating_score = 0
    comments = []

    if results['total_profit_pct'] > 0:
        rating_score += 2
        comments.append("✓ 总体盈利")
    else:
        comments.append("✗ 总体亏损")

    if results['win_rate'] >= 50:
        rating_score += 2
        comments.append(f"✓ 胜率达标 ({results['win_rate']:.1f}%)")
    else:
        comments.append(f"✗ 胜率偏低 ({results['win_rate']:.1f}%)")

    if results['profit_factor'] > 1:
        rating_score += 2
        comments.append(f"✓ 盈亏比良好 ({results['profit_factor']:.2f})")
    else:
        comments.append(f"✗ 盈亏比不佳 ({results['profit_factor']:.2f})")

    if results['max_drawdown'] > -20:
        rating_score += 2
        comments.append(f"✓ 风险可控 (最大回撤{results['max_drawdown']:.1f}%)")
    else:
        comments.append(f"✗ 回撤较大 ({results['max_drawdown']:.1f}%)")

    if rating_score >= 7:
        rating = "优秀 ⭐⭐⭐⭐⭐"
    elif rating_score >= 5:
        rating = "良好 ⭐⭐⭐⭐"
    elif rating_score >= 3:
        rating = "一般 ⭐⭐⭐"
    else:
        rating = "较差 ⭐⭐"

    print(f"   {rating}")
    for comment in comments:
        print(f"   {comment}")

    print()

def main():
    """主函数"""
    # 解析命令行参数
    version = sys.argv[1] if len(sys.argv) > 1 else None

    # 查找结果文件
    base_path, files = find_result_files(version)

    if not files:
        print("❌ 未找到回测结果文件")
        print("\n请确保:")
        print("  1. 已运行回测: python3 run_backtest_all.py")
        print("  2. 结果文件在以下位置之一:")
        print("     - backtest_results/latest/")
        print("     - backtest_results/v4_optimized/")
        print("     - backtest_results/v3_original/")
        print("     - 当前目录")
        return

    print(f"\n📂 分析路径: {base_path}")
    print()

    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    all_results = []

    for symbol in symbols:
        filename = f"backtest_trades_{symbol.replace('/', '_')}_1h.csv"
        filepath = os.path.join(base_path, filename)

        if not os.path.exists(filepath):
            print(f"⚠️  未找到 {symbol} 的回测结果: {filepath}")
            continue

        try:
            results = analyze_trades(filepath, symbol)
            if results:
                all_results.append(results)
                print_analysis(results)
        except Exception as e:
            print(f"❌ 分析 {symbol} 时出错: {e}")

    # 综合比较
    if len(all_results) > 1:
        print("=" * 80)
        print("综合对比")
        print("=" * 80)
        print(f"\n{'交易对':<15} {'收益率':<12} {'胜率':<10} {'盈亏比':<10} {'最大回撤':<12} {'信号强度':<10}")
        print("-" * 80)
        for r in all_results:
            print(f"{r['symbol']:<15} {r['total_profit_pct']:>+10.2f}%  {r['win_rate']:>8.2f}%  {r['profit_factor']:>8.2f}  {r['max_drawdown']:>10.2f}%  {r['avg_signal_strength']:>8.1f}")

        # 找出最佳表现
        best_profit = max(all_results, key=lambda x: x['total_profit_pct'])
        best_winrate = max(all_results, key=lambda x: x['win_rate'])
        best_profit_factor = max(all_results, key=lambda x: x['profit_factor'] if x['profit_factor'] != float('inf') else 0)

        print(f"\n🏆 最佳表现:")
        print(f"   最高收益率: {best_profit['symbol']} ({best_profit['total_profit_pct']:+.2f}%)")
        print(f"   最高胜率: {best_winrate['symbol']} ({best_winrate['win_rate']:.2f}%)")
        print(f"   最佳盈亏比: {best_profit_factor['symbol']} ({best_profit_factor['profit_factor']:.2f})")

        # 计算总体表现
        total_value = sum(r['final_value'] for r in all_results)
        initial_total = 10000 * len(all_results)
        total_return = ((total_value - initial_total) / initial_total) * 100
        avg_winrate = sum(r['win_rate'] for r in all_results) / len(all_results)

        print(f"\n📈 整体组合表现:")
        print(f"   总投入: {initial_total:,.2f} USDT (每个品种 10,000 USDT)")
        print(f"   总资产: {total_value:,.2f} USDT")
        print(f"   总收益率: {total_return:+.2f}%")
        print(f"   平均胜率: {avg_winrate:.2f}%")
        print()

if __name__ == '__main__':
    main()
