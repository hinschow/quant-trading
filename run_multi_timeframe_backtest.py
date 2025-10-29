#!/usr/bin/env python3
"""
多时间周期回测脚本
支持 15m、30m、1h 三个时间周期的对比测试
"""

import subprocess
import sys
import os
from datetime import datetime
import json

def run_backtest(symbol, timeframe, limit, capital=10000, position=1.0, commission=0.001):
    """运行单个品种和时间周期的回测"""
    print(f"\n{'='*80}")
    print(f"回测: {symbol} @ {timeframe} (数据量: {limit})")
    print(f"{'='*80}\n")

    cmd = [
        sys.executable,  # 使用当前 Python 解释器
        'backtest_engine.py',
        symbol,
        '-t', timeframe,
        '--limit', str(limit),
        '--capital', str(capital),
        '--position', str(position),
        '--commission', str(commission)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n✅ {symbol} @ {timeframe} 回测完成\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {symbol} @ {timeframe} 回测失败: {e}\n")
        return False

def calculate_limit(timeframe, days):
    """根据时间周期和天数计算需要的K线数量"""
    bars_per_day = {
        '15m': 24 * 4,      # 96根/天
        '30m': 24 * 2,      # 48根/天
        '1h': 24,           # 24根/天
        '4h': 6,            # 6根/天
        '1d': 1             # 1根/天
    }

    # 加上200根预热数据
    return bars_per_day.get(timeframe, 24) * days + 200

def organize_results(timeframe):
    """整理回测结果到对应目录"""
    target_dir = f'backtest_results/multi_timeframe/{timeframe}'
    os.makedirs(target_dir, exist_ok=True)

    moved_count = 0
    for file in os.listdir('.'):
        if file.startswith('backtest_trades_') and file.endswith(f'_{timeframe}.csv'):
            dest = os.path.join(target_dir, file)
            if os.path.exists(file):
                os.rename(file, dest)
                moved_count += 1
                print(f"  ✓ 移动: {file} → {dest}")

    return moved_count

def main():
    """主函数"""
    print("\n" + "="*80)
    print("多时间周期回测 - 1h、30m、15m 对比")
    print("="*80)
    print()

    # 检查是否在正确的目录
    if not os.path.exists('backtest_engine.py'):
        print("❌ 错误: 请在项目根目录执行此脚本")
        print("   cd /path/to/quant-trading")
        sys.exit(1)

    # 配置 - 从配置文件读取交易对
    try:
        from config.strategy_params import TRADING_SYMBOLS
        symbols = TRADING_SYMBOLS
        print(f"✓ 从配置文件读取到 {len(symbols)} 个交易对")
    except ImportError:
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        print(f"⚠️  未找到配置文件，使用默认交易对: {symbols}")

    # 时间周期配置（可修改 days 参数来调整回测时长）
    # 例如：{'days': 90} = 回测最近90天数据
    timeframes = {
        '1h': {'days': 60, 'desc': '1小时（60天数据）'},
        '30m': {'days': 60, 'desc': '30分钟（60天数据）'},
        '15m': {'days': 60, 'desc': '15分钟（60天数据）'},
    }

    capital = 10000
    position_size = 1.0
    commission = 0.001

    print(f"配置信息:")
    print(f"  交易对: {', '.join(symbols)}")
    print(f"  时间周期:")
    for tf, config in timeframes.items():
        limit = calculate_limit(tf, config['days'])
        print(f"    - {tf}: {config['desc']} (约{limit}根K线)")
    print(f"  初始资金: {capital:,} USDT")
    print(f"  仓位比例: {position_size*100}%")
    print(f"  手续费率: {commission*100}%")
    print()

    # 确认执行
    response = input("是否开始多时间周期回测？(y/n): ").strip().lower()
    if response != 'y':
        print("取消回测")
        sys.exit(0)

    # 执行回测
    start_time = datetime.now()
    all_results = {}

    for timeframe, config in timeframes.items():
        print(f"\n{'#'*80}")
        print(f"# 时间周期: {timeframe} - {config['desc']}")
        print(f"{'#'*80}\n")

        limit = calculate_limit(timeframe, config['days'])
        tf_results = {}

        for symbol in symbols:
            success = run_backtest(symbol, timeframe, limit, capital, position_size, commission)
            tf_results[symbol] = success

        all_results[timeframe] = tf_results

        # 整理结果文件
        print(f"\n整理 {timeframe} 结果文件...")
        moved = organize_results(timeframe)
        print(f"✓ 已移动 {moved} 个文件到 backtest_results/multi_timeframe/{timeframe}/")

    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("多时间周期回测完成总结")
    print("="*80)
    print()
    print(f"总耗时: {duration/60:.1f} 分钟")
    print()

    # 显示结果
    for timeframe in timeframes.keys():
        print(f"\n{timeframe} 周期:")
        for symbol, success in all_results[timeframe].items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"  {symbol:<15} {status}")

    # 保存元数据
    metadata = {
        'run_time': start_time.isoformat(),
        'duration_seconds': duration,
        'symbols': symbols,
        'timeframes': timeframes,
        'capital': capital,
        'results': {tf: {s: 'success' if r else 'failed' for s, r in results.items()}
                   for tf, results in all_results.items()}
    }

    metadata_file = 'backtest_results/multi_timeframe/metadata.json'
    os.makedirs('backtest_results/multi_timeframe', exist_ok=True)
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n元数据已保存: {metadata_file}")
    print()
    print("="*80)
    print("下一步:")
    print("="*80)
    print("  1. 分析各时间周期: python analyze_multi_timeframe.py")
    print("  2. 查看结果目录: dir backtest_results\\multi_timeframe\\")
    print("  3. 对比最佳周期: 查看分析报告")
    print()

if __name__ == '__main__':
    main()
