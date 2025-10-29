"""
量化交易监控Dashboard
实时显示信号、持仓、新闻、情绪分析等
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from urllib.parse import unquote
import sys
import os
import json
import pandas as pd

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.external_sentiment import get_sentiment_analyzer
from utils.hyperliquid_client import HyperliquidClient
from config.strategy_params import TRADING_SYMBOLS, SYMBOL_SPECIFIC_PARAMS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文

# 全局对象
sentiment_analyzer = None
market_client = None

def init_services():
    """初始化服务"""
    global sentiment_analyzer, market_client
    try:
        print("\n正在初始化Dashboard服务...")

        # 初始化情绪分析器
        try:
            sentiment_analyzer = get_sentiment_analyzer()
            print("  ✅ 情绪分析器初始化成功")
        except Exception as e:
            print(f"  ⚠️  情绪分析器初始化失败: {e}")
            sentiment_analyzer = None

        # 初始化市场数据客户端
        try:
            market_client = HyperliquidClient()
            print("  ✅ 市场数据客户端初始化成功")
        except Exception as e:
            print(f"  ⚠️  市场数据客户端初始化失败: {e}")
            market_client = None

        print("✅ Dashboard服务初始化完成\n")

    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html',
                         symbols=TRADING_SYMBOLS,
                         update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/api/market_overview')
def market_overview():
    """市场概览API"""
    try:
        if not market_client:
            return jsonify({
                'success': False,
                'error': '市场数据客户端未初始化',
                'data': []
            })

        overview = []

        for symbol in TRADING_SYMBOLS:
            try:
                # 获取市场数据
                market_data = market_client.get_market_data(symbol)

                # 获取配置
                config = SYMBOL_SPECIFIC_PARAMS.get(symbol, {})
                enabled = config.get('enabled', True)

                overview.append({
                    'symbol': symbol,
                    'price': market_data.get('price', 0) if market_data else 0,
                    'funding_rate': market_data.get('funding_rate', 0) if market_data else 0,
                    'open_interest': market_data.get('open_interest', 0) if market_data else 0,
                    'data_source': market_data.get('source', 'N/A') if market_data else 'N/A',
                    'enabled': enabled,
                    'timeframe': config.get('timeframe_preference', '30m'),
                })
            except Exception as e:
                print(f"获取 {symbol} 数据失败: {e}")
                continue

        return jsonify({
            'success': True,
            'data': overview,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"市场概览API错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'data': []})


@app.route('/api/sentiment/<path:symbol>')
def get_sentiment(symbol):
    """获取指定币种的情绪分析"""
    try:
        # URL解码symbol参数（如 BTC%2FUSDT -> BTC/USDT）
        symbol = unquote(symbol)

        if not sentiment_analyzer:
            return jsonify({'success': False, 'error': '情绪分析器未初始化'})

        sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol)

        return jsonify({
            'success': True,
            'data': sentiment
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/news')
def get_news():
    """获取最新新闻"""
    try:
        if not sentiment_analyzer:
            return jsonify({'success': False, 'error': '新闻监控未初始化'})

        # 获取所有主要币种的新闻
        all_news = []
        for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
            sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol)
            news_list = sentiment.get('details', {}).get('news', {}).get('news', [])
            all_news.extend(news_list)

        # 去重并按时间排序
        seen = set()
        unique_news = []
        for news in all_news:
            title = news.get('title')
            if title and title not in seen:
                seen.add(title)
                unique_news.append(news)

        # 取最新20条
        unique_news = unique_news[:20]

        return jsonify({
            'success': True,
            'data': unique_news,
            'count': len(unique_news)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/signals')
def get_signals():
    """获取交易信号"""
    try:
        signals = []

        for symbol in TRADING_SYMBOLS:
            config = SYMBOL_SPECIFIC_PARAMS.get(symbol, {})
            if not config.get('enabled', True):
                continue

            # 获取市场数据
            market_data = market_client.get_market_data(symbol) if market_client else {}

            # 获取情绪分析
            sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol) if sentiment_analyzer else {}

            # 简单的信号生成逻辑（实际应该调用strategy_engine）
            signal_strength = 50  # 基础分数
            signal_type = 'NEUTRAL'

            # 根据资金费率调整
            funding_rate = market_data.get('funding_rate', 0)
            if funding_rate > 0.001:  # 0.1%
                signal_strength -= 10
                signal_type = 'BEARISH'
            elif funding_rate < -0.001:
                signal_strength += 10
                signal_type = 'BULLISH'

            # 根据情绪调整
            sentiment_score = sentiment.get('total_score', 0)
            signal_strength += sentiment_score * 0.3

            # 判断信号强度
            if signal_strength >= config.get('min_signal_strength', 55):
                signals.append({
                    'symbol': symbol,
                    'type': signal_type,
                    'strength': round(signal_strength, 1),
                    'price': market_data.get('price', 0),
                    'sentiment': sentiment_score,
                    'funding_rate': funding_rate,
                    'timestamp': datetime.now().isoformat(),
                    'alerts': sentiment.get('alerts', []),
                })

        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backtest_results')
def get_backtest_results():
    """获取回测结果摘要"""
    try:
        # 读取回测元数据
        metadata_file = 'backtest_results/multi_timeframe/metadata.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # 读取对比报告（如果存在）
        comparison_file = 'backtest_results/multi_timeframe/comparison_report.txt'
        comparison_text = ""
        if os.path.exists(comparison_file):
            with open(comparison_file, 'r', encoding='utf-8') as f:
                comparison_text = f.read()

        return jsonify({
            'success': True,
            'data': {
                'metadata': metadata,
                'comparison': comparison_text,
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/whale_alerts')
def get_whale_alerts():
    """获取鲸鱼交易告警"""
    try:
        # TODO: 实现真实的鲸鱼监控
        # 这里返回示例数据
        alerts = [
            {
                'symbol': 'BTC',
                'type': 'large_transfer',
                'amount': 150,
                'from': 'Unknown Wallet',
                'to': 'Binance',
                'impact': 'bearish',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            },
        ]

        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 启动量化交易监控Dashboard")
    print("="*60)

    # 初始化服务
    init_services()

    print("\n访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
