"""
策略引擎 - 市场状态识别 + 信号生成
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from utils.indicators import (
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_adx,
    calculate_bollinger_bands,
    calculate_bbw,
    calculate_atr
)
from config.strategy_params import (
    TREND_FOLLOWING_PARAMS,
    MEAN_REVERSION_PARAMS,
    MARKET_REGIME_PARAMS,
    MARKET_REGIME_STRATEGY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyEngine:
    """策略引擎 - 负责市场分析和信号生成"""

    def __init__(self):
        """初始化策略引擎"""
        self.market_regime_params = MARKET_REGIME_PARAMS
        self.trend_params = TREND_FOLLOWING_PARAMS
        self.mean_reversion_params = MEAN_REVERSION_PARAMS
        logger.info("✅ 策略引擎初始化完成")

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: OHLCV数据

        Returns:
            添加了指标的DataFrame
        """
        logger.info("📊 开始计算技术指标...")

        # 趋势指标
        df['ema_50'] = calculate_ema(df, self.trend_params['ema_fast'])
        df['ema_200'] = calculate_ema(df, self.trend_params['ema_slow'])

        # MACD
        macd, signal, hist = calculate_macd(
            df,
            self.trend_params['macd_fast'],
            self.trend_params['macd_slow'],
            self.trend_params['macd_signal']
        )
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist

        # RSI
        df['rsi'] = calculate_rsi(df, self.mean_reversion_params['rsi_period'])

        # ADX
        adx, plus_di, minus_di = calculate_adx(df, self.market_regime_params['adx_period'])
        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di

        # Bollinger Bands
        upper, middle, lower = calculate_bollinger_bands(
            df,
            self.mean_reversion_params['bb_period'],
            self.mean_reversion_params['bb_std']
        )
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower

        # BBW (Bollinger Band Width)
        df['bbw'] = calculate_bbw(df, self.market_regime_params['bbw_period'])
        df['bbw_ma'] = df['bbw'].rolling(self.market_regime_params['bbw_ma_period']).mean()

        # ATR (Average True Range)
        df['atr'] = calculate_atr(df, 14)

        logger.info("✅ 技术指标计算完成")
        return df

    def identify_market_regime(self, df: pd.DataFrame) -> str:
        """
        识别当前市场状态

        Args:
            df: 包含指标的DataFrame

        Returns:
            市场状态: STRONG_TREND, TREND, RANGE, SQUEEZE, NEUTRAL
        """
        latest = df.iloc[-1]

        adx = latest['adx']
        bbw = latest['bbw']
        bbw_ma = latest['bbw_ma']

        adx_trend = self.market_regime_params['adx_trend_threshold']
        adx_range = self.market_regime_params['adx_range_threshold']
        bbw_high = self.market_regime_params['bbw_high_threshold']
        bbw_squeeze = self.market_regime_params['bbw_squeeze_threshold']

        # 强趋势 + 高波动
        if adx > adx_trend and bbw > bbw_high:
            return 'STRONG_TREND'

        # 趋势 + 正常波动
        elif adx > self.market_regime_params['adx_weak_trend_threshold'] and bbw > bbw_ma:
            return 'TREND'

        # 震荡 + 低波动
        elif adx < adx_range and bbw < bbw_ma:
            return 'RANGE'

        # 挤压（波动极低，可能爆发）
        elif bbw < bbw_squeeze:
            return 'SQUEEZE'

        # 中性
        else:
            return 'NEUTRAL'

    def generate_trend_signal(self, df: pd.DataFrame) -> Dict:
        """
        趋势跟随信号（放宽条件，更实用）

        Args:
            df: 包含指标的DataFrame

        Returns:
            信号字典
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signal = {
            'type': 'TREND_FOLLOWING',
            'action': 'HOLD',
            'strength': 0,
            'reasons': []
        }

        # EMA金叉/死叉
        ema_cross_up = prev['ema_50'] <= prev['ema_200'] and latest['ema_50'] > latest['ema_200']
        ema_cross_down = prev['ema_50'] >= prev['ema_200'] and latest['ema_50'] < latest['ema_200']

        # MACD金叉/死叉
        macd_cross_up = prev['macd'] <= prev['macd_signal'] and latest['macd'] > latest['macd_signal']
        macd_cross_down = prev['macd'] >= prev['macd_signal'] and latest['macd'] < latest['macd_signal']

        # 趋势状态
        in_uptrend = latest['ema_50'] > latest['ema_200']
        in_downtrend = latest['ema_50'] < latest['ema_200']

        # MACD 状态
        macd_bullish = latest['macd'] > latest['macd_signal']
        macd_bearish = latest['macd'] < latest['macd_signal']

        # RSI 状态（放宽上限，适应持续上涨）
        rsi = latest['rsi']
        rsi_bullish = 40 < rsi < 80  # 扩大到80，允许强趋势中的高RSI
        rsi_bearish = 20 < rsi < 60  # RSI 在健康的空头区间
        rsi_very_strong = rsi > 70  # 非常强劲的多头

        # 买入信号（增强持续上涨检测）
        buy_strength = 0
        buy_reasons = []

        if ema_cross_up:
            buy_strength += 50
            buy_reasons.append('EMA金叉(50上穿200)')
        elif in_uptrend:
            buy_strength += 20
            buy_reasons.append('处于上升趋势')

            # 检测强劲上涨：价格远高于EMA200
            price_above_ema200_pct = (latest['close'] - latest['ema_200']) / latest['ema_200'] * 100
            if price_above_ema200_pct > 5:  # 价格比EMA200高5%以上
                buy_strength += 10
                buy_reasons.append(f'强劲上涨(价格高于EMA200 {price_above_ema200_pct:.1f}%)')

            # 检测EMA向上发散（趋势加速）
            ema_spread_pct = (latest['ema_50'] - latest['ema_200']) / latest['ema_200'] * 100
            if ema_spread_pct > 3:  # EMA50比EMA200高3%以上
                buy_strength += 10
                buy_reasons.append('EMA向上发散(趋势加速)')

        if macd_cross_up:
            buy_strength += 40
            buy_reasons.append('MACD金叉')
        elif macd_bullish:
            buy_strength += 15
            buy_reasons.append('MACD多头排列')

        # RSI判断（放宽限制）
        if rsi_bullish:
            buy_strength += 15
            buy_reasons.append(f'RSI健康({rsi:.1f})')
        elif rsi_very_strong and in_uptrend:  # 强趋势中允许高RSI
            buy_strength += 10
            buy_reasons.append(f'RSI强劲({rsi:.1f}，强势上涨)')

        # ADX 确认（可选）
        if latest['adx'] > 25:
            buy_strength += 10
            buy_reasons.append(f'趋势明确(ADX:{latest["adx"]:.1f})')

        # 强趋势额外加分
        if latest['adx'] > 40:
            buy_strength += 5
            buy_reasons.append(f'极强趋势(ADX:{latest["adx"]:.1f})')

        # 如果信号强度 > 30，发出买入信号
        if buy_strength >= 30:
            signal['action'] = 'BUY'
            signal['strength'] = min(buy_strength, 100)
            signal['reasons'] = buy_reasons

        # 卖出信号（增强持续下跌检测）
        else:
            sell_strength = 0
            sell_reasons = []

            if ema_cross_down:
                sell_strength += 50
                sell_reasons.append('EMA死叉(50下穿200)')
            elif in_downtrend:
                sell_strength += 20
                sell_reasons.append('处于下降趋势')

                # 检测强劲下跌：价格远低于EMA200
                price_below_ema200_pct = (latest['ema_200'] - latest['close']) / latest['ema_200'] * 100
                if price_below_ema200_pct > 5:  # 价格比EMA200低5%以上
                    sell_strength += 10
                    sell_reasons.append(f'强劲下跌(价格低于EMA200 {price_below_ema200_pct:.1f}%)')

                # 检测EMA向下发散
                ema_spread_pct = (latest['ema_200'] - latest['ema_50']) / latest['ema_200'] * 100
                if ema_spread_pct > 3:
                    sell_strength += 10
                    sell_reasons.append('EMA向下发散(趋势加速)')

            if macd_cross_down:
                sell_strength += 40
                sell_reasons.append('MACD死叉')
            elif macd_bearish:
                sell_strength += 15
                sell_reasons.append('MACD空头排列')

            if rsi_bearish:
                sell_strength += 15
                sell_reasons.append(f'RSI偏弱({rsi:.1f})')
            elif rsi < 20 and in_downtrend:  # 极度超卖
                sell_strength += 10
                sell_reasons.append(f'RSI极弱({rsi:.1f}，强势下跌)')

            if latest['adx'] > 25:
                sell_strength += 10
                sell_reasons.append(f'趋势明确(ADX:{latest["adx"]:.1f})')

            # 强趋势额外加分
            if latest['adx'] > 40:
                sell_strength += 5
                sell_reasons.append(f'极强趋势(ADX:{latest["adx"]:.1f})')

            # 如果信号强度 > 30，发出卖出信号
            if sell_strength >= 30:
                signal['action'] = 'SELL'
                signal['strength'] = min(sell_strength, 100)
                signal['reasons'] = sell_reasons

        return signal

    def generate_mean_reversion_signal(self, df: pd.DataFrame) -> Dict:
        """
        均值回归信号（震荡市场）

        Args:
            df: 包含指标的DataFrame

        Returns:
            信号字典
        """
        latest = df.iloc[-1]

        signal = {
            'type': 'MEAN_REVERSION',
            'action': 'HOLD',
            'strength': 0,
            'reasons': []
        }

        rsi = latest['rsi']
        close = latest['close']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_middle = latest['bb_middle']

        # 计算布林带位置（0=下轨，0.5=中轨，1=上轨）
        bb_range = bb_upper - bb_lower
        bb_position = (close - bb_lower) / bb_range if bb_range > 0 else 0.5

        # 买入信号（放宽条件）
        buy_strength = 0
        buy_reasons = []

        # 条件1: RSI 超卖（降低到 35）
        if rsi < 35:
            buy_strength += int((35 - rsi) * 2)
            buy_reasons.append(f'RSI偏低({rsi:.1f})')

        # 条件2: 价格接近布林带下轨（放宽到下方 30%）
        if bb_position < 0.3:
            buy_strength += int((0.3 - bb_position) * 100)
            buy_reasons.append(f'价格接近布林下轨')

        # 如果有任一条件满足，发出买入信号
        if buy_strength > 20:  # 信号强度 > 20 就提示
            signal['action'] = 'BUY'
            signal['strength'] = min(buy_strength, 100)
            signal['reasons'] = buy_reasons

        # 卖出信号（放宽条件）
        else:
            sell_strength = 0
            sell_reasons = []

            # 条件1: RSI 超买（降低到 65）
            if rsi > 65:
                sell_strength += int((rsi - 65) * 2)
                sell_reasons.append(f'RSI偏高({rsi:.1f})')

            # 条件2: 价格接近布林带上轨（放宽到上方 30%）
            if bb_position > 0.7:
                sell_strength += int((bb_position - 0.7) * 100)
                sell_reasons.append(f'价格接近布林上轨')

            # 如果有任一条件满足，发出卖出信号
            if sell_strength > 20:
                signal['action'] = 'SELL'
                signal['strength'] = min(sell_strength, 100)
                signal['reasons'] = sell_reasons

        return signal

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        生成综合交易信号

        Args:
            df: OHLCV数据

        Returns:
            完整的交易信号
        """
        # 计算指标
        df = self.calculate_all_indicators(df)

        # 识别市场状态
        market_regime = self.identify_market_regime(df)
        logger.info(f"🎯 当前市场状态: {market_regime}")

        # 根据市场状态选择策略
        regime_strategy = MARKET_REGIME_STRATEGY.get(market_regime, {})
        strategy_type = regime_strategy.get('strategy', 'trend_following')

        # 生成信号
        if strategy_type == 'trend_following' or market_regime in ['STRONG_TREND', 'TREND']:
            signal = self.generate_trend_signal(df)
        elif strategy_type == 'mean_reversion' or market_regime == 'RANGE':
            signal = self.generate_mean_reversion_signal(df)
        elif market_regime == 'SQUEEZE':
            # 挤压状态，等待突破
            signal = {
                'type': 'BREAKOUT_WAIT',
                'action': 'HOLD',
                'strength': 0,
                'reasons': ['市场挤压，等待突破']
            }
        else:
            signal = {
                'type': 'NEUTRAL',
                'action': 'HOLD',
                'strength': 0,
                'reasons': ['市场中性，观望']
            }

        # 添加市场状态信息
        signal['market_regime'] = market_regime
        signal['market_data'] = self._get_market_summary(df)

        # 添加具体的交易价格（买入价、止盈价、止损价）
        signal['trading_plan'] = self._calculate_trading_plan(df, signal, market_regime)

        return signal

    def _calculate_trading_plan(self, df: pd.DataFrame, signal: Dict, market_regime: str) -> Dict:
        """
        计算具体的交易计划（买入价、止盈价、止损价）

        Args:
            df: DataFrame
            signal: 信号字典
            market_regime: 市场状态

        Returns:
            交易计划字典
        """
        latest = df.iloc[-1]
        current_price = float(latest['close'])
        action = signal['action']

        # 如果是持有，不需要计算
        if action == 'HOLD':
            return {
                'entry_price': None,
                'stop_loss_price': None,
                'take_profit_price': None,
                'risk_reward_ratio': None
            }

        # 根据市场状态选择参数
        if market_regime in ['STRONG_TREND', 'TREND']:
            # 趋势市场参数
            stop_loss_pct = self.trend_params['stop_loss_pct']  # 1.5%
            take_profit_pct = self.trend_params['take_profit_pct']  # 3%
        else:
            # 震荡市场参数
            stop_loss_pct = self.mean_reversion_params['stop_loss_pct']  # 1.5%
            take_profit_pct = 0.02  # 震荡市2%止盈

        # 计算买入价（当前价格）
        entry_price = current_price

        # 计算止损和止盈价格
        if action == 'BUY':
            # 买入信号
            stop_loss_price = entry_price * (1 - stop_loss_pct)  # 下方止损
            take_profit_price = entry_price * (1 + take_profit_pct)  # 上方止盈
        else:  # SELL
            # 卖出信号（做空）
            stop_loss_price = entry_price * (1 + stop_loss_pct)  # 上方止损
            take_profit_price = entry_price * (1 - take_profit_pct)  # 下方止盈

        # 计算风险回报比
        risk = abs(entry_price - stop_loss_price)
        reward = abs(take_profit_price - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0

        return {
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'risk_reward_ratio': risk_reward_ratio,
            'stop_loss_pct': stop_loss_pct * 100,  # 转为百分比
            'take_profit_pct': take_profit_pct * 100
        }

    def _get_market_summary(self, df: pd.DataFrame) -> Dict:
        """获取市场摘要信息"""
        latest = df.iloc[-1]

        return {
            'price': float(latest['close']),
            'ema_50': float(latest['ema_50']),
            'ema_200': float(latest['ema_200']),
            'rsi': float(latest['rsi']),
            'macd': float(latest['macd']),
            'macd_signal': float(latest['macd_signal']),
            'adx': float(latest['adx']),
            'bbw': float(latest['bbw']),
            'atr': float(latest['atr']),
            'bb_upper': float(latest['bb_upper']),
            'bb_lower': float(latest['bb_lower']),
        }


if __name__ == '__main__':
    # 测试代码
    from data_collector import DataCollector

    collector = DataCollector('binance')
    engine = StrategyEngine()

    # 获取BTC数据
    df = collector.fetch_ohlcv('BTC/USDT', '1h', 500)

    # 生成信号
    signal = engine.generate_signal(df)

    print("\n" + "="*60)
    print("📊 交易信号分析")
    print("="*60)
    print(f"市场状态: {signal['market_regime']}")
    print(f"策略类型: {signal['type']}")
    print(f"操作建议: {signal['action']}")
    print(f"信号强度: {signal['strength']}/100")
    print(f"\n理由:")
    for reason in signal['reasons']:
        print(f"  • {reason}")

    print(f"\n市场数据:")
    for key, value in signal['market_data'].items():
        print(f"  {key}: {value:.2f}")
