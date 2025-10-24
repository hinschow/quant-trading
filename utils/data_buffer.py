"""
数据缓冲区管理
维护实时K线数据的滚动窗口
"""

import pandas as pd
from collections import deque
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class KlineBuffer:
    """K线数据缓冲区"""

    def __init__(self, symbol: str, timeframe: str, max_size: int = 500):
        """
        初始化K线缓冲区

        Args:
            symbol: 交易对
            timeframe: 时间周期
            max_size: 最大缓冲数量
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.max_size = max_size

        # 使用 deque 实现高效的滚动窗口
        self.buffer = deque(maxlen=max_size)

        # 当前正在形成的K线
        self.current_kline: Optional[Dict] = None

        logger.info(f"📊 初始化缓冲区: {symbol} {timeframe}, 容量: {max_size}")

    def initialize(self, historical_data: pd.DataFrame):
        """
        使用历史数据初始化缓冲区

        Args:
            historical_data: 历史K线数据
        """
        self.buffer.clear()

        for _, row in historical_data.iterrows():
            kline = {
                'timestamp': int(row['timestamp']),
                'datetime': row.name if isinstance(row.name, pd.Timestamp) else pd.to_datetime(row['timestamp'], unit='ms'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            }
            self.buffer.append(kline)

        logger.info(f"✅ 缓冲区初始化完成: {len(self.buffer)} 条K线")

    def update_tick(self, price: float, volume: float, timestamp: int):
        """
        更新实时tick数据

        Args:
            price: 当前价格
            volume: 成交量
            timestamp: 时间戳（毫秒）
        """
        dt = pd.to_datetime(timestamp, unit='ms')

        # 判断是否需要创建新K线
        if self.current_kline is None:
            # 第一个tick，创建新K线
            self.current_kline = {
                'timestamp': timestamp,
                'datetime': dt,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        else:
            # 检查是否需要封闭当前K线
            if self._should_close_kline(timestamp):
                # 封闭当前K线，加入缓冲区
                self.buffer.append(self.current_kline.copy())

                # 创建新K线
                self.current_kline = {
                    'timestamp': timestamp,
                    'datetime': dt,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume
                }

                logger.debug(f"🕐 新K线: {dt}, 开: {price}")
                return True  # 返回True表示新K线
            else:
                # 更新当前K线
                self.current_kline['high'] = max(self.current_kline['high'], price)
                self.current_kline['low'] = min(self.current_kline['low'], price)
                self.current_kline['close'] = price
                self.current_kline['volume'] += volume
                self.current_kline['datetime'] = dt

        return False  # 返回False表示K线更新

    def update_kline(self, kline: Dict):
        """
        直接更新K线数据（来自WebSocket K线流）

        Args:
            kline: K线数据字典
        """
        timestamp = kline['timestamp']

        # 检查是否是新K线
        if self.current_kline is None or timestamp > self.current_kline['timestamp']:
            # 封闭旧K线
            if self.current_kline is not None:
                self.buffer.append(self.current_kline.copy())

            # 设置新K线
            self.current_kline = kline.copy()
            logger.debug(f"🕐 新K线: {kline['datetime']}")
            return True
        else:
            # 更新当前K线
            self.current_kline = kline.copy()
            return False

    def _should_close_kline(self, timestamp: int) -> bool:
        """
        判断是否应该封闭当前K线

        Args:
            timestamp: 当前时间戳

        Returns:
            是否应该封闭
        """
        if self.current_kline is None:
            return False

        # 根据时间周期判断
        timeframe_seconds = self._get_timeframe_seconds()
        current_period = timestamp // (timeframe_seconds * 1000)
        kline_period = self.current_kline['timestamp'] // (timeframe_seconds * 1000)

        return current_period > kline_period

    def _get_timeframe_seconds(self) -> int:
        """获取时间周期的秒数"""
        timeframe_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return timeframe_map.get(self.timeframe, 3600)

    def to_dataframe(self, include_current: bool = True) -> pd.DataFrame:
        """
        转换为DataFrame

        Args:
            include_current: 是否包含当前正在形成的K线

        Returns:
            DataFrame
        """
        data = list(self.buffer)

        if include_current and self.current_kline is not None:
            data.append(self.current_kline)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)

        return df

    def get_latest_price(self) -> Optional[float]:
        """获取最新价格"""
        if self.current_kline:
            return self.current_kline['close']
        elif self.buffer:
            return self.buffer[-1]['close']
        return None

    def is_ready(self, min_periods: int = 200) -> bool:
        """
        检查缓冲区是否准备好（有足够的数据）

        Args:
            min_periods: 最小周期数

        Returns:
            是否准备好
        """
        return len(self.buffer) >= min_periods

    def __len__(self):
        """缓冲区大小"""
        return len(self.buffer)

    def __repr__(self):
        return f"KlineBuffer({self.symbol}, {self.timeframe}, {len(self.buffer)} klines)"
