#!/usr/bin/env python3
"""
回测结果分析脚本
分析多周期回测结果，找出最优周期
"""

import json
import pandas as pd
import os
from pathlib import Path


def analyze_timeframe_results():
    """分析多周期回测结果"""

    print("=" * 80)
    print("📊 多周期回测结果分析")
    print("=" * 80)
    print()

    # 读取metadata
    metadata_file = "backtest_results/multi_timeframe/metadata.json"
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            print(f"回测时间: {metadata.get('start_date')} ~ {metadata.get('end_date')}")
            print(f"交易对: {', '.join(metadata.get('symbols', []))}")
            print(f"测试周期: {', '.join(metadata.get('timeframes', []))}")
            print()

    timeframes = ['15m', '30m', '1h']
    results_base = Path("backtest_results/multi_timeframe")

    # 存储所有结果
    all_results = {}

    for timeframe in timeframes:
        timeframe_dir = results_base / timeframe

        if not timeframe_dir.exists():
            continue

        print(f"\n{'=' * 80}")
        print(f"⏰ {timeframe} 周期结果")
        print(f"{'=' * 80}")

        csv_files = list(timeframe_dir.glob("backtest_trades_*.csv"))

        if not csv_files:
            print(f"  ⚠️  没有找到交易记录")
            continue

        timeframe_summary = {
            'total_trades': 0,
            'total_profit': 0,
            'win_count': 0,
            'symbols': {}
        }

        for csv_file in sorted(csv_files):
            # 从文件名提取交易对
            symbol = csv_file.stem.replace('backtest_trades_', '').replace('_' + timeframe, '')

            # 读取交易记录
            try:
                df = pd.read_csv(csv_file)

                if len(df) == 0:
                    print(f"\n  📊 {symbol:15} 无交易记录")
                    continue

                # 计算统计
                trades = len(df)
                total_profit = df['profit_pct'].sum()
                wins = len(df[df['profit_pct'] > 0])
                losses = len(df[df['profit_pct'] <= 0])
                win_rate = (wins / trades * 100) if trades > 0 else 0

                avg_profit = df[df['profit_pct'] > 0]['profit_pct'].mean() if wins > 0 else 0
                avg_loss = abs(df[df['profit_pct'] <= 0]['profit_pct'].mean()) if losses > 0 else 0
                profit_factor = (avg_profit / avg_loss) if avg_loss > 0 else 0

                max_profit = df['profit_pct'].max()
                max_loss = df['profit_pct'].min()

                # 保存结果
                timeframe_summary['total_trades'] += trades
                timeframe_summary['total_profit'] += total_profit
                timeframe_summary['win_count'] += wins
                timeframe_summary['symbols'][symbol] = {
                    'trades': trades,
                    'profit': total_profit,
                    'win_rate': win_rate,
                    'profit_factor': profit_factor
                }

                # 显示结果
                print(f"\n  📊 {symbol:15}")
                print(f"     交易次数: {trades:2d}笔")
                print(f"     总收益:   {total_profit:+7.2f}%")
                print(f"     胜率:     {win_rate:5.1f}%  ({wins}胜{losses}负)")
                print(f"     盈亏比:   {profit_factor:5.2f}")
                print(f"     最大盈利: {max_profit:+7.2f}%")
                print(f"     最大亏损: {max_loss:+7.2f}%")

            except Exception as e:
                print(f"\n  ❌ {symbol} 读取失败: {e}")

        # 保存周期汇总
        all_results[timeframe] = timeframe_summary

        # 显示周期汇总
        if timeframe_summary['total_trades'] > 0:
            overall_win_rate = (timeframe_summary['win_count'] / timeframe_summary['total_trades'] * 100)
            print(f"\n  {'─' * 76}")
            print(f"  📈 {timeframe} 周期汇总:")
            print(f"     总交易: {timeframe_summary['total_trades']}笔")
            print(f"     总收益: {timeframe_summary['total_profit']:+.2f}%")
            print(f"     整体胜率: {overall_win_rate:.1f}%")

    # 对比分析
    print(f"\n\n{'=' * 80}")
    print("🏆 周期对比")
    print(f"{'=' * 80}")

    comparison = []
    for tf, summary in all_results.items():
        if summary['total_trades'] > 0:
            comparison.append({
                'timeframe': tf,
                'trades': summary['total_trades'],
                'profit': summary['total_profit'],
                'win_rate': summary['win_count'] / summary['total_trades'] * 100
            })

    if comparison:
        # 按收益排序
        comparison.sort(key=lambda x: x['profit'], reverse=True)

        print(f"\n{'周期':<8} {'交易数':<10} {'总收益':<12} {'胜率':<10}")
        print("─" * 80)

        for i, item in enumerate(comparison):
            emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            print(f"{emoji} {item['timeframe']:<6} {item['trades']:<10d} {item['profit']:+10.2f}%  {item['win_rate']:>6.1f}%")

        # 推荐
        best = comparison[0]
        print(f"\n✅ 推荐周期: {best['timeframe']}")
        print(f"   理由: 收益最高 ({best['profit']:+.2f}%), 交易次数适中 ({best['trades']}笔)")

    print(f"\n{'=' * 80}")
    print("📁 详细结果")
    print(f"{'=' * 80}")
    print("\n查看各周期详细交易记录:")
    for timeframe in timeframes:
        print(f"  {timeframe}: backtest_results/multi_timeframe/{timeframe}/")

    print(f"\n{'=' * 80}")
    print("🎯 下一步建议")
    print(f"{'=' * 80}")

    if comparison and comparison[0]['profit'] > 5:
        print("""
✅ 回测效果良好！建议：

1. 查看最优周期的详细交易记录
   open backtest_results/multi_timeframe/{}/backtest_trades_XXX.csv

2. 准备实盘测试（小资金）
   - 配置交易所API
   - 使用$1000-2000测试
   - 运行2周观察效果

3. 实盘前的准备
   - 阅读: 如何配置交易对.md
   - 设置风控参数
   - 准备监控工具
""".format(comparison[0]['timeframe']))
    elif comparison:
        print("""
⚠️  回测效果一般，建议：

1. 优化交易对选择
   - 减少低收益币种
   - 专注高收益币种

2. 调整策略参数
   - 优化信号强度阈值
   - 调整止盈止损比例

3. 延长回测周期
   - 获取更多历史数据
   - 验证策略稳定性
""")
    else:
        print("\n⚠️  未找到有效的回测结果")

    print()


if __name__ == "__main__":
    analyze_timeframe_results()
