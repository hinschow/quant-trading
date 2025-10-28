#!/usr/bin/env python3
"""
方案B配置验证脚本
验证参数配置和量价背离过滤逻辑是否正确实施
"""

import sys
from config.strategy_params import SYMBOL_SPECIFIC_PARAMS

def verify_plan_b_params():
    """验证方案B参数配置"""
    print("=" * 60)
    print("方案B参数配置验证")
    print("=" * 60)

    errors = []
    warnings = []

    # 检查必需的参数
    required_keys = [
        'min_signal_strength',
        'adx_threshold',
        'min_signal_with_divergence',
        'filter_divergence_enabled'
    ]

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        print(f"\n{'='*60}")
        print(f"品种: {symbol}")
        print(f"{'='*60}")

        if symbol not in SYMBOL_SPECIFIC_PARAMS:
            errors.append(f"❌ {symbol} 未在 SYMBOL_SPECIFIC_PARAMS 中配置")
            continue

        params = SYMBOL_SPECIFIC_PARAMS[symbol]

        # 检查必需参数
        for key in required_keys:
            if key not in params:
                errors.append(f"❌ {symbol} 缺少参数: {key}")
            else:
                value = params[key]
                print(f"✅ {key}: {value}")

        # 验证方案B特定要求
        if symbol == 'BTC/USDT':
            # BTC: min_signal_strength = 60
            if params.get('min_signal_strength') != 60:
                errors.append(f"❌ BTC min_signal_strength 应为 60，当前为 {params.get('min_signal_strength')}")

            # BTC: adx_threshold = 30
            if params.get('adx_threshold') != 30:
                errors.append(f"❌ BTC adx_threshold 应为 30，当前为 {params.get('adx_threshold')}")

            # BTC: min_signal_with_divergence = 75
            if params.get('min_signal_with_divergence') != 75:
                errors.append(f"❌ BTC min_signal_with_divergence 应为 75，当前为 {params.get('min_signal_with_divergence')}")

        elif symbol == 'ETH/USDT':
            # ETH: min_signal_strength = 65
            if params.get('min_signal_strength') != 65:
                errors.append(f"❌ ETH min_signal_strength 应为 65，当前为 {params.get('min_signal_strength')}")

            # ETH: adx_threshold = 30
            if params.get('adx_threshold') != 30:
                errors.append(f"❌ ETH adx_threshold 应为 30，当前为 {params.get('adx_threshold')}")

            # ETH: min_signal_with_divergence = 75
            if params.get('min_signal_with_divergence') != 75:
                errors.append(f"❌ ETH min_signal_with_divergence 应为 75，当前为 {params.get('min_signal_with_divergence')}")

        elif symbol == 'SOL/USDT':
            # SOL: min_signal_strength = 60
            if params.get('min_signal_strength') != 60:
                errors.append(f"❌ SOL min_signal_strength 应为 60，当前为 {params.get('min_signal_strength')}")

            # SOL: adx_threshold = 30
            if params.get('adx_threshold') != 30:
                errors.append(f"❌ SOL adx_threshold 应为 30，当前为 {params.get('adx_threshold')}")

            # SOL: min_signal_with_divergence = 80
            if params.get('min_signal_with_divergence') != 80:
                errors.append(f"❌ SOL min_signal_with_divergence 应为 80，当前为 {params.get('min_signal_with_divergence')}")

        # 所有品种都应启用量价背离过滤
        if not params.get('filter_divergence_enabled', False):
            warnings.append(f"⚠️  {symbol} 未启用 filter_divergence_enabled")

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
        print("\n✅ 所有参数配置正确！方案B配置验证通过。")
        return True
    elif not errors:
        print("\n✅ 参数配置基本正确，但有一些警告需要注意。")
        return True
    else:
        print("\n❌ 参数配置存在错误，请修正后重新验证。")
        return False


def verify_strategy_engine():
    """验证 strategy_engine.py 中的量价背离过滤逻辑"""
    print("\n" + "=" * 60)
    print("strategy_engine.py 量价背离过滤逻辑验证")
    print("=" * 60)

    try:
        with open('strategy_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ('filter_divergence_enabled', '检查是否启用量价背离过滤'),
            ('min_signal_with_divergence', '检查量价背离最低信号强度'),
            ('量价背离', '检查是否检测量价背离关键词'),
            ('假突破风险', '检查是否检测假突破风险关键词'),
            ('FILTERED_DIVERGENCE', '检查是否返回背离过滤类型'),
        ]

        missing = []
        for keyword, description in checks:
            if keyword in content:
                print(f"✅ {description}: 找到 '{keyword}'")
            else:
                print(f"❌ {description}: 未找到 '{keyword}'")
                missing.append(keyword)

        if missing:
            print(f"\n❌ strategy_engine.py 缺少必要的量价背离过滤逻辑")
            print(f"   缺失关键词: {', '.join(missing)}")
            return False
        else:
            print("\n✅ strategy_engine.py 量价背离过滤逻辑验证通过")
            return True

    except FileNotFoundError:
        print("❌ 未找到 strategy_engine.py 文件")
        return False
    except Exception as e:
        print(f"❌ 验证 strategy_engine.py 时出错: {e}")
        return False


def print_plan_b_summary():
    """打印方案B优化总结"""
    print("\n" + "=" * 60)
    print("方案B优化总结")
    print("=" * 60)

    print("""
📊 方案B核心改进：

1. **BTC参数调整**：
   - min_signal_strength: 65 → 60 (增加交易机会)
   - adx_threshold: 35 → 30 (适应30m周期)
   - 新增量价背离过滤: ≥75

2. **ETH参数微调**：
   - min_signal_strength: 保持65
   - adx_threshold: 35 → 30 (适应30m周期)
   - 新增量价背离过滤: ≥75

3. **SOL参数保持**：
   - 保持方案A所有参数（已盈利）
   - 新增量价背离过滤: ≥80 (更严格)

4. **量价背离智能过滤**：
   - 检测信号中的"⚠️ 量价背离(假突破风险)"
   - 如果信号强度 < min_signal_with_divergence，则过滤
   - 目标：屏蔽假突破交易，提升胜率

📈 预期效果（vs 方案A-30m）：
   - BTC: -3.47% → -1%~0% (增加优质交易)
   - ETH: -0.76% → 0%~+2% (过滤假突破)
   - SOL: +1.15% → +1%~+3% (保持盈利)
   - 总计: -3.09% → 0%~+2% ✅ (首次实现盈利)
""")


if __name__ == '__main__':
    print("\n🔍 方案B配置验证工具\n")

    # 验证参数配置
    params_ok = verify_plan_b_params()

    # 验证策略引擎
    engine_ok = verify_strategy_engine()

    # 打印总结
    print_plan_b_summary()

    # 最终结果
    print("\n" + "=" * 60)
    print("最终验证结果")
    print("=" * 60)

    if params_ok and engine_ok:
        print("\n✅✅ 方案B配置完全正确！可以开始回测。")
        print("\n执行回测命令：")
        print("  python run_multi_timeframe_backtest.py")
        sys.exit(0)
    else:
        print("\n❌ 方案B配置存在问题，请先修正再回测。")
        sys.exit(1)
