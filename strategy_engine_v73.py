"""
策略引擎 v7.3 - 可配置信号过滤系统
支持灵活的指标启用/禁用和权重调整

主要改进：
1. 从 signal_filter_config.py 读取配置
2. 支持3种预设方案（保守/简化/自定义）
3. 动态调整信号阈值和指标权重
4. 市场状态过滤
5. 额外过滤条件

使用方法：
  from strategy_engine_v73 import StrategyEngineV73
  engine = StrategyEngineV73()  # 默认使用 CONSERVATIVE 方案
"""

from strategy_engine import StrategyEngine
from config.signal_filter_config import get_active_config
import logging

logger = logging.getLogger(__name__)


class StrategyEngineV73(StrategyEngine):
    """
    策略引擎 v7.3 - 继承自原策略引擎，添加可配置过滤
    """

    def __init__(self, *args, **kwargs):
        """初始化，加载信号过滤配置"""
        super().__init__(*args, **kwargs)

        # 加载信号过滤配置
        self.filter_config = get_active_config()
        logger.info(f"✅ 信号过滤配置已加载: {self.filter_config['name']}")

        # 打印配置摘要
        self._print_config_summary()

    def _print_config_summary(self):
        """打印配置摘要"""
        config = self.filter_config
        logger.info(f"\n{'='*80}")
        logger.info(f"信号配置: {config['name']}")
        logger.info(f"{'='*80}")

        # 阈值
        logger.info("阈值设置:")
        for key, value in config['thresholds'].items():
            logger.info(f"  {key}: {value}分")

        # 启用的指标
        enabled = [name for name, cfg in config['indicators'].items()
                   if cfg.get('enabled', True)]
        logger.info(f"\n启用指标 ({len(enabled)}/10):")
        logger.info(f"  {', '.join(enabled)}")

        # 市场状态过滤
        allowed_regimes = [regime for regime, allowed in config['market_regime_filter'].items()
                           if allowed]
        logger.info(f"\n允许市场状态:")
        logger.info(f"  {', '.join(allowed_regimes)}")

        logger.info(f"{'='*80}\n")

    def generate_trend_signal(self, df, symbol=None):
        """
        生成趋势信号（应用配置过滤）

        覆盖父类方法，添加配置化权重和过滤
        """
        # 先调用父类方法获取原始信号（父类方法接受symbol参数）
        signal = super().generate_trend_signal(df, symbol)

        # 应用配置过滤
        signal = self._apply_config_filter(signal, 'trend')

        return signal

    def generate_mean_reversion_signal(self, df, symbol=None):
        """
        生成均值回归信号（应用配置过滤）

        覆盖父类方法，添加配置化权重和过滤
        """
        # 先调用父类方法获取原始信号（父类方法不接受symbol参数）
        signal = super().generate_mean_reversion_signal(df)

        # 应用配置过滤
        signal = self._apply_config_filter(signal, 'mean_reversion')

        return signal

    def _apply_config_filter(self, signal: dict, signal_type: str) -> dict:
        """
        应用配置过滤器

        Args:
            signal: 原始信号
            signal_type: 'trend' 或 'mean_reversion'

        Returns:
            过滤后的信号
        """
        config = self.filter_config
        thresholds = config['thresholds']

        # 1. 应用新的阈值
        if signal['action'] == 'BUY':
            threshold_key = f"{signal_type}_buy"
            required_strength = thresholds.get(threshold_key, 40)

            if signal['strength'] < required_strength:
                logger.info(f"⚠️  买入信号强度不足: {signal['strength']} < {required_strength}")
                signal['action'] = 'HOLD'
                signal['reasons'].insert(0, f"信号强度不足（{signal['strength']} < {required_strength}）")

        elif signal['action'] == 'SELL':
            threshold_key = f"{signal_type}_sell"
            required_strength = thresholds.get(threshold_key, 40)

            if signal['strength'] < required_strength:
                logger.info(f"⚠️  卖出信号强度不足: {signal['strength']} < {required_strength}")
                signal['action'] = 'HOLD'
                signal['reasons'].insert(0, f"信号强度不足（{signal['strength']} < {required_strength}）")

        # 2. 应用额外过滤条件
        signal = self._apply_extra_filters(signal)

        return signal

    def _apply_extra_filters(self, signal: dict) -> dict:
        """
        应用额外过滤条件

        Args:
            signal: 信号字典

        Returns:
            过滤后的信号
        """
        if signal['action'] == 'HOLD':
            return signal

        extra_filters = self.filter_config.get('extra_filters', {})
        market_data = signal.get('market_data', {})

        # 过滤：最低ADX要求
        min_adx = extra_filters.get('min_adx')
        if min_adx and 'adx' in market_data:
            if market_data['adx'] < min_adx:
                logger.info(f"⚠️  ADX不足: {market_data['adx']:.1f} < {min_adx}")
                signal['action'] = 'HOLD'
                signal['reasons'].insert(0, f"ADX不足（{market_data['adx']:.1f} < {min_adx}）")
                return signal

        # 过滤：买入时RSI上限
        if signal['action'] == 'BUY':
            max_rsi = extra_filters.get('max_rsi_for_buy')
            if max_rsi and 'rsi' in market_data:
                if market_data['rsi'] > max_rsi:
                    logger.info(f"⚠️  RSI过高: {market_data['rsi']:.1f} > {max_rsi}")
                    signal['action'] = 'HOLD'
                    signal['reasons'].insert(0, f"RSI过高（{market_data['rsi']:.1f} > {max_rsi}）")
                    return signal

        # 过滤：卖出时RSI下限
        if signal['action'] == 'SELL':
            min_rsi = extra_filters.get('min_rsi_for_sell')
            if min_rsi and 'rsi' in market_data:
                if market_data['rsi'] < min_rsi:
                    logger.info(f"⚠️  RSI过低: {market_data['rsi']:.1f} < {min_rsi}")
                    signal['action'] = 'HOLD'
                    signal['reasons'].insert(0, f"RSI过低（{market_data['rsi']:.1f} < {min_rsi}）")
                    return signal

        # 过滤：必须成交量确认
        require_volume = extra_filters.get('require_volume_confirmation', False)
        if require_volume:
            # 检查reasons中是否包含成交量确认
            volume_confirmed = any('成交量' in reason or 'volume' in reason.lower()
                                   for reason in signal['reasons'])
            if not volume_confirmed:
                logger.info("⚠️  缺少成交量确认")
                signal['action'] = 'HOLD'
                signal['reasons'].insert(0, "缺少成交量确认")
                return signal

        return signal

    def generate_signal(self, df, symbol=None):
        """
        生成最终信号（应用市场状态过滤）

        覆盖父类方法，添加市场状态过滤
        """
        # 先调用父类方法获取原始信号
        signal = super().generate_signal(df, symbol)

        # 应用市场状态过滤
        signal = self._apply_market_regime_filter(signal)

        return signal

    def _apply_market_regime_filter(self, signal: dict) -> dict:
        """
        应用市场状态过滤

        Args:
            signal: 信号字典

        Returns:
            过滤后的信号
        """
        if signal['action'] == 'HOLD':
            return signal

        market_regime = signal.get('market_regime')
        if not market_regime:
            return signal

        # 检查当前市场状态是否允许交易
        regime_filter = self.filter_config.get('market_regime_filter', {})
        allowed = regime_filter.get(market_regime, True)

        if not allowed:
            logger.info(f"⚠️  市场状态不允许交易: {market_regime}")
            signal['action'] = 'HOLD'
            signal['reasons'].insert(0, f"市场状态不允许交易（{market_regime}）")

        return signal


# ==================== 测试代码 ====================
if __name__ == '__main__':
    """测试配置化引擎"""
    import pandas as pd
    from data_collector import DataCollector

    # 创建引擎
    engine = StrategyEngineV73(use_hyperliquid=False, use_smart_money=False)

    # 获取测试数据
    collector = DataCollector('binance')
    df = collector.fetch_ohlcv('BTC/USDT', '1h', 500)

    # 生成信号
    signal = engine.generate_signal(df, 'BTC/USDT')

    print(f"\n{'='*80}")
    print(f"测试信号生成")
    print(f"{'='*80}")
    print(f"市场状态: {signal['market_regime']}")
    print(f"操作建议: {signal['action']}")
    print(f"信号强度: {signal['strength']}/100")
    print(f"\n理由:")
    for reason in signal['reasons']:
        print(f"  • {reason}")
    print(f"{'='*80}\n")
