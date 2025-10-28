"""
交易信号持久化存储模块
支持SQLite数据库存储、查询、导出
"""

import os
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from config.storage_params import (
    STORAGE_PARAMS,
    SIGNAL_TABLE_SCHEMA,
    KLINE_TABLE_SCHEMA,
    STATS_QUERY,
    SYMBOL_STATS_QUERY,
)

logger = logging.getLogger(__name__)


class SignalStorage:
    """交易信号存储管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化信号存储

        Args:
            db_path: 数据库文件路径（默认使用配置文件中的路径）
        """
        self.db_path = db_path or STORAGE_PARAMS['db_path']
        self.storage_mode = STORAGE_PARAMS['storage_mode']
        self.enabled = STORAGE_PARAMS['enable_storage']

        if not self.enabled:
            logger.info("📦 信号存储已禁用")
            return

        # 确保data目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 初始化数据库
        self._init_database()

        # 启动时清理过期数据
        if STORAGE_PARAMS['cleanup_on_startup']:
            self.cleanup_old_data()

        logger.info(f"✅ 信号存储初始化完成: {self.db_path} (模式: {self.storage_mode})")

    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建信号表
            cursor.executescript(SIGNAL_TABLE_SCHEMA)

            # 创建K线快照表（standard/full模式）
            if STORAGE_PARAMS['save_kline_snapshot']:
                cursor.executescript(KLINE_TABLE_SCHEMA)

            # 启用性能优化
            if STORAGE_PARAMS['enable_compression']:
                cursor.execute("PRAGMA auto_vacuum = FULL;")
                cursor.execute("PRAGMA journal_mode = WAL;")

            conn.commit()
            conn.close()

            logger.debug("📊 数据库表结构初始化完成")

        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise

    def save_signal(self, signal: Dict, symbol: str, timeframe: str = '15m') -> bool:
        """
        保存交易信号到数据库

        Args:
            signal: 信号字典（来自StrategyEngine.generate_signal）
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            是否保存成功
        """
        if not self.enabled:
            return False

        try:
            # 检查信号强度过滤
            if signal.get('strength', 0) < STORAGE_PARAMS['min_signal_strength']:
                logger.debug(f"⏭️  跳过弱信号: {symbol} 强度{signal.get('strength')}")
                return False

            # 检查中性信号过滤
            if signal.get('action') == 'HOLD' and not STORAGE_PARAMS['save_neutral_signals']:
                logger.debug(f"⏭️  跳过中性信号: {symbol}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 准备信号数据
            timestamp = datetime.now()
            action = signal.get('action', 'HOLD')
            strength = signal.get('strength', 0)
            market_regime = signal.get('market_regime', 'UNKNOWN')

            # 价格数据
            price = signal.get('price', 0.0)
            price_change_pct = signal.get('price_change_pct', 0.0)

            # 情绪数据
            funding_rate = signal.get('funding_rate', None)
            open_interest = signal.get('open_interest', None)
            oi_change_24h = signal.get('oi_change_24h', None)

            # 信号详情（序列化为JSON）
            reasons = json.dumps(signal.get('reasons', []), ensure_ascii=False)
            sentiment_reasons = json.dumps(signal.get('sentiment_reasons', []), ensure_ascii=False)

            # 指标快照（可选）
            indicators = None
            if STORAGE_PARAMS['save_signal_details']:
                indicators = json.dumps({
                    'ema_fast': signal.get('ema_fast'),
                    'ema_slow': signal.get('ema_slow'),
                    'rsi': signal.get('rsi'),
                    'macd': signal.get('macd'),
                    'adx': signal.get('adx'),
                }, ensure_ascii=False)

            # 插入数据（使用REPLACE处理重复）
            cursor.execute("""
                INSERT OR REPLACE INTO signals (
                    timestamp, symbol, timeframe,
                    action, strength, market_regime,
                    price, price_change_pct,
                    funding_rate, open_interest, oi_change_24h,
                    reasons, sentiment_reasons, indicators
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, symbol, timeframe,
                action, strength, market_regime,
                price, price_change_pct,
                funding_rate, open_interest, oi_change_24h,
                reasons, sentiment_reasons, indicators
            ))

            conn.commit()
            conn.close()

            logger.debug(f"💾 已保存信号: {symbol} {action} {strength}/100 @ {timestamp.strftime('%H:%M:%S')}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存信号失败 {symbol}: {e}")
            return False

    def query_signals(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_strength: int = 0,
        action: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        查询信号数据

        Args:
            symbol: 交易对（None=所有）
            start_date: 开始日期
            end_date: 结束日期
            min_strength: 最低信号强度
            action: 信号动作（BUY/SELL/HOLD）
            limit: 返回数量限制

        Returns:
            信号列表
        """
        if not self.enabled:
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典格式返回
            cursor = conn.cursor()

            # 构建查询条件
            query = "SELECT * FROM signals WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            if min_strength > 0:
                query += " AND strength >= ?"
                params.append(min_strength)

            if action:
                query += " AND action = ?"
                params.append(action)

            # 排序和限制
            query += " ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # 转换为字典列表
            signals = []
            for row in rows:
                signal = dict(row)
                # 解析JSON字段
                signal['reasons'] = json.loads(signal.get('reasons', '[]'))
                signal['sentiment_reasons'] = json.loads(signal.get('sentiment_reasons', '[]'))
                if signal.get('indicators'):
                    signal['indicators'] = json.loads(signal['indicators'])
                signals.append(signal)

            conn.close()

            logger.debug(f"📊 查询到 {len(signals)} 条信号记录")
            return signals

        except Exception as e:
            logger.error(f"❌ 查询信号失败: {e}")
            return []

    def get_stats(self) -> Dict:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        if not self.enabled:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 总体统计
            cursor.execute(STATS_QUERY)
            stats = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))

            # 数据库文件大小
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            # 按币种统计
            cursor.execute(SYMBOL_STATS_QUERY)
            symbol_stats = []
            for row in cursor.fetchall():
                symbol_stats.append(dict(zip([d[0] for d in cursor.description], row)))

            stats['symbol_stats'] = symbol_stats

            conn.close()

            return stats

        except Exception as e:
            logger.error(f"❌ 获取统计失败: {e}")
            return {}

    def cleanup_old_data(self) -> Tuple[int, int]:
        """
        清理过期数据

        Returns:
            (清理的信号数量, 清理的K线数量)
        """
        if not self.enabled or not STORAGE_PARAMS['auto_cleanup']:
            return 0, 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 计算过期日期
            signal_cutoff = datetime.now() - timedelta(days=STORAGE_PARAMS['signal_retention_days'])
            kline_cutoff = datetime.now() - timedelta(days=STORAGE_PARAMS['kline_retention_days'])

            # 清理过期信号
            cursor.execute("DELETE FROM signals WHERE timestamp < ?", (signal_cutoff,))
            signal_deleted = cursor.rowcount

            # 清理过期K线（如果表存在）
            kline_deleted = 0
            if STORAGE_PARAMS['save_kline_snapshot']:
                cursor.execute("DELETE FROM kline_snapshots WHERE timestamp < ?", (kline_cutoff,))
                kline_deleted = cursor.rowcount

            # 清理并优化数据库
            cursor.execute("VACUUM;")

            conn.commit()
            conn.close()

            if signal_deleted > 0 or kline_deleted > 0:
                logger.info(f"🗑️  清理完成: 信号 {signal_deleted} 条, K线 {kline_deleted} 条")

            return signal_deleted, kline_deleted

        except Exception as e:
            logger.error(f"❌ 清理数据失败: {e}")
            return 0, 0

    def export_to_csv(self, output_path: str, **query_kwargs) -> bool:
        """
        导出信号数据为CSV文件

        Args:
            output_path: 输出文件路径
            **query_kwargs: 查询参数（传递给query_signals）

        Returns:
            是否导出成功
        """
        try:
            signals = self.query_signals(**query_kwargs)

            if not signals:
                logger.warning("⚠️  没有数据可导出")
                return False

            # 转换为DataFrame
            df = pd.DataFrame(signals)

            # 展开JSON列（reasons和sentiment_reasons）
            if 'reasons' in df.columns:
                df['reasons'] = df['reasons'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
            if 'sentiment_reasons' in df.columns:
                df['sentiment_reasons'] = df['sentiment_reasons'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

            # 删除indicators列（太复杂，不适合CSV）
            if 'indicators' in df.columns:
                df = df.drop(columns=['indicators'])

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 导出CSV
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            logger.info(f"✅ 已导出 {len(signals)} 条记录到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 导出CSV失败: {e}")
            return False

    def export_to_json(self, output_path: str, **query_kwargs) -> bool:
        """
        导出信号数据为JSON文件

        Args:
            output_path: 输出文件路径
            **query_kwargs: 查询参数

        Returns:
            是否导出成功
        """
        try:
            signals = self.query_signals(**query_kwargs)

            if not signals:
                logger.warning("⚠️  没有数据可导出")
                return False

            # 转换datetime为字符串
            for signal in signals:
                if 'timestamp' in signal:
                    signal['timestamp'] = str(signal['timestamp'])
                if 'created_at' in signal:
                    signal['created_at'] = str(signal['created_at'])

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 导出JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(signals, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 已导出 {len(signals)} 条记录到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 导出JSON失败: {e}")
            return False


# ==================== 便捷函数 ====================

# 全局存储实例（单例模式）
_storage_instance = None


def get_storage() -> SignalStorage:
    """
    获取全局存储实例（单例）

    Returns:
        SignalStorage实例
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SignalStorage()
    return _storage_instance


def save_signal(signal: Dict, symbol: str, timeframe: str = '15m') -> bool:
    """
    快捷保存信号

    Args:
        signal: 信号字典
        symbol: 交易对
        timeframe: 时间周期

    Returns:
        是否保存成功
    """
    storage = get_storage()
    return storage.save_signal(signal, symbol, timeframe)


def query_signals(**kwargs) -> List[Dict]:
    """
    快捷查询信号

    Args:
        **kwargs: 查询参数

    Returns:
        信号列表
    """
    storage = get_storage()
    return storage.query_signals(**kwargs)


def get_stats() -> Dict:
    """
    快捷获取统计信息

    Returns:
        统计信息字典
    """
    storage = get_storage()
    return storage.get_stats()
