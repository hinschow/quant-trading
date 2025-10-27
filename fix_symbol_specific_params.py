#!/usr/bin/env python3
"""
修复品种差异化参数支持
在策略引擎中应用 SYMBOL_SPECIFIC_PARAMS
"""

import re

def fix_strategy_engine():
    """修复 strategy_engine.py"""
    file_path = 'strategy_engine.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 添加 SYMBOL_SPECIFIC_PARAMS 导入
    old_import = """from config.strategy_params import (
    TREND_FOLLOWING_PARAMS,
    MEAN_REVERSION_PARAMS,
    MARKET_REGIME_PARAMS,
    MARKET_REGIME_STRATEGY,
    VOLUME_PARAMS,
    SENTIMENT_PARAMS
)"""

    new_import = """from config.strategy_params import (
    TREND_FOLLOWING_PARAMS,
    MEAN_REVERSION_PARAMS,
    MARKET_REGIME_PARAMS,
    MARKET_REGIME_STRATEGY,
    VOLUME_PARAMS,
    SENTIMENT_PARAMS,
    SYMBOL_SPECIFIC_PARAMS
)"""

    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✓ 已添加 SYMBOL_SPECIFIC_PARAMS 导入")
    else:
        print("⚠ 未找到原始导入语句，可能已经修改")

    # 2. 在 __init__ 中初始化
    old_init = """        self.market_regime_params = MARKET_REGIME_PARAMS
        self.trend_params = TREND_FOLLOWING_PARAMS
        self.mean_reversion_params = MEAN_REVERSION_PARAMS
        self.volume_params = VOLUME_PARAMS
        self.sentiment_params = SENTIMENT_PARAMS"""

    new_init = """        self.market_regime_params = MARKET_REGIME_PARAMS
        self.trend_params = TREND_FOLLOWING_PARAMS
        self.mean_reversion_params = MEAN_REVERSION_PARAMS
        self.volume_params = VOLUME_PARAMS
        self.sentiment_params = SENTIMENT_PARAMS
        self.symbol_specific_params = SYMBOL_SPECIFIC_PARAMS"""

    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✓ 已在 __init__ 中初始化品种参数")
    else:
        print("⚠ 未找到原始初始化代码")

    # 3. 在 generate_signal 末尾添加品种参数过滤
    # 找到 generate_signal 函数的结尾
    pattern = r'(    def generate_signal\(self.*?)(        return signal)'

    filter_code = '''
        # 应用品种差异化参数过滤
        if symbol and symbol in self.symbol_specific_params:
            symbol_params = self.symbol_specific_params[symbol]
            min_strength = symbol_params.get('min_signal_strength', 0)

            # 如果信号强度不足，转为 HOLD
            if signal.get('strength', 0) < min_strength:
                logger.info(f"⚠️  信号强度 {signal.get('strength', 0)} < 品种要求 {min_strength}，过滤")
                signal = {
                    'type': 'FILTERED',
                    'action': 'HOLD',
                    'strength': signal.get('strength', 0),
                    'reasons': [f'信号强度不足（{signal.get("strength", 0)} < {min_strength}）'],
                    'market_regime': signal.get('market_regime'),
                    'market_data': signal.get('market_data')
                }

        return signal'''

    def replacement(match):
        return match.group(1) + filter_code

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✓ 已添加品种参数过滤逻辑")
    else:
        print("⚠ 未找到 generate_signal 返回语句")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ {file_path} 修复完成")

def main():
    print("="*80)
    print("修复品种差异化参数支持")
    print("="*80)
    print()

    try:
        fix_strategy_engine()
        print()
        print("="*80)
        print("修复完成！")
        print("="*80)
        print()
        print("下一步：")
        print("1. 在本地重新运行回测: python3 run_backtest_all.py")
        print("2. 分析结果: python3 analyze_backtest.py")
        print("3. 对比: python3 compare_results.py _v4")
        print()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
