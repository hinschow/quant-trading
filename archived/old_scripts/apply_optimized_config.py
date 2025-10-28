#!/usr/bin/env python3
"""
应用优化配置脚本
将优化后的参数应用到策略引擎
"""

import shutil
import os
from datetime import datetime

def backup_original():
    """备份原始配置"""
    original = 'config/strategy_params.py'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f'config/strategy_params_backup_{timestamp}.py'

    if os.path.exists(original):
        shutil.copy(original, backup)
        print(f"✅ 原始配置已备份至: {backup}")
        return backup
    else:
        print(f"⚠️  原始配置文件不存在: {original}")
        return None

def apply_optimized():
    """应用优化配置"""
    optimized = 'config/strategy_params_optimized.py'
    target = 'config/strategy_params.py'

    if not os.path.exists(optimized):
        print(f"❌ 优化配置文件不存在: {optimized}")
        return False

    shutil.copy(optimized, target)
    print(f"✅ 优化配置已应用至: {target}")
    return True

def show_changes():
    """显示主要变更"""
    print("\n" + "="*80)
    print("主要优化变更：")
    print("="*80)

    changes = [
        ("入场信号强度阈值", "0.6 (60%)", "60+ (更高)", "减少低质量交易"),
        ("ADX趋势阈值", "30", "35", "只在强趋势交易"),
        ("止损幅度（趋势策略）", "2.5%", "3.5%", "避免震荡止损"),
        ("止损幅度（BTC/ETH）", "2.5%", "4%", "大盘需要更宽空间"),
        ("止盈幅度（趋势策略）", "5%", "7%", "提高盈亏比"),
        ("止盈幅度（BTC/ETH）", "5%", "8%", "提高盈亏比"),
        ("成交量确认倍数", "1.3x", "1.5x", "要求更强成交量"),
        ("最长持仓时间", "72小时", "96小时", "给趋势更多时间"),
        ("移动止损触发点", "3%", "4%", "更稳健的保护"),
        ("仓位管理（趋势）", "80%", "70%", "更保守的仓位"),
    ]

    print(f"\n{'参数':<25} {'原值':<15} {'新值':<15} {'说明'}")
    print("-"*80)
    for param, old, new, desc in changes:
        print(f"{param:<25} {old:<15} {new:<15} {desc}")

    print("\n" + "="*80)
    print("品种差异化配置（新增）：")
    print("="*80)

    symbols = [
        ("BTC/USDT", "4%止损, 8%止盈", "65信号强度", "波动小，要求高"),
        ("ETH/USDT", "4%止损, 8%止盈", "65信号强度", "波动中等，要求高"),
        ("SOL/USDT", "3.5%止损, 7%止盈", "55信号强度", "表现最好，保持"),
    ]

    print(f"\n{'品种':<15} {'止损/止盈':<25} {'信号要求':<20} {'说明'}")
    print("-"*80)
    for symbol, stops, signal, desc in symbols:
        print(f"{symbol:<15} {stops:<25} {signal:<20} {desc}")

def main():
    print("="*80)
    print("策略参数优化 - 配置应用工具")
    print("="*80)
    print()

    # 1. 备份原始配置
    print("步骤 1: 备份原始配置...")
    backup_file = backup_original()
    print()

    # 2. 显示变更
    show_changes()
    print()

    # 3. 确认应用
    print("="*80)
    response = input("是否应用优化配置？(y/n): ").strip().lower()

    if response == 'y':
        print()
        print("步骤 2: 应用优化配置...")
        if apply_optimized():
            print()
            print("="*80)
            print("✅ 配置优化完成！")
            print("="*80)
            print()
            print("下一步操作：")
            print("1. 在本地执行回测: python3 backtest_engine.py")
            print("2. 对比新旧结果")
            print("3. 如需恢复原配置:")
            if backup_file:
                print(f"   cp {backup_file} config/strategy_params.py")
            print()
        else:
            print("❌ 配置应用失败")
    else:
        print("\n取消操作")

if __name__ == '__main__':
    main()
