"""
量化交易系统主程序入口
v3.2 - 融合版
"""
import argparse
import asyncio
import sys
from datetime import datetime

from utils.logger import logger
from config.settings import PROJECT_NAME, VERSION, ENVIRONMENT


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} - 数字货币量化交易系统"
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['backtest', 'paper', 'live'],
        required=True,
        help='运行模式：backtest(回测), paper(模拟), live(实盘)'
    )

    parser.add_argument(
        '--start',
        type=str,
        help='回测开始日期 (格式: YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end',
        type=str,
        help='回测结束日期 (格式: YYYY-MM-DD)'
    )

    parser.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        help='交易对列表，例如：BTC/USDT ETH/USDT'
    )

    parser.add_argument(
        '--strategy',
        type=str,
        choices=['trend', 'mean_reversion', 'auto'],
        default='auto',
        help='策略类型：trend(趋势), mean_reversion(均值回归), auto(自动切换)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='自定义配置文件路径'
    )

    return parser.parse_args()


async def run_backtest(args):
    """运行回测模式"""
    logger.info("="*60)
    logger.info("启动回测模式")
    logger.info(f"回测区间: {args.start} 至 {args.end}")
    logger.info("="*60)

    try:
        from backtest.engine import BacktestEngine
        from config.strategy_params import TREND_FOLLOWING_PARAMS, MEAN_REVERSION_PARAMS

        # 初始化回测引擎
        engine = BacktestEngine(
            start_date=args.start,
            end_date=args.end,
            symbols=args.symbols,
            initial_capital=10000
        )

        # 运行回测
        results = await engine.run()

        # 输出结果
        logger.info("\n" + "="*60)
        logger.info("回测结果摘要")
        logger.info("="*60)
        logger.info(f"总收益率: {results['total_return']:.2%}")
        logger.info(f"年化收益率: {results['annual_return']:.2%}")
        logger.info(f"最大回撤: {results['max_drawdown']:.2%}")
        logger.info(f"夏普比率: {results['sharpe_ratio']:.2f}")
        logger.info(f"胜率: {results['win_rate']:.2%}")
        logger.info(f"盈亏比: {results['profit_factor']:.2f}")
        logger.info(f"总交易次数: {results['total_trades']}")
        logger.info("="*60)

        # 生成报告
        engine.generate_report()

    except Exception as e:
        logger.error(f"回测失败: {str(e)}", exc_info=True)
        sys.exit(1)


async def run_paper_trading(args):
    """运行模拟交易模式"""
    logger.info("="*60)
    logger.info("启动模拟交易模式")
    logger.info("="*60)

    try:
        from strategies.market_regime import MarketRegimeDetector
        from execution.order_manager import OrderManager
        from risk.risk_manager import RiskManager
        from monitor.alert_manager import AlertManager

        # 初始化各模块
        regime_detector = MarketRegimeDetector()
        order_manager = OrderManager(mode='paper')
        risk_manager = RiskManager()
        alert_manager = AlertManager()

        logger.info("所有模块初始化完成")
        logger.info("开始模拟交易...")

        # 主交易循环
        while True:
            try:
                # TODO: 实现主交易逻辑
                await asyncio.sleep(60)  # 每分钟检查一次

            except KeyboardInterrupt:
                logger.info("接收到停止信号，正在安全退出...")
                break
            except Exception as e:
                logger.error(f"交易循环出错: {str(e)}", exc_info=True)
                await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"模拟交易启动失败: {str(e)}", exc_info=True)
        sys.exit(1)


async def run_live_trading(args):
    """运行实盘交易模式"""
    # 实盘交易需要额外确认
    logger.warning("="*60)
    logger.warning("!!! 警告：即将启动实盘交易模式 !!!")
    logger.warning("="*60)

    confirmation = input("请输入 'YES' 确认启动实盘交易: ")
    if confirmation != "YES":
        logger.info("已取消实盘交易")
        return

    logger.info("="*60)
    logger.info("启动实盘交易模式")
    logger.info(f"环境: {ENVIRONMENT}")
    logger.info("="*60)

    try:
        # TODO: 实现实盘交易逻辑
        logger.info("实盘交易功能开发中...")

    except Exception as e:
        logger.error(f"实盘交易启动失败: {str(e)}", exc_info=True)
        sys.exit(1)


async def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()

    # 打印欢迎信息
    print("\n" + "="*60)
    print(f"  {PROJECT_NAME}")
    print(f"  版本: {VERSION}")
    print(f"  环境: {ENVIRONMENT}")
    print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # 根据模式运行
    try:
        if args.mode == 'backtest':
            if not args.start or not args.end:
                logger.error("回测模式需要指定 --start 和 --end 参数")
                sys.exit(1)
            await run_backtest(args)

        elif args.mode == 'paper':
            await run_paper_trading(args)

        elif args.mode == 'live':
            await run_live_trading(args)

    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("程序已退出")


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
