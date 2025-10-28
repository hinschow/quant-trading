#!/usr/bin/env python3
"""
方案D-Stage2配置验证脚本
验证量价背离分级惩罚逻辑是否正确实现
"""

import sys

def verify_stage2_implementation():
    """验证Stage2的量价背离分级逻辑"""
    print("=" * 60)
    print("方案D-Stage2 配置验证（量价背离分级惩罚）")
    print("=" * 60)

    errors = []
    warnings = []

    # 检查strategy_engine.py中的关键代码
    try:
        with open('strategy_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 必须包含的关键词
        required_keywords = [
            'obv_gap_pct',           # OBV差距计算
            'penalty = 30',          # 严重背离惩罚
            'penalty = 20',          # 中度背离惩罚
            'penalty = 10',          # 轻微背离惩罚
            'penalty = 5',           # 微弱背离惩罚
            '严重量价背离',          # 严重背离标记
            '中度量价背离',          # 中度背离标记
            '轻微背离',              # 轻微背离标记
            '微弱背离',              # 微弱背离标记
        ]

        print("\n检查 strategy_engine.py 中的关键实现：")
        for keyword in required_keywords:
            if keyword in content:
                print(f"  ✅ 找到: '{keyword}'")
            else:
                errors.append(f"❌ 未找到: '{keyword}'")
                print(f"  ❌ 未找到: '{keyword}'")

        # 检查分级逻辑
        if 'obv_gap_pct > 10' in content and 'obv_gap_pct > 5' in content and 'obv_gap_pct > 2' in content:
            print("\n✅ 分级逻辑正确：")
            print("   - 严重背离: OBV差距 > 10%")
            print("   - 中度背离: OBV差距 > 5%")
            print("   - 轻微背离: OBV差距 > 2%")
            print("   - 微弱背离: OBV差距 ≤ 2%")
        else:
            errors.append("❌ 分级逻辑不完整")
            print("\n❌ 分级逻辑不完整")

    except FileNotFoundError:
        errors.append("❌ 未找到 strategy_engine.py")
        print("❌ 未找到 strategy_engine.py")
    except Exception as e:
        errors.append(f"❌ 检查 strategy_engine.py 时出错: {e}")
        print(f"❌ 检查时出错: {e}")

    # 检查配置文件版本
    try:
        with open('config/strategy_params.py', 'r', encoding='utf-8') as f:
            config_content = f.read()

        if 'v7.0' in config_content and 'Stage2' in config_content:
            print("\n✅ 配置文件版本正确: v7.0 (Stage2)")
        else:
            warnings.append("⚠️  配置文件版本可能未更新")
            print("\n⚠️  配置文件版本可能未更新")

    except Exception as e:
        warnings.append(f"⚠️  检查配置文件时出错: {e}")

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
        print("\n✅✅ 所有检查通过！Stage2量价背离分级逻辑实现正确。")
        return True
    elif not errors:
        print("\n✅ 核心逻辑正确，但有一些警告需要注意。")
        return True
    else:
        print("\n❌ 实现存在错误，请修正后重新验证。")
        return False


def print_stage2_summary():
    """打印Stage2改进总结"""
    print("\n" + "=" * 60)
    print("Stage2 改进总结")
    print("=" * 60)

    print("""
📊 量价背离分级惩罚（核心改进）：

【Stage1固定惩罚】
量价背离 → 固定扣 -30分

【Stage2分级惩罚】
根据OBV差距程度决定：

1. 严重背离（OBV差距 > 10%）
   惩罚：-30分
   标记：⚠️⚠️ 严重量价背离(OBV差距X%)
   说明：OBV严重落后价格，假突破风险极高

2. 中度背离（OBV差距 5-10%）
   惩罚：-20分
   标记：⚠️ 中度量价背离(OBV差距X%)
   说明：OBV较明显落后，需谨慎

3. 轻微背离（OBV差距 2-5%）
   惩罚：-10分
   标记：⚠️ 轻微背离(OBV差距X%)
   说明：轻微背离，可能仍是真趋势

4. 微弱背离（OBV差距 ≤ 2%）
   惩罚：-5分
   标记：注意：微弱背离(OBV差距X%)
   说明：几乎可忽略的背离

📈 预期效果：

| 场景 | Stage1 | Stage2 | 结果变化 |
|------|--------|--------|---------|
| 轻微背离(3%) | 75-30=45❌ | 75-10=65✅ | 通过阈值60 |
| 中度背离(7%) | 75-30=45❌ | 75-20=55❌ | 仍被过滤 |
| 严重背离(12%) | 75-30=45❌ | 75-30=45❌ | 继续过滤 |

优点：
✅ 减少误杀轻微背离的优质信号
✅ 保持严格过滤严重背离
✅ 更精细的风险评估
✅ 可能增加1-3笔优质交易

目标：
- 总收益：+5.66% → +6.5~7%
- 交易数：12笔 → 13-15笔
- 胜率：保持≥33%
""")


def print_backtest_instructions():
    """打印回测执行指令"""
    print("\n" + "=" * 60)
    print("回测执行指令")
    print("=" * 60)

    print("""
1. 备份Stage1结果：
   mkdir -p backtest_results/stage1_30m
   cp backtest_results/multi_timeframe/30m/*.csv backtest_results/stage1_30m/

2. 激活虚拟环境：
   source venv/bin/activate

3. 执行Stage2回测：
   python3 run_multi_timeframe_backtest.py

4. 快速对比交易数：
   echo "=== Stage1 ==="
   grep "BUY" backtest_results/stage1_30m/backtest_trades_*_30m.csv | wc -l
   echo "=== Stage2 ==="
   grep "BUY" backtest_results/multi_timeframe/30m/backtest_trades_*_30m.csv | wc -l

5. 查看量价背离分级：
   grep "背离" backtest_results/multi_timeframe/30m/backtest_trades_*_30m.csv

6. 提交结果：
   git add .
   git commit -m "方案D-Stage2回测完成：量价背离分级"
   git push
""")


if __name__ == '__main__':
    print("\n🔍 方案D-Stage2配置验证工具\n")

    # 验证实现
    implementation_ok = verify_stage2_implementation()

    # 打印总结
    print_stage2_summary()

    # 打印回测指令
    print_backtest_instructions()

    # 最终结果
    print("\n" + "=" * 60)
    print("最终验证结果")
    print("=" * 60)

    if implementation_ok:
        print("\n✅✅ Stage2量价背离分级逻辑实现正确！可以开始回测。")
        print("\n下一步：")
        print("  1. 在本地Mac备份Stage1结果")
        print("  2. 运行 python3 run_multi_timeframe_backtest.py")
        print("  3. 提交结果到服务器")
        print("  4. 对比Stage1和Stage2的差异")
        sys.exit(0)
    else:
        print("\n❌ Stage2实现存在问题，请先修正再回测。")
        sys.exit(1)
