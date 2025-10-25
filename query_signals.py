#!/usr/bin/env python3
"""
交易信号查询工具
支持查询、统计、导出历史信号数据
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

from utils.signal_storage import SignalStorage, get_storage
from config.storage_params import STORAGE_PARAMS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_signal_table(signals: list, limit: int = 20):
    """以表格形式打印信号"""
    if not signals:
        print("❌ 没有找到信号记录")
        return

    # 打印表头
    print("\n" + "=" * 150)
    print(f"{'时间':<20} {'币种':<18} {'周期':<6} {'动作':<6} {'强度':<5} {'价格':<10} {'资金费率':<10} {'市场状态':<15} {'触发原因':<40}")
    print("=" * 150)

    # 打印数据（限制显示数量）
    for i, signal in enumerate(signals[:limit]):
        timestamp = signal.get('timestamp', '')
        if isinstance(timestamp, str):
            timestamp = timestamp[:19]  # 只显示到秒

        symbol = signal.get('symbol', '')
        timeframe = signal.get('timeframe', '')
        action = signal.get('action', '')
        strength = signal.get('strength', 0)
        price = signal.get('price', 0.0)
        funding_rate = signal.get('funding_rate')
        market_regime = signal.get('market_regime', '')

        # 颜色标记
        action_display = action
        if action == 'BUY':
            action_display = f"\033[92m{action}\033[0m"  # 绿色
        elif action == 'SELL':
            action_display = f"\033[91m{action}\033[0m"  # 红色

        # 处理原因（合并主要原因和情绪原因）
        reasons = signal.get('reasons', [])
        sentiment_reasons = signal.get('sentiment_reasons', [])
        all_reasons = reasons + sentiment_reasons
        reason_text = ', '.join(all_reasons[:2]) if all_reasons else ''  # 只显示前2个原因
        if len(all_reasons) > 2:
            reason_text += f" (+{len(all_reasons)-2})"

        funding_str = f"{funding_rate:.4f}%" if funding_rate is not None else "N/A"

        print(f"{timestamp:<20} {symbol:<18} {timeframe:<6} {action_display:<6} {strength:<5} {price:<10.4f} {funding_str:<10} {market_regime:<15} {reason_text:<40}")

    if len(signals) > limit:
        print(f"\n... 还有 {len(signals) - limit} 条记录（使用 --limit 参数查看更多）")

    print("=" * 150 + "\n")


def print_stats(stats: dict):
    """打印统计信息"""
    print("\n📊 信号数据库统计")
    print("━" * 80)

    # 数据库信息
    db_path = STORAGE_PARAMS['db_path']
    db_size = stats.get('db_size_mb', 0)
    print(f"📁 数据库文件: {db_path}")
    print(f"💾 文件大小: {db_size:.2f} MB")

    # 总体统计
    total_signals = stats.get('total_signals', 0)
    total_symbols = stats.get('total_symbols', 0)
    oldest = stats.get('oldest_signal', '')
    newest = stats.get('newest_signal', '')
    avg_strength = stats.get('avg_strength', 0)

    print(f"📝 信号总数: {total_signals:,} 条")
    print(f"💰 交易对数: {total_symbols} 个")
    print(f"📅 时间范围: {oldest[:10]} ~ {newest[:10]}")
    print(f"⭐ 平均强度: {avg_strength:.1f}/100")

    # 动作分布
    buy_count = stats.get('buy_signals', 0)
    sell_count = stats.get('sell_signals', 0)
    hold_count = stats.get('hold_signals', 0)

    print(f"\n信号分布:")
    print(f"  \033[92m买入(BUY)\033[0m:  {buy_count:,} 条 ({buy_count/total_signals*100:.1f}%)")
    print(f"  \033[91m卖出(SELL)\033[0m: {sell_count:,} 条 ({sell_count/total_signals*100:.1f}%)")
    print(f"  观望(HOLD):  {hold_count:,} 条 ({hold_count/total_signals*100:.1f}%)")

    # 各币种统计
    symbol_stats = stats.get('symbol_stats', [])
    if symbol_stats:
        print(f"\n各币种信号分布（Top 10）:")
        print(f"{'币种':<20} {'总数':<10} {'买入':<10} {'卖出':<10} {'平均强度':<12} {'最后信号':<20}")
        print("-" * 80)

        for i, s in enumerate(symbol_stats[:10]):
            symbol = s.get('symbol', '')
            count = s.get('signal_count', 0)
            buy = s.get('buy_count', 0)
            sell = s.get('sell_count', 0)
            avg_str = s.get('avg_strength', 0)
            last = s.get('last_signal', '')

            print(f"{symbol:<20} {count:<10} {buy:<10} {sell:<10} {avg_str:<12.1f} {last[:19]:<20}")

    # 清理建议
    retention_days = STORAGE_PARAMS['signal_retention_days']
    print(f"\n💡 提示: 数据保留策略为 {retention_days} 天，过期数据将自动清理")

    print("━" * 80 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='交易信号查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看所有信号
  python query_signals.py

  # 查看BTC的历史信号
  python query_signals.py BTC/USDT:USDT

  # 查看今天的信号
  python query_signals.py --today

  # 查看强度>70的高质量信号
  python query_signals.py --min-strength 70

  # 查看最近7天的买入信号
  python query_signals.py --days 7 --action BUY

  # 查看数据库统计
  python query_signals.py --stats

  # 导出为CSV
  python query_signals.py --export csv --output signals.csv

  # 导出BTC最近30天的信号
  python query_signals.py BTC/USDT:USDT --days 30 --export csv
        """
    )

    # 查询参数
    parser.add_argument('symbol', nargs='?', help='交易对（如 BTC/USDT:USDT）')
    parser.add_argument('--action', choices=['BUY', 'SELL', 'HOLD'], help='信号动作')
    parser.add_argument('--min-strength', type=int, default=0, help='最低信号强度（0-100）')
    parser.add_argument('--limit', type=int, default=20, help='显示数量限制（默认20）')

    # 时间范围
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('--today', action='store_true', help='查看今天的信号')
    time_group.add_argument('--yesterday', action='store_true', help='查看昨天的信号')
    time_group.add_argument('--days', type=int, help='查看最近N天的信号')
    time_group.add_argument('--start', type=str, help='开始日期（YYYY-MM-DD）')

    parser.add_argument('--end', type=str, help='结束日期（YYYY-MM-DD）')

    # 统计和导出
    parser.add_argument('--stats', action='store_true', help='显示数据库统计信息')
    parser.add_argument('--export', choices=['csv', 'json'], help='导出格式')
    parser.add_argument('--output', help='导出文件路径（默认: data/exports/signals_YYYYMMDD.csv）')

    args = parser.parse_args()

    # 获取存储实例
    storage = get_storage()

    if not storage.enabled:
        print("❌ 信号存储功能未启用")
        print("请在 config/storage_params.py 中设置 enable_storage = True")
        sys.exit(1)

    # 统计模式
    if args.stats:
        stats = storage.get_stats()
        print_stats(stats)
        return

    # 构建查询参数
    query_params = {
        'symbol': args.symbol,
        'min_strength': args.min_strength,
        'action': args.action,
    }

    # 处理时间范围
    if args.today:
        query_params['start_date'] = datetime.now().replace(hour=0, minute=0, second=0)
    elif args.yesterday:
        yesterday = datetime.now() - timedelta(days=1)
        query_params['start_date'] = yesterday.replace(hour=0, minute=0, second=0)
        query_params['end_date'] = yesterday.replace(hour=23, minute=59, second=59)
    elif args.days:
        query_params['start_date'] = datetime.now() - timedelta(days=args.days)
    elif args.start:
        query_params['start_date'] = datetime.strptime(args.start, '%Y-%m-%d')

    if args.end:
        query_params['end_date'] = datetime.strptime(args.end, '%Y-%m-%d')

    # 导出模式
    if args.export:
        # 设置默认输出路径
        if not args.output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = args.export
            args.output = f"data/exports/signals_{timestamp}.{ext}"

        # 执行导出
        if args.export == 'csv':
            success = storage.export_to_csv(args.output, **query_params)
        else:
            success = storage.export_to_json(args.output, **query_params)

        if success:
            print(f"✅ 导出成功: {args.output}")
        else:
            print(f"❌ 导出失败")
        return

    # 查询模式
    signals = storage.query_signals(**query_params, limit=None)

    # 显示结果
    if signals:
        print(f"\n🔍 找到 {len(signals)} 条信号记录")
        print_signal_table(signals, limit=args.limit)
    else:
        print("\n❌ 没有找到符合条件的信号")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}", exc_info=True)
        sys.exit(1)
