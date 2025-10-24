"""
实时信号引擎
基于实时数据生成交易信号
"""

import pandas as pd
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

from utils.data_buffer import KlineBuffer
from strategy_engine import StrategyEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeSignalEngine:
    """实时信号引擎"""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        buffer_size: int = 500,
        min_periods: int = 200
    ):
        """
        初始化实时信号引擎

        Args:
            symbol: 交易对
            timeframe: 时间周期
            buffer_size: 缓冲区大小
            min_periods: 最小周期数（指标计算需要）
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.min_periods = min_periods

        # 数据缓冲区
        self.buffer = KlineBuffer(symbol, timeframe, buffer_size)

        # 策略引擎
        self.strategy = StrategyEngine()

        # 最新信号
        self.latest_signal: Optional[Dict] = None
        self.last_action = 'HOLD'  # 上次动作

        # 回调函数
        self.on_signal_change: Optional[Callable] = None

        logger.info(f"🎯 实时信号引擎初始化: {symbol} {timeframe}")

    def initialize(self, historical_data: pd.DataFrame):
        """
        使用历史数据初始化

        Args:
            historical_data: 历史K线数据
        """
        self.buffer.initialize(historical_data)
        logger.info(f"✅ 引擎初始化完成: {len(self.buffer)} 条K线")

        # 立即生成初始信号
        if self.buffer.is_ready(self.min_periods):
            self._generate_signal()

    async def on_kline(self, kline: Dict):
        """
        处理新K线数据

        Args:
            kline: K线数据
        """
        # 更新缓冲区
        is_new_kline = self.buffer.update_kline(kline)

        # 如果数据足够，生成信号
        if self.buffer.is_ready(self.min_periods):
            # 只在新K线封闭时重新计算
            if is_new_kline:
                self._generate_signal()
                logger.info(f"🕐 新K线封闭: {kline['datetime']}, 重新计算信号")
            else:
                # K线更新中，只更新价格显示（不重新计算指标）
                self._update_current_price(kline['close'])
        else:
            logger.info(f"⏳ 数据不足: {len(self.buffer)}/{self.min_periods}")

    def _generate_signal(self):
        """生成交易信号"""
        try:
            # 获取数据框（不包含当前正在形成的K线）
            df = self.buffer.to_dataframe(include_current=False)

            if len(df) < self.min_periods:
                logger.warning(f"⚠️  数据不足，无法计算指标")
                return

            # 生成信号
            signal = self.strategy.generate_signal(df)

            # 检查信号是否变化
            action_changed = (signal['action'] != self.last_action)

            # 更新状态
            self.latest_signal = signal
            self.last_action = signal['action']

            # 如果信号改变且有回调，触发回调
            if action_changed and self.on_signal_change:
                self.on_signal_change(signal)

        except Exception as e:
            logger.error(f"❌ 生成信号失败: {e}")
            import traceback
            traceback.print_exc()

    def _update_current_price(self, price: float):
        """
        更新当前价格（不重新计算指标）

        Args:
            price: 当前价格
        """
        if self.latest_signal:
            # 更新信号中的当前价格
            self.latest_signal['current_price'] = price

    def get_signal(self) -> Optional[Dict]:
        """
        获取最新信号

        Returns:
            信号字典
        """
        return self.latest_signal

    def get_current_price(self) -> Optional[float]:
        """获取当前价格"""
        return self.buffer.get_latest_price()

    def is_ready(self) -> bool:
        """引擎是否准备好"""
        return self.buffer.is_ready(self.min_periods)

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计字典
        """
        if not self.latest_signal:
            return {}

        signal = self.latest_signal
        current_price = self.get_current_price()

        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'current_price': current_price,
            'action': signal['action'],
            'strength': signal['strength'],
            'market_regime': signal['market_regime'],
            'buffer_size': len(self.buffer),
            'last_update': datetime.now()
        }
