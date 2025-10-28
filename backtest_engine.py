#!/usr/bin/env python3
"""
简单回测引擎
用于验证策略信号质量和收益表现
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from data_collector import DataCollector
from strategy_engine import StrategyEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleBacktest:
    """简单回测引擎"""

    def __init__(
        self,
        initial_capital: float = 10000,
        position_size_pct: float = 1.0,
        commission: float = 0.001
    ):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金（USDT）
            position_size_pct: 仓位比例（0.0-1.0）
            commission: 手续费率（0.001 = 0.1%）
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.commission = commission

        # 回测状态
        self.capital = initial_capital
        self.position = 0  # 当前持仓量
        self.position_price = 0  # 持仓成本
        self.trades: List[Dict] = []  # 交易记录
        self.equity_curve: List[Dict] = []  # 权益曲线

        # 统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def run(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> Dict:
        """
        运行回测

        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: K线数量

        Returns:
            回测结果
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 开始回测: {symbol} {timeframe}")
        logger.info(f"{'='*80}")
        logger.info(f"初始资金: ${self.initial_capital:,.2f}")
        logger.info(f"仓位比例: {self.position_size_pct*100:.0f}%")
        logger.info(f"手续费率: {self.commission*100:.2f}%")

        # 1. 获取历史数据
        collector = DataCollector('binance')
        df = collector.fetch_ohlcv(symbol, timeframe, limit)

        logger.info(f"数据范围: {df.index[0]} ~ {df.index[-1]}")
        logger.info(f"数据条数: {len(df)}")

        # 2. 初始化策略引擎（回测模式禁用Hyperliquid，因为无历史资金费率）
        engine = StrategyEngine(use_hyperliquid=False)

        # 3. 逐根K线回测
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 开始模拟交易...")
        logger.info(f"{'='*80}\n")

        for i in range(200, len(df)):  # 从第200根开始（确保指标有效）
            # 获取当前时间点的数据
            current_df = df.iloc[:i+1].copy()
            current_time = current_df.index[-1]
            current_price = float(current_df['close'].iloc[-1])

            # 生成交易信号
            signal = engine.generate_signal(current_df, symbol)

            # 检查是否需要止损/止盈
            self._check_exit_conditions(current_time, current_price, signal)

            # 处理信号
            if signal['action'] == 'BUY' and self.position == 0:
                # 买入
                self._execute_buy(current_time, current_price, signal)

            elif signal['action'] == 'SELL' and self.position > 0:
                # 卖出
                self._execute_sell(current_time, current_price, signal)

            # 记录权益
            equity = self._calculate_equity(current_price)
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': equity,
                'capital': self.capital,
                'position': self.position,
                'price': current_price
            })

        # 4. 如果还有持仓，平仓
        if self.position > 0:
            final_price = float(df['close'].iloc[-1])
            final_time = df.index[-1]
            self._execute_sell(final_time, final_price, {'reasons': ['回测结束，强制平仓']})

        # 5. 检查是否有交易
        if self.total_trades == 0:
            logger.warning("\n⚠️  回测期间没有产生任何交易信号")
            logger.warning("可能原因:")
            logger.warning("  1. 数据量太少（建议至少500根K线）")
            logger.warning("  2. 信号阈值太严格（当前阈值: 30分）")
            logger.warning("  3. 市场状态不符合策略条件")
            logger.warning("\n建议:")
            logger.warning("  - 增加数据量: --limit 500")
            logger.warning("  - 尝试其他时间段")
            logger.warning("  - 查看信号分析: python3 signal_analyzer.py BTC/USDT -t 1h")

        # 6. 计算回测结果
        results = self._calculate_results(df)

        # 7. 显示结果
        self._print_results(results)

        return results

    def _execute_buy(self, timestamp, price: float, signal: Dict):
        """执行买入"""
        # 计算买入数量
        capital_to_use = self.capital * self.position_size_pct
        commission_cost = capital_to_use * self.commission
        position_size = (capital_to_use - commission_cost) / price

        # 更新状态
        self.position = position_size
        self.position_price = price
        self.capital -= capital_to_use

        # 记录交易
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

        logger.info(f"🟢 买入 | {timestamp} | ${price:,.2f} | 数量: {position_size:.4f} | 强度: {signal['strength']}")

    def _execute_sell(self, timestamp, price: float, signal: Dict):
        """执行卖出"""
        if self.position == 0:
            return

        # 计算收益
        sell_value = self.position * price
        commission_cost = sell_value * self.commission
        net_value = sell_value - commission_cost

        profit = net_value - (self.position * self.position_price)
        profit_pct = (price - self.position_price) / self.position_price * 100

        # 更新状态
        self.capital += net_value
        self.position = 0

        # 统计
        self.total_trades += 1
        if profit > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # 记录交易
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
        """检查止损/止盈条件"""
        if self.position == 0:
            return

        trading_plan = signal.get('trading_plan', {})
        if not trading_plan.get('stop_loss_price'):
            return

        stop_loss = trading_plan['stop_loss_price']
        take_profit = trading_plan['take_profit_price']

        # 检查止损
        if current_price <= stop_loss:
            logger.info(f"🛑 触发止损 | {timestamp} | ${current_price:,.2f}")
            self._execute_sell(timestamp, current_price, {'reasons': ['止损']})

        # 检查止盈
        elif current_price >= take_profit:
            logger.info(f"🎯 触发止盈 | {timestamp} | ${current_price:,.2f}")
            self._execute_sell(timestamp, current_price, {'reasons': ['止盈']})

    def _calculate_equity(self, current_price: float) -> float:
        """计算当前权益"""
        position_value = self.position * current_price if self.position > 0 else 0
        return self.capital + position_value

    def _calculate_results(self, df: pd.DataFrame) -> Dict:
        """计算回测结果"""
        # 权益曲线
        equity_df = pd.DataFrame(self.equity_curve)

        # 最终权益
        final_equity = equity_df['equity'].iloc[-1] if len(equity_df) > 0 else self.initial_capital

        # 总收益
        total_return = final_equity - self.initial_capital
        total_return_pct = (final_equity / self.initial_capital - 1) * 100

        # 最大回撤（只有在有数据时计算）
        if len(equity_df) > 0:
            equity_df['max_equity'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['max_equity']) / equity_df['max_equity'] * 100
            max_drawdown = equity_df['drawdown'].min()
        else:
            max_drawdown = 0

        # 胜率
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        # 盈亏比
        winning_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('profit', 0) < 0]

        avg_win = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t['profit'] for t in losing_trades])) if losing_trades else 1
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        # 夏普比率（简化版）
        if len(equity_df) > 1:
            equity_df['returns'] = equity_df['equity'].pct_change()
            sharpe_ratio = equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252) if equity_df['returns'].std() > 0 else 0
        else:
            sharpe_ratio = 0

        # 年化收益率（假设数据时间）
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
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': equity_df,
            'trades': self.trades,
            'days': days
        }

    def _print_results(self, results: Dict):
        """打印回测结果"""
        print("\n" + "="*80)
        print("📊 回测结果")
        print("="*80)

        # 基本信息
        print(f"\n【基本信息】")
        print(f"  初始资金:      ${results['initial_capital']:>12,.2f}")
        print(f"  最终权益:      ${results['final_equity']:>12,.2f}")
        print(f"  总收益:        ${results['total_return']:>12,.2f} ({results['total_return_pct']:+.2f}%)")
        print(f"  年化收益率:    {results['annual_return']:>15.2f}%")
        print(f"  最大回撤:      {results['max_drawdown']:>15.2f}%")

        # 交易统计
        print(f"\n【交易统计】")
        print(f"  总交易次数:    {results['total_trades']:>15}")
        print(f"  盈利次数:      {results['winning_trades']:>15}")
        print(f"  亏损次数:      {results['losing_trades']:>15}")
        print(f"  胜率:          {results['win_rate']:>15.2f}%")

        # 盈亏分析
        print(f"\n【盈亏分析】")
        print(f"  平均盈利:      ${results['avg_win']:>12,.2f}")
        print(f"  平均亏损:      ${results['avg_loss']:>12,.2f}")
        print(f"  盈亏比:        {results['profit_factor']:>15.2f}:1")

        # 风险指标
        print(f"\n【风险指标】")
        print(f"  夏普比率:      {results['sharpe_ratio']:>15.2f}")

        # 评价
        print(f"\n【综合评价】")
        score = self._calculate_score(results)
        print(f"  综合得分:      {score:>15.1f}/100")

        if score >= 80:
            print(f"  评级:          ⭐⭐⭐⭐⭐ 优秀")
        elif score >= 60:
            print(f"  评级:          ⭐⭐⭐⭐ 良好")
        elif score >= 40:
            print(f"  评级:          ⭐⭐⭐ 一般")
        elif score >= 20:
            print(f"  评级:          ⭐⭐ 较差")
        else:
            print(f"  评级:          ⭐ 很差")

        print("\n" + "="*80)

    def _calculate_score(self, results: Dict) -> float:
        """计算综合得分"""
        score = 0

        # 收益率得分（40分）
        if results['total_return_pct'] > 50:
            score += 40
        elif results['total_return_pct'] > 30:
            score += 30
        elif results['total_return_pct'] > 15:
            score += 20
        elif results['total_return_pct'] > 0:
            score += 10

        # 回撤得分（30分）
        if results['max_drawdown'] > -5:
            score += 30
        elif results['max_drawdown'] > -10:
            score += 20
        elif results['max_drawdown'] > -15:
            score += 10

        # 胜率得分（20分）
        if results['win_rate'] > 60:
            score += 20
        elif results['win_rate'] > 50:
            score += 15
        elif results['win_rate'] > 40:
            score += 10

        # 盈亏比得分（10分）
        if results['profit_factor'] > 2:
            score += 10
        elif results['profit_factor'] > 1.5:
            score += 7
        elif results['profit_factor'] > 1:
            score += 5

        return score


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='简单回测引擎 - 验证策略信号质量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 回测BTC/USDT 1小时周期
  python backtest_engine.py BTC/USDT -t 1h

  # 回测ETH/USDT 4小时周期，获取更多数据
  python backtest_engine.py ETH/USDT -t 4h --limit 2000

  # 指定初始资金和仓位
  python backtest_engine.py BTC/USDT -t 1h --capital 50000 --position 0.5
        """
    )

    parser.add_argument('symbol', help='交易对，如 BTC/USDT')
    parser.add_argument('-t', '--timeframe', default='1h',
                        help='时间周期 (1m, 5m, 15m, 1h, 4h, 1d), 默认: 1h')
    parser.add_argument('--capital', type=float, default=10000,
                        help='初始资金（USDT），默认: 10000')
    parser.add_argument('--position', type=float, default=1.0,
                        help='仓位比例（0.0-1.0），默认: 1.0 (100%)')
    parser.add_argument('--commission', type=float, default=0.001,
                        help='手续费率，默认: 0.001 (0.1%%)')
    parser.add_argument('--limit', type=int, default=1000,
                        help='K线数量，默认: 1000')

    args = parser.parse_args()

    # 创建回测引擎
    backtest = SimpleBacktest(
        initial_capital=args.capital,
        position_size_pct=args.position,
        commission=args.commission
    )

    # 运行回测
    try:
        results = backtest.run(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.limit
        )

        # 导出交易记录
        if results['trades']:
            trades_df = pd.DataFrame(results['trades'])
            filename = f"backtest_trades_{args.symbol.replace('/', '_')}_{args.timeframe}.csv"
            trades_df.to_csv(filename, index=False)
            print(f"\n💾 交易记录已导出: {filename}")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
