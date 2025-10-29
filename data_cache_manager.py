#!/usr/bin/env python3
"""
本地数据缓存管理器
持久化保存历史K线数据，支持快速回测

功能：
1. 自动保存拉取的历史数据到本地
2. 优先从本地读取，缺失时才从API拉取
3. 支持数据更新（追加最新数据）
4. 支持数据管理（查看、清理、导出）

数据结构：
data/cache/
  ├── BTC_USDT_1h.csv
  ├── BTC_USDT_30m.csv
  ├── ETH_USDT_1h.csv
  └── ...

每个文件包含：timestamp, open, high, low, close, volume
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataCacheManager:
    """本地数据缓存管理器"""

    def __init__(self, cache_dir: str = 'data/cache'):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 数据缓存目录: {self.cache_dir.absolute()}")

    def _get_cache_path(self, symbol: str, timeframe: str) -> Path:
        """
        获取缓存文件路径

        Args:
            symbol: 交易对，如 'BTC/USDT'
            timeframe: 时间周期，如 '1h'

        Returns:
            缓存文件路径
        """
        # 将 BTC/USDT 转换为 BTC_USDT
        safe_symbol = symbol.replace('/', '_')
        filename = f"{safe_symbol}_{timeframe}.csv"
        return self.cache_dir / filename

    def load_from_cache(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        从缓存加载数据

        Args:
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            DataFrame或None
        """
        cache_path = self._get_cache_path(symbol, timeframe)

        if not cache_path.exists():
            logger.info(f"⚠️  缓存不存在: {cache_path.name}")
            return None

        try:
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            logger.info(f"✅ 从缓存加载: {cache_path.name}")
            logger.info(f"   数据范围: {df.index[0]} 至 {df.index[-1]}")
            logger.info(f"   数据条数: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"❌ 加载缓存失败: {e}")
            return None

    def save_to_cache(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        保存数据到缓存

        Args:
            df: 数据DataFrame
            symbol: 交易对
            timeframe: 时间周期
        """
        cache_path = self._get_cache_path(symbol, timeframe)

        try:
            df.to_csv(cache_path)
            logger.info(f"💾 保存到缓存: {cache_path.name}")
            logger.info(f"   数据范围: {df.index[0]} 至 {df.index[-1]}")
            logger.info(f"   数据条数: {len(df)}")
        except Exception as e:
            logger.error(f"❌ 保存缓存失败: {e}")

    def merge_and_save(self, new_df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        合并新旧数据并保存

        Args:
            new_df: 新拉取的数据
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            合并后的完整数据
        """
        # 加载现有缓存
        cached_df = self.load_from_cache(symbol, timeframe)

        if cached_df is None:
            # 没有缓存，直接保存
            self.save_to_cache(new_df, symbol, timeframe)
            return new_df

        # 合并数据
        merged_df = pd.concat([cached_df, new_df])

        # 去重（按时间戳）
        merged_df = merged_df[~merged_df.index.duplicated(keep='last')]

        # 排序
        merged_df = merged_df.sort_index()

        # 保存
        self.save_to_cache(merged_df, symbol, timeframe)

        logger.info(f"🔄 数据合并完成:")
        logger.info(f"   原有: {len(cached_df)} 条")
        logger.info(f"   新增: {len(new_df)} 条")
        logger.info(f"   总计: {len(merged_df)} 条")

        return merged_df

    def update_latest(self, symbol: str, timeframe: str, data_collector) -> pd.DataFrame:
        """
        更新最新数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            data_collector: DataCollector实例

        Returns:
            更新后的完整数据
        """
        cached_df = self.load_from_cache(symbol, timeframe)

        if cached_df is None:
            # 没有缓存，拉取完整数据
            logger.info("📥 首次拉取，获取完整历史数据...")
            new_df = data_collector.fetch_ohlcv(symbol, timeframe, limit=1000)
            self.save_to_cache(new_df, symbol, timeframe)
            return new_df

        # 计算需要更新的数据量
        last_time = cached_df.index[-1]
        now = pd.Timestamp.now(tz='UTC')
        time_diff = now - last_time

        # 根据时间周期计算需要拉取的K线数量
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes = timeframe_minutes.get(timeframe, 60)
        bars_needed = int(time_diff.total_seconds() / 60 / minutes) + 10  # +10确保覆盖

        if bars_needed <= 0:
            logger.info("✅ 数据已是最新，无需更新")
            return cached_df

        logger.info(f"📥 更新最新数据，预计需要 {bars_needed} 根K线...")
        new_df = data_collector.fetch_ohlcv(symbol, timeframe, limit=min(bars_needed, 1000))

        # 合并并保存
        merged_df = self.merge_and_save(new_df, symbol, timeframe)
        return merged_df

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'files': []
        }

        for cache_file in self.cache_dir.glob('*.csv'):
            try:
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                size_mb = cache_file.stat().st_size / (1024 * 1024)

                stats['files'].append({
                    'name': cache_file.name,
                    'rows': len(df),
                    'size_mb': size_mb,
                    'start': df.index[0],
                    'end': df.index[-1],
                    'days': (df.index[-1] - df.index[0]).days
                })

                stats['total_files'] += 1
                stats['total_size_mb'] += size_mb
            except Exception as e:
                logger.warning(f"⚠️  无法读取 {cache_file.name}: {e}")

        return stats

    def print_stats(self):
        """打印缓存统计"""
        stats = self.get_stats()

        print(f"\n{'='*80}")
        print(f"📊 本地数据缓存统计")
        print(f"{'='*80}")
        print(f"缓存目录: {self.cache_dir.absolute()}")
        print(f"文件总数: {stats['total_files']}")
        print(f"总大小:   {stats['total_size_mb']:.2f} MB")
        print()

        if stats['files']:
            print(f"{'文件名':<25} {'数据条数':<10} {'天数':<8} {'大小':<10} {'时间范围'}")
            print(f"{'-'*80}")
            for file_info in sorted(stats['files'], key=lambda x: x['name']):
                print(f"{file_info['name']:<25} "
                      f"{file_info['rows']:<10} "
                      f"{file_info['days']:<8} "
                      f"{file_info['size_mb']:.2f} MB   "
                      f"{file_info['start']} ~ {file_info['end']}")
        else:
            print("⚠️  缓存为空")

        print(f"{'='*80}\n")

    def clear_cache(self, symbol: Optional[str] = None, timeframe: Optional[str] = None):
        """
        清理缓存

        Args:
            symbol: 交易对（None表示全部）
            timeframe: 时间周期（None表示全部）
        """
        if symbol and timeframe:
            # 清理特定文件
            cache_path = self._get_cache_path(symbol, timeframe)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"🗑️  已删除: {cache_path.name}")
            else:
                logger.warning(f"⚠️  文件不存在: {cache_path.name}")
        else:
            # 清理所有文件
            count = 0
            for cache_file in self.cache_dir.glob('*.csv'):
                cache_file.unlink()
                count += 1
            logger.info(f"🗑️  已清理 {count} 个缓存文件")


# ==================== 命令行工具 ====================
def main():
    """主函数：缓存管理工具"""
    import argparse

    parser = argparse.ArgumentParser(description='数据缓存管理工具')
    parser.add_argument('action', choices=['stats', 'update', 'clear'],
                        help='操作：stats(统计), update(更新), clear(清理)')
    parser.add_argument('--symbol', help='交易对，如 BTC/USDT')
    parser.add_argument('--timeframe', '-t', help='时间周期，如 1h')
    parser.add_argument('--all', action='store_true', help='更新所有交易对')

    args = parser.parse_args()

    manager = DataCacheManager()

    if args.action == 'stats':
        # 显示统计
        manager.print_stats()

    elif args.action == 'update':
        # 更新数据
        from data_collector import DataCollector
        from config.strategy_params import TRADING_SYMBOLS

        collector = DataCollector('binance')

        if args.all:
            # 更新所有交易对
            timeframes = ['1h', '30m', '15m']
            for symbol in TRADING_SYMBOLS:
                for tf in timeframes:
                    print(f"\n更新 {symbol} @ {tf}...")
                    manager.update_latest(symbol, tf, collector)
        elif args.symbol and args.timeframe:
            # 更新指定交易对
            manager.update_latest(args.symbol, args.timeframe, collector)
        else:
            print("❌ 请指定 --symbol 和 --timeframe，或使用 --all")

    elif args.action == 'clear':
        # 清理缓存
        if args.symbol and args.timeframe:
            manager.clear_cache(args.symbol, args.timeframe)
        else:
            confirm = input("⚠️  确认清理所有缓存？(y/n): ")
            if confirm.lower() == 'y':
                manager.clear_cache()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
