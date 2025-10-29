#!/usr/bin/env python3
"""
快速回测引擎 - 使用本地缓存数据
无需每次从API拉取，快速验证策略参数

使用方法：
  python3 fast_backtest.py BTC/USDT -t 1h
  python3 fast_backtest.py --all  # 回测所有交易对
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import logging
from pathlib import Path

from data_cache_manager import DataCacheManager
from strategy_engine_v73 import StrategyEngineV73
from config.strategy_params import TRADING_SYMBOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastBacktest:
    """快速回测引擎（使用本地缓存）"""

    def __init__(
        self,
        initial_capital: float = 10000,
        position_size_pct: float = 1.0,
        commission: float = 0.001
    ):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            position_size_pct: 仓位比例
            commission: 手续费率
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.commission = commission

        # 缓存管理器
        self.cache_manager = DataCacheManager()

        # 策略引擎
        self.strategy_engine = StrategyEngineV73(
            use_hyperliquid=False,
            use_smart_money=False
        )

        # 回测状态
        self.reset()

    def reset(self):
        """重置回测状态"""
        self.capital = self.initial_capital
        self.position = 0
        self.position_price = 0
        self.trades = []
        self.equity_curve = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def run(
        self,
        symbol: str,
        timeframe: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        运行快速回测

        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            回测结果
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 快速回测: {symbol} {timeframe}")
        logger.info(f"{'='*80}")

        # 1. 从缓存加载数据
        df = self.cache_manager.load_from_cache(symbol, timeframe)

        if df is None:
            logger.error(f"❌ 缓存不存在，请先运行数据更新:")
            logger.error(f"   python3 data_cache_manager.py update --symbol {symbol} --timeframe {timeframe}")
            return None

        # 2. 过滤日期范围
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        logger.info(f"数据范围: {df.index[0]} ~ {df.index[-1]}")
        logger.info(f"数据条数: {len(df)}")

        # 3. 重置状态
        self.reset()

        # 4. 逐根K线回测
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 开始快速回测...")
        logger.info(f"{'='*80}\n")

        for i in range(200, len(df)):  # 从第200根开始
            current_df = df.iloc[:i+1].copy()
            current_time = current_df.index[-1]
            current_price = float(current_df['close'].iloc[-1])

            # 生成信号
            signal = self.strategy_engine.generate_signal(current_df, symbol)

            # 检查止损止盈
            self._check_exit_conditions(current_time, current_price, signal)

            # 处理信号
            if signal['action'] == 'BUY' and self.position == 0:
                self._execute_buy(current_time, current_price, signal)
            elif signal['action'] == 'SELL' and self.position > 0:
                self._execute_sell(current_time, current_price, signal)

            # 记录权益
            equity = self._calculate_equity(current_price)
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': equity,
                'price': current_price
            })

        # 5. 强制平仓
        if self.position > 0:
            final_price = float(df['close'].iloc[-1])
            final_time = df.index[-1]
            self._execute_sell(final_time, final_price, {'reasons': ['回测结束']})

        # 6. 计算结果
        results = self._calculate_results(df)

        # 7. 打印结果
        self._print_results(results)

        return results

    def _execute_buy(self, timestamp, price: float, signal: Dict):
        """执行买入"""
        capital_to_use = self.capital * self.position_size_pct
        commission_cost = capital_to_use * self.commission
        position_size = (capital_to_use - commission_cost) / price

        self.position = position_size
        self.position_price = price
        self.capital -= capital_to_use

        trade = {
            'type': 'BUY',
            'timestamp': timestamp,
            'price': price,
            'size': position_size,
            'cost': capital_to_use,
            'commission': commission_cost,
            'signal_strength': signal['strength'],
            'reasons': signal.get('reasons', [])
        }
        self.trades.append(trade)

        logger.info(f"🟢 买入 | {timestamp} | ${price:,.2f} | 强度: {signal['strength']}")

    def _execute_sell(self, timestamp, price: float, signal: Dict):
        """执行卖出"""
        if self.position == 0:
            return

        sell_value = self.position * price
        commission_cost = sell_value * self.commission
        net_value = sell_value - commission_cost

        profit = net_value - (self.position * self.position_price)
        profit_pct = (price - self.position_price) / self.position_price * 100

        self.capital += net_value
        self.position = 0

        self.total_trades += 1
        if profit > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        trade = {
            'type': 'SELL',
            'timestamp': timestamp,
            'price': price,
            'size': self.position,
            'value': net_value,
            'commission': commission_cost,
            'profit': profit,
            'profit_pct': profit_pct,
            'signal_strength': signal.get('strength', 0),
            'reasons': signal.get('reasons', [])
        }
        self.trades.append(trade)

        result_icon = "✅" if profit > 0 else "❌"
        logger.info(f"{result_icon} 卖出 | {timestamp} | ${price:,.2f} | 收益: ${profit:,.2f} ({profit_pct:+.2f}%)")

    def _check_exit_conditions(self, timestamp, current_price: float, signal: Dict):
        """检查止损止盈"""
        if self.position == 0:
            return

        trading_plan = signal.get('trading_plan', {})
        if not trading_plan.get('stop_loss_price'):
            return

        stop_loss = trading_plan['stop_loss_price']
        take_profit = trading_plan['take_profit_price']

        if current_price <= stop_loss:
            logger.info(f"🛑 触发止损 | {timestamp} | ${current_price:,.2f}")
            self._execute_sell(timestamp, current_price, {'reasons': ['止损']})
        elif current_price >= take_profit:
            logger.info(f"🎯 触发止盈 | {timestamp} | ${current_price:,.2f}")
            self._execute_sell(timestamp, current_price, {'reasons': ['止盈']})

    def _calculate_equity(self, current_price: float) -> float:
        """计算当前权益"""
        position_value = self.position * current_price if self.position > 0 else 0
        return self.capital + position_value

    def _calculate_results(self, df: pd.DataFrame) -> Dict:
        """计算回测结果"""
        equity_df = pd.DataFrame(self.equity_curve)

        final_equity = equity_df['equity'].iloc[-1] if len(equity_df) > 0 else self.initial_capital
        total_return = final_equity - self.initial_capital
        total_return_pct = (final_equity / self.initial_capital - 1) * 100

        if len(equity_df) > 0:
            equity_df['max_equity'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['max_equity']) / equity_df['max_equity'] * 100
            max_drawdown = equity_df['drawdown'].min()
        else:
            max_drawdown = 0

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        winning_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('profit', 0) < 0]

        avg_win = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t['profit'] for t in losing_trades])) if losing_trades else 1
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        days = (df.index[-1] - df.index[0]).days
        years = days / 365 if days > 0 else 1
        annual_return = (total_return_pct / years) if years > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'days': days
        }

    def _print_results(self, results: Dict):
        """打印回测结果"""
        print(f"\n{'='*80}")
        print(f"📊 回测结果")
        print(f"{'='*80}")

        print(f"\n【基本信息】")
        print(f"  初始资金:      ${results['initial_capital']:>12,.2f}")
        print(f"  最终权益:      ${results['final_equity']:>12,.2f}")
        print(f"  总收益:        ${results['total_return']:>12,.2f} ({results['total_return_pct']:+.2f}%)")
        print(f"  年化收益率:    {results['annual_return']:>15.2f}%")
        print(f"  最大回撤:      {results['max_drawdown']:>15.2f}%")

        print(f"\n【交易统计】")
        print(f"  总交易次数:    {results['total_trades']:>15}")
        print(f"  盈利次数:      {results['winning_trades']:>15}")
        print(f"  亏损次数:      {results['losing_trades']:>15}")
        print(f"  胜率:          {results['win_rate']:>15.2f}%")

        print(f"\n【盈亏分析】")
        print(f"  平均盈利:      ${results['avg_win']:>12,.2f}")
        print(f"  平均亏损:      ${results['avg_loss']:>12,.2f}")
        print(f"  盈亏比:        {results['profit_factor']:>15.2f}:1")

        print(f"\n{'='*80}\n")


def batch_backtest(timeframes: List[str] = ['1h', '30m', '15m']):
    """批量回测所有交易对"""
    print(f"\n{'='*80}")
    print(f"🔄 批量快速回测")
    print(f"{'='*80}\n")

    backtest = FastBacktest()
    all_results = {}

    for symbol in TRADING_SYMBOLS:
        for timeframe in timeframes:
            print(f"\n{'='*80}")
            print(f"回测: {symbol} @ {timeframe}")
            print(f"{'='*80}")

            try:
                results = backtest.run(symbol, timeframe)
                if results:
                    key = f"{symbol}_{timeframe}"
                    all_results[key] = results
            except Exception as e:
                logger.error(f"❌ 回测失败: {e}")

    # 汇总结果
    print(f"\n{'='*80}")
    print(f"📊 批量回测汇总")
    print(f"{'='*80}\n")

    for key, results in all_results.items():
        print(f"{key:<20} "
              f"收益: {results['total_return_pct']:>7.2f}% | "
              f"胜率: {results['win_rate']:>5.1f}% | "
              f"交易: {results['total_trades']:>3}笔")

    print(f"\n{'='*80}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='快速回测引擎（使用本地缓存）')
    parser.add_argument('symbol', nargs='?', help='交易对，如 BTC/USDT')
    parser.add_argument('-t', '--timeframe', default='1h', help='时间周期，默认: 1h')
    parser.add_argument('--all', action='store_true', help='回测所有交易对')
    parser.add_argument('--start', help='开始日期，如 2025-09-01')
    parser.add_argument('--end', help='结束日期，如 2025-10-27')

    args = parser.parse_args()

    if args.all:
        # 批量回测
        batch_backtest()
    elif args.symbol:
        # 单个回测
        backtest = FastBacktest()
        backtest.run(args.symbol, args.timeframe, args.start, args.end)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
