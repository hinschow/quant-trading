#!/usr/bin/env python3
"""
运行所有品种的回测
"""

import subprocess
import sys
import os
from datetime import datetime

def run_backtest(symbol, timeframe='1h', capital=10000, position=1.0, commission=0.001):
    """运行单个品种的回测"""
    print(f"\n{'='*80}")
    print(f"开始回测: {symbol} ({timeframe})")
    print(f"{'='*80}\n")

    cmd = [
        'python3',
        'backtest_engine.py',
        symbol,
        '-t', timeframe,
        '--capital', str(capital),
        '--position', str(position),
        '--commission', str(commission)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n✅ {symbol} 回测完成\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {symbol} 回测失败: {e}\n")
        return False

def main():
    """主函数"""
    print("\n" + "="*80)
    print("量化交易回测 - 批量执行")
    print("="*80)
    print()

    # 检查是否在正确的目录
    if not os.path.exists('backtest_engine.py'):
        print("❌ 错误: 请在项目根目录执行此脚本")
        print("   cd /path/to/quant-trading")
        sys.exit(1)

    # 配置
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    timeframe = '1h'
    capital = 10000
    position_size = 1.0
    commission = 0.001

    print(f"配置信息:")
    print(f"  交易对: {', '.join(symbols)}")
    print(f"  时间周期: {timeframe}")
    print(f"  初始资金: {capital:,} USDT")
    print(f"  仓位比例: {position_size*100}%")
    print(f"  手续费率: {commission*100}%")
    print()

    # 确认执行
    response = input("是否开始回测？(y/n): ").strip().lower()
    if response != 'y':
        print("取消回测")
        sys.exit(0)

    # 执行回测
    start_time = datetime.now()
    results = {}

    for symbol in symbols:
        success = run_backtest(symbol, timeframe, capital, position_size, commission)
        results[symbol] = success

    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("回测完成总结")
    print("="*80)
    print()
    print(f"总耗时: {duration:.1f} 秒")
    print()
    print("结果:")
    for symbol, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {symbol:<15} {status}")

    # 移动文件到 backtest_results/latest
    print()
    print("整理结果文件...")

    # 创建目录
    os.makedirs('backtest_results/latest', exist_ok=True)

    moved_files = []
    for symbol in symbols:
        filename = f"backtest_trades_{symbol.replace('/', '_')}_{timeframe}.csv"
        if os.path.exists(filename):
            dest = f"backtest_results/latest/{filename}"
            os.rename(filename, dest)
            size = os.path.getsize(dest)
            moved_files.append((dest, size))
            print(f"  ✓ 已移动: {dest} ({size} bytes)")

    print()
    print("下一步:")
    print("  1. 分析结果: python3 analyze_backtest_v2.py")
    print("  2. 查看结果: ls -lh backtest_results/latest/")
    print("  3. 如需保存版本: cp -r backtest_results/latest backtest_results/v4_optimized")
    print()

if __name__ == '__main__':
    main()
