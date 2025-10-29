"""
交易信号历史记录模块
用于记录和查询可交易信号，便于复盘分析
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SignalHistoryRecorder:
    """信号历史记录器"""

    def __init__(self, db_path: str = "data/signal_history.db"):
        """
        初始化记录器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path

        # 确保数据目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        logger.info(f"✅ 信号历史记录器初始化完成: {db_path}")

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建信号记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence TEXT,
                    strength REAL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    risk_reward_ratio REAL,
                    sentiment_score INTEGER,
                    funding_rate REAL,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    outcome TEXT,
                    profit_loss REAL,
                    closed_at DATETIME
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp
                ON signals(symbol, timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON signals(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_type
                ON signals(signal_type)
            """)

            conn.commit()

    def record_signal(self, signal_data: Dict) -> int:
        """
        记录交易信号

        Args:
            signal_data: 信号数据字典

        Returns:
            记录的ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO signals (
                        symbol, signal_type, action, confidence, strength,
                        entry_price, stop_loss, take_profit, risk_reward_ratio,
                        sentiment_score, funding_rate, reason, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data.get('symbol'),
                    signal_data.get('type'),
                    signal_data.get('action'),
                    signal_data.get('confidence'),
                    signal_data.get('strength'),
                    signal_data.get('entry_price'),
                    signal_data.get('stop_loss'),
                    signal_data.get('take_profit'),
                    signal_data.get('risk_reward_ratio'),
                    signal_data.get('sentiment'),
                    signal_data.get('funding_rate'),
                    signal_data.get('reason'),
                    signal_data.get('timestamp', datetime.now().isoformat()),
                ))

                conn.commit()
                signal_id = cursor.lastrowid

                logger.debug(f"📝 记录信号 #{signal_id}: {signal_data.get('symbol')} {signal_data.get('action')}")
                return signal_id

        except Exception as e:
            logger.error(f"❌ 记录信号失败: {e}")
            return -1

    def get_recent_signals(self, hours: int = 24, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取最近的信号记录

        Args:
            hours: 时间范围（小时）
            symbol: 交易对过滤（可选）

        Returns:
            信号列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                since_time = (datetime.now() - timedelta(hours=hours)).isoformat()

                if symbol:
                    cursor.execute("""
                        SELECT * FROM signals
                        WHERE timestamp >= ? AND symbol = ?
                        ORDER BY timestamp DESC
                    """, (since_time, symbol))
                else:
                    cursor.execute("""
                        SELECT * FROM signals
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (since_time,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ 查询信号历史失败: {e}")
            return []

    def get_signal_stats(self, days: int = 7) -> Dict:
        """
        获取信号统计数据

        Args:
            days: 统计天数

        Returns:
            统计数据字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                since_time = (datetime.now() - timedelta(days=days)).isoformat()

                # 总信号数
                cursor.execute("""
                    SELECT COUNT(*) FROM signals WHERE timestamp >= ?
                """, (since_time,))
                total_signals = cursor.fetchone()[0]

                # 按动作分类
                cursor.execute("""
                    SELECT action, COUNT(*) as count
                    FROM signals
                    WHERE timestamp >= ?
                    GROUP BY action
                """, (since_time,))
                action_counts = dict(cursor.fetchall())

                # 按币种分类
                cursor.execute("""
                    SELECT symbol, COUNT(*) as count
                    FROM signals
                    WHERE timestamp >= ?
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 10
                """, (since_time,))
                symbol_counts = dict(cursor.fetchall())

                # 平均信号强度
                cursor.execute("""
                    SELECT AVG(strength) FROM signals WHERE timestamp >= ?
                """, (since_time,))
                avg_strength = cursor.fetchone()[0] or 0

                return {
                    'total_signals': total_signals,
                    'action_counts': action_counts,
                    'symbol_counts': symbol_counts,
                    'avg_strength': round(avg_strength, 2),
                    'period_days': days,
                }

        except Exception as e:
            logger.error(f"❌ 获取信号统计失败: {e}")
            return {}

    def update_signal_outcome(self, signal_id: int, outcome: str, profit_loss: float):
        """
        更新信号结果（用于复盘）

        Args:
            signal_id: 信号ID
            outcome: 结果 (win/loss/breakeven)
            profit_loss: 盈亏百分比
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE signals
                    SET outcome = ?, profit_loss = ?, closed_at = ?
                    WHERE id = ?
                """, (outcome, profit_loss, datetime.now().isoformat(), signal_id))

                conn.commit()
                logger.debug(f"📝 更新信号 #{signal_id} 结果: {outcome} {profit_loss:+.2f}%")

        except Exception as e:
            logger.error(f"❌ 更新信号结果失败: {e}")

    def clear_old_signals(self, days: int = 30):
        """
        清理旧信号记录

        Args:
            days: 保留天数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

                cursor.execute("""
                    DELETE FROM signals WHERE timestamp < ?
                """, (cutoff_time,))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"🗑️  清理 {deleted_count} 条旧信号记录（>{days}天）")

        except Exception as e:
            logger.error(f"❌ 清理旧信号失败: {e}")


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建记录器
    recorder = SignalHistoryRecorder()

    # 测试记录信号
    test_signal = {
        'symbol': 'BTC/USDT',
        'type': 'LONG',
        'action': '做多',
        'confidence': 'high',
        'strength': 85.5,
        'entry_price': 112000.0,
        'stop_loss': 110000.0,
        'take_profit': 116000.0,
        'risk_reward_ratio': 2.0,
        'sentiment': 15,
        'funding_rate': 0.0001,
        'reason': '多头信号强烈，情绪积极',
    }

    signal_id = recorder.record_signal(test_signal)
    print(f"\n✅ 记录信号 ID: {signal_id}")

    # 获取最近信号
    recent = recorder.get_recent_signals(hours=24)
    print(f"\n📊 最近24小时信号数: {len(recent)}")
    if recent:
        print(f"最新信号: {recent[0]['symbol']} - {recent[0]['action']}")

    # 获取统计
    stats = recorder.get_signal_stats(days=7)
    print(f"\n📈 7天统计:")
    print(f"  总信号数: {stats.get('total_signals', 0)}")
    print(f"  平均强度: {stats.get('avg_strength', 0)}")
    print(f"  动作分布: {stats.get('action_counts', {})}")
