#!/usr/bin/env python3
"""
Stage1 vs Stage2 回测结果对比分析工具
"""

import pandas as pd
import os
from pathlib import Path

def analyze_trades(csv_path):
    """分析单个交易CSV文件"""
    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)
    buy_df = df[df['type'] == 'BUY']
    sell_df = df[df['type'] == 'SELL']

    if len(sell_df) == 0:
        return {
            'trades': 0,
            'profit_pct': 0,
            'win_rate': 0,
            'wins': 0,
            'losses': 0
        }

    total_profit = sell_df['profit'].sum()
    final_value = 10000 + total_profit
    total_return = (final_value - 10000) / 10000 * 100

    wins = len(sell_df[sell_df['profit'] > 0])
    losses = len(sell_df[sell_df['profit'] <= 0])
    win_rate = wins / len(sell_df) * 100 if len(sell_df) > 0 else 0

    total_wins = sell_df[sell_df['profit'] > 0]['profit'].sum()
    total_losses = abs(sell_df[sell_df['profit'] < 0]['profit'].sum())
    profit_factor = total_wins / total_losses if total_losses > 0 else 0

    return {
        'trades': len(sell_df),
        'profit_pct': total_return,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'wins': wins,
        'losses': losses
    }


def compare_stages():
    """对比Stage1和Stage2的30m回测结果"""
    print("=" * 80)
    print("Stage1 vs Stage2 回测结果对比（30m周期）")
    print("=" * 80)

    symbols = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']

    # Stage1和Stage2结果目录
    stage1_dir = Path('backtest_results/stage1_30m')
    stage2_dir = Path('backtest_results/multi_timeframe/30m')

    # 检查目录
    if not stage1_dir.exists():
        print("\n⚠️  未找到Stage1备份目录")
        print(f"   请运行: mkdir -p {stage1_dir} && cp backtest_results/multi_timeframe/30m/*.csv {stage1_dir}/")
        return

    if not stage2_dir.exists():
        print("\n❌ 未找到Stage2回测结果目录")
        return

    comparison = []

    for symbol in symbols:
        symbol_name = symbol.replace('_', '/')
        print(f"\n{'='*80}")
        print(f"品种: {symbol_name}")
        print(f"{'='*80}")

        # 分析Stage1
        stage1_file = stage1_dir / f'backtest_trades_{symbol}_30m.csv'
        stage1_stats = analyze_trades(stage1_file)

        # 分析Stage2
        stage2_file = stage2_dir / f'backtest_trades_{symbol}_30m.csv'
        stage2_stats = analyze_trades(stage2_file)

        if not stage1_stats or not stage2_stats:
            print(f"❌ 缺少 {symbol_name} 的回测数据")
            continue

        print(f"\nStage1结果：")
        print(f"  交易次数: {stage1_stats['trades']}")
        print(f"  总收益: {stage1_stats['profit_pct']:.2f}%")
        print(f"  胜率: {stage1_stats['win_rate']:.0f}%")
        print(f"  盈亏比: {stage1_stats['profit_factor']:.2f}")

        print(f"\nStage2结果：")
        print(f"  交易次数: {stage2_stats['trades']}")
        print(f"  总收益: {stage2_stats['profit_pct']:.2f}%")
        print(f"  胜率: {stage2_stats['win_rate']:.0f}%")
        print(f"  盈亏比: {stage2_stats['profit_factor']:.2f}")

        # 计算改善
        profit_change = stage2_stats['profit_pct'] - stage1_stats['profit_pct']
        trades_change = stage2_stats['trades'] - stage1_stats['trades']
        win_rate_change = stage2_stats['win_rate'] - stage1_stats['win_rate']

        print(f"\n改善情况：")
        profit_emoji = "✅" if profit_change > 0 else "❌" if profit_change < 0 else "➖"
        trades_emoji = "✅" if trades_change > 0 else "❌" if trades_change < 0 else "➖"
        win_rate_emoji = "✅" if win_rate_change > 0 else "❌" if win_rate_change < 0 else "➖"

        print(f"  收益变化: {profit_emoji} {profit_change:+.2f}%")
        print(f"  交易变化: {trades_emoji} {trades_change:+d}笔")
        print(f"  胜率变化: {win_rate_emoji} {win_rate_change:+.2f}%")

        comparison.append({
            'symbol': symbol_name,
            'stage1_profit': stage1_stats['profit_pct'],
            'stage2_profit': stage2_stats['profit_pct'],
            'profit_change': profit_change,
            'stage1_trades': stage1_stats['trades'],
            'stage2_trades': stage2_stats['trades'],
            'trades_change': trades_change
        })

    # 总体对比
    if comparison:
        print(f"\n{'='*80}")
        print("总体对比")
        print(f"{'='*80}")

        total_stage1 = sum(r['stage1_profit'] for r in comparison)
        total_stage2 = sum(r['stage2_profit'] for r in comparison)
        total_change = total_stage2 - total_stage1

        trades_stage1 = sum(r['stage1_trades'] for r in comparison)
        trades_stage2 = sum(r['stage2_trades'] for r in comparison)

        print(f"\nStage1总收益: {total_stage1:.2f}%")
        print(f"Stage2总收益: {total_stage2:.2f}%")
        print(f"总改善: {total_change:+.2f}%")

        print(f"\nStage1总交易: {trades_stage1}笔")
        print(f"Stage2总交易: {trades_stage2}笔")
        print(f"交易变化: {trades_stage2 - trades_stage1:+d}笔")

        # 判断是否达到预期
        print(f"\n{'='*80}")
        print("是否达到Stage2预期目标？")
        print(f"{'='*80}")

        # 预期目标
        print(f"\n预期目标（Stage2 vs Stage1）:")
        print(f"  - 总收益: +5.66% → +6.5~7%")
        print(f"  - 交易数: 12笔 → 13-15笔")
        print(f"  - 胜率: 保持≥33%")

        print(f"\n实际结果：")
        if total_stage2 >= 6.5:
            print(f"✅ 总收益达到理想目标: {total_stage2:.2f}% ≥ 6.5%")
        elif total_stage2 > total_stage1:
            print(f"⚠️  总收益有改善但未达理想: {total_stage2:.2f}% (目标≥6.5%)")
        else:
            print(f"❌ 总收益未改善或恶化: {total_stage2:.2f}%")

        if trades_stage2 >= 13:
            print(f"✅ 交易数达到目标: {trades_stage2}笔 ≥ 13笔")
        else:
            print(f"⚠️  交易数未达目标: {trades_stage2}笔 (目标≥13笔)")

        # 分析量价背离分级效果
        print(f"\n{'='*80}")
        print("量价背离分级效果分析")
        print(f"{'='*80}")

        print("""
查看Stage2回测中的背离标记：
  grep "背离" backtest_results/multi_timeframe/30m/backtest_trades_*_30m.csv

预期看到：
  - ⚠️⚠️ 严重量价背离(OBV差距X%)
  - ⚠️ 中度量价背离(OBV差距X%)
  - ⚠️ 轻微背离(OBV差距X%)
  - 注意：微弱背离(OBV差距X%)

如果交易数增加，说明轻微背离的信号通过了过滤。
""")


def check_divergence_signals():
    """检查Stage2中的量价背离分级信号"""
    print(f"\n{'='*80}")
    print("Stage2量价背离分级信号检查")
    print(f"{'='*80}")

    stage2_dir = Path('backtest_results/multi_timeframe/30m')

    for symbol in ['BTC', 'ETH', 'SOL']:
        csv_file = stage2_dir / f'backtest_trades_{symbol}_USDT_30m.csv'

        if not csv_file.exists():
            continue

        print(f"\n{symbol}/USDT:")

        try:
            df = pd.read_csv(csv_file)
            buy_df = df[df['type'] == 'BUY']

            divergence_trades = buy_df[buy_df['reasons'].str.contains('背离', na=False)]

            if len(divergence_trades) > 0:
                print(f"  包含背离标记的交易: {len(divergence_trades)}笔")
                for idx, row in divergence_trades.iterrows():
                    reasons = eval(row['reasons']) if isinstance(row['reasons'], str) else row['reasons']
                    divergence_reasons = [r for r in reasons if '背离' in r]
                    strength = row['signal_strength']
                    print(f"    - 强度{strength}: {divergence_reasons}")
            else:
                print(f"  ✅ 无背离标记的交易")

        except Exception as e:
            print(f"  ⚠️  检查出错: {e}")


if __name__ == '__main__':
    print("\n📊 Stage1 vs Stage2 对比分析工具\n")

    # 对比结果
    compare_stages()

    # 检查背离信号
    check_divergence_signals()

    print("\n" + "="*80)
    print("提示")
    print("="*80)
    print("""
如果Stage2结果满意：
1. 提交到Git: git add . && git commit -m "Stage2回测完成" && git push
2. 决定下一步：
   - 继续Stage3（权重重构+趋势延续）
   - 或开始实盘验证（推荐SOL）
   - 或专注SOL+ETH，放弃BTC

如果Stage2结果不理想：
1. 分析新增交易的质量
2. 考虑调整分级阈值（2/5/10 → 3/7/12）
3. 或回退到Stage1配置
""")
