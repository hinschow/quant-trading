#!/usr/bin/env python3
"""
方案A vs 方案B 回测结果对比分析工具
"""

import pandas as pd
import os
from pathlib import Path

def analyze_trades(csv_path):
    """分析单个交易CSV文件"""
    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)

    # 只分析BUY/SELL配对的交易
    buy_df = df[df['type'] == 'BUY'].copy()
    sell_df = df[df['type'] == 'SELL'].copy()

    if len(buy_df) == 0 or len(sell_df) == 0:
        return {
            'trades': 0,
            'profit_pct': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_holding_hours': 0,
            'max_drawdown': 0
        }

    # 配对交易
    trades = []
    for i, sell in sell_df.iterrows():
        profit_pct = sell['profit_pct']
        if pd.notna(profit_pct):
            trades.append({
                'profit_pct': profit_pct,
                'profit': sell['profit']
            })

    if not trades:
        return None

    trades_df = pd.DataFrame(trades)

    # 计算指标
    total_profit = trades_df['profit'].sum()
    final_value = 10000 + total_profit
    total_return = (final_value - 10000) / 10000 * 100

    wins = len(trades_df[trades_df['profit'] > 0])
    losses = len(trades_df[trades_df['profit'] <= 0])
    win_rate = wins / len(trades_df) * 100 if len(trades_df) > 0 else 0

    total_wins = trades_df[trades_df['profit'] > 0]['profit'].sum()
    total_losses = abs(trades_df[trades_df['profit'] < 0]['profit'].sum())
    profit_factor = total_wins / total_losses if total_losses > 0 else 0

    # 计算平均持仓时间
    holding_times = []
    for i in range(len(buy_df)):
        if i < len(sell_df):
            buy_time = pd.to_datetime(buy_df.iloc[i]['timestamp'])
            sell_time = pd.to_datetime(sell_df.iloc[i]['timestamp'])
            hours = (sell_time - buy_time).total_seconds() / 3600
            holding_times.append(hours)

    avg_holding = sum(holding_times) / len(holding_times) if holding_times else 0

    return {
        'trades': len(trades_df),
        'profit_pct': total_return,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_holding_hours': avg_holding,
        'wins': wins,
        'losses': losses
    }


def compare_plans():
    """对比方案A和方案B的30m回测结果"""
    print("=" * 80)
    print("方案A vs 方案B 回测结果对比（30m周期）")
    print("=" * 80)

    symbols = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']
    results_dir = Path('backtest_results/multi_timeframe/30m')

    # 方案A结果（需要用户指定目录或重命名）
    plan_a_dir = results_dir  # 假设当前是方案A结果
    plan_b_dir = results_dir  # 回测后会覆盖

    print("\n⚠️  注意：请确保在运行方案B回测前，先备份方案A的结果！")
    print("   建议：将方案A结果复制到 backtest_results/plan_a_30m/")
    print()

    # 检查是否有方案A备份
    plan_a_backup = Path('backtest_results/plan_a_30m')
    if plan_a_backup.exists():
        plan_a_dir = plan_a_backup
        print("✅ 找到方案A备份目录")
    else:
        print("⚠️  未找到方案A备份目录，将使用当前结果作为方案A")

    comparison = []

    for symbol in symbols:
        symbol_name = symbol.replace('_', '/')
        print(f"\n{'='*80}")
        print(f"品种: {symbol_name}")
        print(f"{'='*80}")

        # 分析方案A
        plan_a_file = plan_a_dir / f'backtest_trades_{symbol}_30m.csv'
        plan_a_stats = analyze_trades(plan_a_file)

        # 分析方案B
        plan_b_file = results_dir / f'backtest_trades_{symbol}_30m.csv'
        plan_b_stats = analyze_trades(plan_b_file)

        if not plan_a_stats or not plan_b_stats:
            print(f"❌ 缺少 {symbol_name} 的回测数据")
            continue

        print(f"\n方案A结果：")
        print(f"  交易次数: {plan_a_stats['trades']}")
        print(f"  总收益: {plan_a_stats['profit_pct']:.2f}%")
        print(f"  胜率: {plan_a_stats['win_rate']:.2f}%")
        print(f"  盈亏比: {plan_a_stats['profit_factor']:.2f}")
        print(f"  平均持仓: {plan_a_stats['avg_holding_hours']:.1f}h")

        print(f"\n方案B结果：")
        print(f"  交易次数: {plan_b_stats['trades']}")
        print(f"  总收益: {plan_b_stats['profit_pct']:.2f}%")
        print(f"  胜率: {plan_b_stats['win_rate']:.2f}%")
        print(f"  盈亏比: {plan_b_stats['profit_factor']:.2f}")
        print(f"  平均持仓: {plan_b_stats['avg_holding_hours']:.1f}h")

        # 计算改善
        profit_change = plan_b_stats['profit_pct'] - plan_a_stats['profit_pct']
        trades_change = plan_b_stats['trades'] - plan_a_stats['trades']
        win_rate_change = plan_b_stats['win_rate'] - plan_a_stats['win_rate']

        print(f"\n改善情况：")
        profit_emoji = "✅" if profit_change > 0 else "❌" if profit_change < 0 else "➖"
        trades_emoji = "✅" if trades_change > 0 else "❌" if trades_change < 0 else "➖"
        win_rate_emoji = "✅" if win_rate_change > 0 else "❌" if win_rate_change < 0 else "➖"

        print(f"  收益变化: {profit_emoji} {profit_change:+.2f}%")
        print(f"  交易变化: {trades_emoji} {trades_change:+d}笔")
        print(f"  胜率变化: {win_rate_emoji} {win_rate_change:+.2f}%")

        comparison.append({
            'symbol': symbol_name,
            'plan_a_profit': plan_a_stats['profit_pct'],
            'plan_b_profit': plan_b_stats['profit_pct'],
            'profit_change': profit_change,
            'plan_a_trades': plan_a_stats['trades'],
            'plan_b_trades': plan_b_stats['trades'],
            'trades_change': trades_change
        })

    # 总体对比
    if comparison:
        print(f"\n{'='*80}")
        print("总体对比")
        print(f"{'='*80}")

        total_a = sum(r['plan_a_profit'] for r in comparison)
        total_b = sum(r['plan_b_profit'] for r in comparison)
        total_change = total_b - total_a

        trades_a = sum(r['plan_a_trades'] for r in comparison)
        trades_b = sum(r['plan_b_trades'] for r in comparison)

        print(f"\n方案A总收益: {total_a:.2f}%")
        print(f"方案B总收益: {total_b:.2f}%")
        print(f"总改善: {total_change:+.2f}%")

        print(f"\n方案A总交易: {trades_a}笔")
        print(f"方案B总交易: {trades_b}笔")
        print(f"交易变化: {trades_b - trades_a:+d}笔")

        # 判断是否达到预期
        print(f"\n{'='*80}")
        print("是否达到预期目标？")
        print(f"{'='*80}")

        if total_b >= 0:
            print("✅ 总收益实现盈利（目标：0%~+2%）")
        elif total_b > total_a:
            print(f"⚠️  总收益仍为负但有改善（{total_a:.2f}% → {total_b:.2f}%）")
        else:
            print(f"❌ 总收益未改善或恶化")

        # 检查各品种
        btc = next((r for r in comparison if 'BTC' in r['symbol']), None)
        eth = next((r for r in comparison if 'ETH' in r['symbol']), None)
        sol = next((r for r in comparison if 'SOL' in r['symbol']), None)

        if btc:
            if btc['profit_change'] > 0:
                print(f"✅ BTC收益改善 {btc['profit_change']:+.2f}%")
            else:
                print(f"⚠️  BTC收益未改善")

        if eth:
            if eth['plan_b_profit'] >= 0:
                print(f"✅ ETH实现盈利 {eth['plan_b_profit']:.2f}%")
            elif eth['profit_change'] > 0:
                print(f"⚠️  ETH有改善但仍亏损（{eth['plan_a_profit']:.2f}% → {eth['plan_b_profit']:.2f}%）")

        if sol:
            if sol['plan_b_profit'] > 0:
                print(f"✅ SOL保持盈利 {sol['plan_b_profit']:.2f}%")
            else:
                print(f"❌ SOL不再盈利")


if __name__ == '__main__':
    print("\n📊 方案A vs 方案B 对比分析工具\n")

    # 检查目录
    results_dir = Path('backtest_results/multi_timeframe/30m')
    if not results_dir.exists():
        print("❌ 未找到回测结果目录")
        print(f"   请确保 {results_dir} 存在")
        exit(1)

    compare_plans()

    print("\n" + "="*80)
    print("提示：")
    print("="*80)
    print("""
1. 在运行方案B回测前，请先备份方案A结果：
   mkdir -p backtest_results/plan_a_30m
   cp backtest_results/multi_timeframe/30m/*.csv backtest_results/plan_a_30m/

2. 运行方案B回测：
   python run_multi_timeframe_backtest.py

3. 再次运行本脚本查看对比：
   python compare_plan_a_vs_b.py
""")
