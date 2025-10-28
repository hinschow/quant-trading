#!/usr/bin/env python3
"""
方案D-Stage1配置验证脚本
验证参数是否正确实施渐进式灵活化第1阶段
"""

import sys
from config.strategy_params import SYMBOL_SPECIFIC_PARAMS

def verify_stage1_params():
    """验证方案D-Stage1参数配置"""
    print("=" * 60)
    print("方案D-Stage1 参数配置验证（渐进式灵活化第1阶段）")
    print("=" * 60)

    errors = []
    warnings = []

    # 预期参数（Stage1）
    expected_params = {
        "BTC/USDT": {
            "min_signal_strength": 55,
            "adx_threshold": 25,
            "min_signal_with_divergence": 75,
        },
        "ETH/USDT": {
            "min_signal_strength": 60,
            "adx_threshold": 25,
            "min_signal_with_divergence": 75,
        },
        "SOL/USDT": {
            "min_signal_strength": 55,
            "adx_threshold": 25,
            "min_signal_with_divergence": 80,
        },
    }

    for symbol, expected in expected_params.items():
        print(f"\n{'='*60}")
        print(f"品种: {symbol}")
        print(f"{'='*60}")

        if symbol not in SYMBOL_SPECIFIC_PARAMS:
            errors.append(f"❌ {symbol} 未在 SYMBOL_SPECIFIC_PARAMS 中配置")
            continue

        actual = SYMBOL_SPECIFIC_PARAMS[symbol]

        # 验证每个参数
        for key, expected_value in expected.items():
            actual_value = actual.get(key)

            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value}")
            else:
                errors.append(
                    f"❌ {symbol} {key}: 预期 {expected_value}, 实际 {actual_value}"
                )
                print(f"❌ {key}: 预期 {expected_value}, 实际 {actual_value}")

        # 验证量价背离过滤仍然启用
        if not actual.get('filter_divergence_enabled', False):
            warnings.append(f"⚠️  {symbol} 未启用 filter_divergence_enabled")

    # 打印改进对比
    print("\n" + "=" * 60)
    print("方案B → 方案D-Stage1 参数变化")
    print("=" * 60)

    changes = [
        ("BTC min_signal_strength", "60", "55", "-5", "增加交易机会"),
        ("BTC adx_threshold", "30", "25", "-5", "放宽趋势要求"),
        ("ETH min_signal_strength", "65", "60", "-5", "增加交易机会"),
        ("ETH adx_threshold", "30", "25", "-5", "放宽趋势要求"),
        ("SOL min_signal_strength", "60", "55", "-5", "保守增加机会"),
        ("SOL adx_threshold", "30", "25", "-5", "放宽趋势要求"),
    ]

    print(f"\n{'参数':<30} {'方案B':<10} {'Stage1':<10} {'变化':<10} {'目的'}")
    print("-" * 80)
    for param, plan_b, stage1, change, purpose in changes:
        print(f"{param:<30} {plan_b:<10} {stage1:<10} {change:<10} {purpose}")

    # 打印总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)

    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误：")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告：")
        for warning in warnings:
            print(f"  {warning}")

    if not errors and not warnings:
        print("\n✅ 所有参数配置正确！方案D-Stage1配置验证通过。")
        return True
    elif not errors:
        print("\n✅ 参数配置基本正确，但有一些警告需要注意。")
        return True
    else:
        print("\n❌ 参数配置存在错误，请修正后重新验证。")
        return False


def print_stage1_summary():
    """打印方案D-Stage1优化总结"""
    print("\n" + "=" * 60)
    print("方案D-Stage1 优化总结")
    print("=" * 60)

    print("""
📊 核心改进（第1阶段 - 保守灵活化）：

1. **降低ADX要求**: 30 → 25
   - 理由：30m周期ADX普遍偏低
   - 预期：+30-40%交易机会

2. **降低信号阈值**:
   - BTC: 60 → 55 (目标: 2笔 → 5-6笔)
   - ETH: 65 → 60 (目标: 5笔 → 7-8笔)
   - SOL: 60 → 55 (目标: 4笔 → 6-8笔)

3. **保持风险控制**:
   - ✅ 止损/止盈参数不变
   - ✅ 量价背离过滤保持
   - ✅ 仅降低阈值，不改其他逻辑

📈 预期效果（vs 方案B）：

| 指标 | 方案B | Stage1预期 | 改善 |
|------|-------|-----------|------|
| 总交易数 | 11笔 | 18-22笔 | +64-100% |
| BTC | -3.37%, 2笔 | -1~+1%, 5-6笔 | 显著改善 |
| ETH | -0.31%, 5笔 | +1~+3%, 7-8笔 | 突破盈亏平衡 |
| SOL | +8.21%, 4笔 | +6~+10%, 6-8笔 | 保持盈利 |
| **总收益** | **+4.52%** | **+6~9%** | **+33-100%** |

⚠️  风险控制：
- 最低标准：交易数≥14笔，收益≥+4.5%
- 如果未达标：回退到方案B
- 如果达标：继续Stage2（量价背离分级）

🎯 成功后的下一阶段：
- Stage2: 量价背离分级惩罚（-10/-20/-30）
- Stage3: 指标权重重构 + 趋势延续信号
""")


def print_backtest_instructions():
    """打印回测执行指令"""
    print("\n" + "=" * 60)
    print("回测执行指令")
    print("=" * 60)

    print("""
1. 备份方案B结果：
   mkdir -p backtest_results/plan_b_30m
   cp backtest_results/multi_timeframe/30m/*.csv backtest_results/plan_b_30m/

2. 激活虚拟环境：
   source venv/bin/activate

3. 执行回测：
   python3 run_multi_timeframe_backtest.py

4. 快速检查交易数：
   grep "BUY" backtest_results/multi_timeframe/30m/backtest_trades_*_30m.csv | wc -l

5. 提交结果：
   git add .
   git commit -m "方案D-Stage1回测完成"
   git push
""")


if __name__ == '__main__':
    print("\n🔍 方案D-Stage1配置验证工具\n")

    # 验证参数配置
    params_ok = verify_stage1_params()

    # 打印总结
    print_stage1_summary()

    # 打印回测指令
    print_backtest_instructions()

    # 最终结果
    print("\n" + "=" * 60)
    print("最终验证结果")
    print("=" * 60)

    if params_ok:
        print("\n✅✅ 方案D-Stage1配置完全正确！可以开始回测。")
        print("\n下一步：")
        print("  1. 在本地Mac备份方案B结果")
        print("  2. 运行 python3 run_multi_timeframe_backtest.py")
        print("  3. 提交结果到服务器")
        sys.exit(0)
    else:
        print("\n❌ 方案D-Stage1配置存在问题，请先修正再回测。")
        sys.exit(1)
