"""
信号记录器
自动保存所有买卖信号到文件，方便后续分析
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class SignalLogger:
    """信号记录器"""

    def __init__(self, log_dir: str = "signal_logs"):
        """
        初始化信号记录器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # CSV文件路径
        today = datetime.now().strftime('%Y%m%d')
        self.csv_file = self.log_dir / f"signals_{today}.csv"
        self.json_file = self.log_dir / f"signals_{today}.json"

        # 初始化CSV文件（如果不存在）
        self._init_csv()

        # 内存中的信号列表
        self.signals = []

    def _init_csv(self):
        """初始化CSV文件（添加表头）"""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间',
                    '交易对',
                    '时间周期',
                    '市场状态',
                    '操作',
                    '信号强度',
                    '当前价格',
                    '买入价',
                    '止盈价',
                    '止损价',
                    '止盈百分比',
                    '止损百分比',
                    '风险回报比',
                    '信号理由',
                    'RSI',
                    'ADX',
                    'MACD'
                ])

    def log_signal(
        self,
        symbol: str,
        timeframe: str,
        signal: Dict,
        exchange: str = 'binance'
    ):
        """
        记录交易信号

        Args:
            symbol: 交易对
            timeframe: 时间周期
            signal: 信号字典
            exchange: 交易所
        """
        # 只记录买卖信号，不记录 HOLD
        if signal['action'] == 'HOLD':
            return

        timestamp = datetime.now()
        trading_plan = signal.get('trading_plan', {})
        market_data = signal.get('market_data', {})

        # 构建信号记录
        signal_record = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'timeframe': timeframe,
            'exchange': exchange,
            'market_regime': signal['market_regime'],
            'action': signal['action'],
            'strength': signal['strength'],
            'current_price': market_data.get('price', 0),
            'entry_price': trading_plan.get('entry_price'),
            'take_profit_price': trading_plan.get('take_profit_price'),
            'stop_loss_price': trading_plan.get('stop_loss_price'),
            'take_profit_pct': trading_plan.get('take_profit_pct'),
            'stop_loss_pct': trading_plan.get('stop_loss_pct'),
            'risk_reward_ratio': trading_plan.get('risk_reward_ratio'),
            'reasons': ' | '.join(signal.get('reasons', [])),
            'rsi': market_data.get('rsi'),
            'adx': market_data.get('adx'),
            'macd': market_data.get('macd'),
        }

        # 保存到内存
        self.signals.append(signal_record)

        # 保存到CSV
        self._save_to_csv(signal_record)

        # 保存到JSON
        self._save_to_json()

    def _save_to_csv(self, signal_record: Dict):
        """保存单条信号到CSV"""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                signal_record['timestamp'],
                signal_record['symbol'],
                signal_record['timeframe'],
                signal_record['market_regime'],
                signal_record['action'],
                signal_record['strength'],
                signal_record['current_price'],
                signal_record['entry_price'],
                signal_record['take_profit_price'],
                signal_record['stop_loss_price'],
                signal_record['take_profit_pct'],
                signal_record['stop_loss_pct'],
                signal_record['risk_reward_ratio'],
                signal_record['reasons'],
                signal_record['rsi'],
                signal_record['adx'],
                signal_record['macd'],
            ])

    def _save_to_json(self):
        """保存所有信号到JSON（完整数据）"""
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.signals, f, ensure_ascii=False, indent=2)

    def get_summary(self) -> str:
        """获取今日信号摘要"""
        if not self.signals:
            return "今日暂无信号记录"

        buy_count = sum(1 for s in self.signals if s['action'] == 'BUY')
        sell_count = sum(1 for s in self.signals if s['action'] == 'SELL')
        avg_strength = sum(s['strength'] for s in self.signals) / len(self.signals)

        summary = f"""
今日信号统计:
  总信号数: {len(self.signals)}
  买入信号: {buy_count}
  卖出信号: {sell_count}
  平均强度: {avg_strength:.1f}/100

日志文件:
  CSV: {self.csv_file}
  JSON: {self.json_file}
"""
        return summary
