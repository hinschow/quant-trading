#!/usr/bin/env python3
"""
配置管理工具
方便查看和修改策略参数
"""

import json
import yaml
from typing import Dict, Any
from config.strategy_params import (
    MARKET_REGIME_PARAMS,
    TREND_FOLLOWING_PARAMS,
    MEAN_REVERSION_PARAMS,
    VOLUME_PARAMS,
    SENTIMENT_PARAMS,
    MARKET_REGIME_STRATEGY,
    OPTIMIZATION_RANGES
)


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.configs = {
            'market_regime': MARKET_REGIME_PARAMS,
            'trend_following': TREND_FOLLOWING_PARAMS,
            'mean_reversion': MEAN_REVERSION_PARAMS,
            'volume': VOLUME_PARAMS,
            'sentiment': SENTIMENT_PARAMS,
            'regime_strategy': MARKET_REGIME_STRATEGY,
            'optimization': OPTIMIZATION_RANGES
        }

    def show_all(self):
        """显示所有配置"""
        print("\n" + "="*80)
        print("📊 当前策略参数配置")
        print("="*80)

        # 市场状态识别参数
        print("\n【1. 市场状态识别参数】")
        print("-" * 80)
        self._print_params(self.configs['market_regime'])

        # 趋势跟踪参数
        print("\n【2. 趋势跟踪策略参数】")
        print("-" * 80)
        self._print_params(self.configs['trend_following'])

        # 均值回归参数
        print("\n【3. 均值回归策略参数】")
        print("-" * 80)
        self._print_params(self.configs['mean_reversion'])

        # 量价分析参数
        print("\n【4. 量价分析参数】")
        print("-" * 80)
        self._print_params(self.configs['volume'])

        # 市场情绪参数
        print("\n【5. 市场情绪参数】")
        print("-" * 80)
        self._print_params(self.configs['sentiment'])

        print("\n" + "="*80)

    def show_category(self, category: str):
        """显示特定类别的配置"""
        if category not in self.configs:
            print(f"❌ 未知类别: {category}")
            print(f"可用类别: {', '.join(self.configs.keys())}")
            return

        print(f"\n【{category.upper()} 参数】")
        print("-" * 80)
        self._print_params(self.configs[category])

    def _print_params(self, params: Dict[str, Any]):
        """打印参数（格式化）"""
        if isinstance(params, dict):
            for key, value in params.items():
                if isinstance(value, dict):
                    print(f"\n  {key}:")
                    for k, v in value.items():
                        print(f"    {k:<30} = {v}")
                else:
                    # 格式化注释
                    comment = self._get_comment(key, value)
                    print(f"  {key:<30} = {value:<15} {comment}")
        else:
            print(params)

    def _get_comment(self, key: str, value: Any) -> str:
        """获取参数注释"""
        comments = {
            # 市场状态
            'adx_trend_threshold': '# ADX > 30 = 强趋势',
            'adx_weak_trend_threshold': '# ADX > 25 = 一般趋势',
            'adx_range_threshold': '# ADX < 18 = 震荡市',
            'bbw_high_threshold': '# BBW > 1.2 = 高波动',
            'bbw_squeeze_threshold': '# BBW < 0.5 = 挤压状态',

            # 趋势跟踪
            'ema_fast': '# 快速EMA周期',
            'ema_slow': '# 慢速EMA周期',
            'stop_loss_pct': '# 止损百分比',
            'take_profit_pct': '# 止盈百分比',

            # 均值回归
            'rsi_oversold': '# RSI超卖阈值',
            'rsi_overbought': '# RSI超买阈值',
            'kdj_enabled': '# 是否启用KDJ指标',

            # 情绪
            'funding_rate_enabled': '# 是否启用资金费率',
            'open_interest_enabled': '# 是否启用持仓量',
        }
        return comments.get(key, '')

    def export_json(self, filepath: str = 'config_backup.json'):
        """导出配置为JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, indent=2, ensure_ascii=False)
        print(f"✅ 配置已导出到: {filepath}")

    def export_yaml(self, filepath: str = 'config_backup.yaml'):
        """导出配置为YAML"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.configs, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ 配置已导出到: {filepath}")

    def get_presets(self) -> Dict[str, Dict]:
        """获取预设配置方案"""
        return {
            'conservative': {
                'name': '保守型（追求稳定）',
                'params': {
                    'stop_loss_pct': 0.01,
                    'take_profit_pct': 0.025,
                    'adx_trend_threshold': 35,
                    'signal_threshold': 40
                }
            },
            'balanced': {
                'name': '均衡型（当前配置）',
                'params': {
                    'stop_loss_pct': 0.015,
                    'take_profit_pct': 0.03,
                    'adx_trend_threshold': 30,
                    'signal_threshold': 30
                }
            },
            'aggressive': {
                'name': '激进型（追求高收益）',
                'params': {
                    'stop_loss_pct': 0.02,
                    'take_profit_pct': 0.05,
                    'adx_trend_threshold': 25,
                    'signal_threshold': 25
                }
            }
        }

    def show_presets(self):
        """显示预设配置方案"""
        presets = self.get_presets()

        print("\n" + "="*80)
        print("📋 预设配置方案")
        print("="*80)

        for key, preset in presets.items():
            print(f"\n【{preset['name']}】")
            print("-" * 40)
            for param, value in preset['params'].items():
                if isinstance(value, float):
                    if value < 1:
                        print(f"  {param:<30} = {value*100:.1f}%")
                    else:
                        print(f"  {param:<30} = {value:.1f}")
                else:
                    print(f"  {param:<30} = {value}")

        print("\n" + "="*80)

    def compare_with_preset(self, preset_name: str):
        """对比当前配置与预设配置"""
        presets = self.get_presets()

        if preset_name not in presets:
            print(f"❌ 未知预设: {preset_name}")
            print(f"可用预设: {', '.join(presets.keys())}")
            return

        preset = presets[preset_name]
        current = {
            'stop_loss_pct': self.configs['trend_following']['stop_loss_pct'],
            'take_profit_pct': self.configs['trend_following']['take_profit_pct'],
            'adx_trend_threshold': self.configs['market_regime']['adx_trend_threshold'],
            'signal_threshold': 30  # 硬编码在策略引擎中
        }

        print(f"\n【当前配置 vs {preset['name']}】")
        print("-" * 80)
        print(f"{'参数':<30} {'当前值':<20} {'预设值':<20} {'差异'}")
        print("-" * 80)

        for param in preset['params'].keys():
            current_val = current[param]
            preset_val = preset['params'][param]

            if isinstance(current_val, float) and current_val < 1:
                current_str = f"{current_val*100:.1f}%"
                preset_str = f"{preset_val*100:.1f}%"
                diff = f"{(preset_val - current_val)*100:+.1f}%"
            else:
                current_str = f"{current_val}"
                preset_str = f"{preset_val}"
                diff = f"{preset_val - current_val:+}"

            print(f"{param:<30} {current_str:<20} {preset_str:<20} {diff}")

        print("-" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='策略参数配置管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看所有配置
  python config_manager.py --show-all

  # 查看特定类别
  python config_manager.py --category trend_following

  # 查看预设方案
  python config_manager.py --show-presets

  # 对比配置
  python config_manager.py --compare conservative

  # 导出配置
  python config_manager.py --export-json config.json
  python config_manager.py --export-yaml config.yaml
        """
    )

    parser.add_argument('--show-all', action='store_true', help='显示所有配置')
    parser.add_argument('--category', help='显示特定类别配置')
    parser.add_argument('--show-presets', action='store_true', help='显示预设方案')
    parser.add_argument('--compare', help='对比预设配置 (conservative/balanced/aggressive)')
    parser.add_argument('--export-json', help='导出为JSON文件')
    parser.add_argument('--export-yaml', help='导出为YAML文件')

    args = parser.parse_args()

    manager = ConfigManager()

    # 如果没有参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return

    # 执行操作
    if args.show_all:
        manager.show_all()

    if args.category:
        manager.show_category(args.category)

    if args.show_presets:
        manager.show_presets()

    if args.compare:
        manager.compare_with_preset(args.compare)

    if args.export_json:
        manager.export_json(args.export_json)

    if args.export_yaml:
        manager.export_yaml(args.export_yaml)


if __name__ == '__main__':
    main()
