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
        all_alerts = []

        for symbol in TRADING_SYMBOLS:
            config = SYMBOL_SPECIFIC_PARAMS.get(symbol, {})
            if not config.get('enabled', True):
                continue

            # 获取市场数据
            market_data = market_client.get_market_data(symbol) if market_client else {}
            if not market_data.get('price'):
                continue  # 跳过无法获取数据的币种

            # 获取情绪分析
            sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol) if sentiment_analyzer else {}

            # 改进的信号生成逻辑
            signal_strength = 60  # 提高基础分数
            signal_type = 'NEUTRAL'

            # 根据资金费率调整（更激进）
            funding_rate = market_data.get('funding_rate', 0)
            if funding_rate > 0.0015:  # 0.15%
                signal_strength -= 15
                signal_type = 'BEARISH'
            elif funding_rate > 0.0005:  # 0.05%
                signal_strength -= 5
            elif funding_rate < -0.0015:
                signal_strength += 15
                signal_type = 'BULLISH'
            elif funding_rate < -0.0005:
                signal_strength += 5
                signal_type = 'BULLISH'

            # 根据情绪调整（增强权重）
            sentiment_score = sentiment.get('total_score', 0)
            signal_strength += sentiment_score * 0.5  # 从0.3提高到0.5

            # 根据持仓量变化调整
            oi = market_data.get('open_interest', 0)
            if oi > 0:
                signal_strength += 5  # 有持仓数据加分

            # 收集告警信息
            symbol_alerts = sentiment.get('alerts', [])
            if symbol_alerts:
                all_alerts.extend([f"[{symbol.split('/')[0]}] {alert}" for alert in symbol_alerts])

            # 显示所有启用的币种（即使信号强度不够）
            # 但标注强度质量供用户判断
            signals.append({
                'symbol': symbol,
                'type': signal_type,
                'strength': round(signal_strength, 1),
                'price': market_data.get('price', 0),
                'sentiment': sentiment_score,
                'funding_rate': funding_rate,
                'timestamp': datetime.now().isoformat(),
                'alerts': symbol_alerts,
            })

        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals),
            'all_alerts': all_alerts  # 返回所有告警
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/trading_suggestions')
def get_trading_suggestions():
    """获取买卖指引建议"""
    try:
        suggestions = []

        for symbol in TRADING_SYMBOLS:
            config = SYMBOL_SPECIFIC_PARAMS.get(symbol, {})
            if not config.get('enabled', True):
                continue

            # 获取市场数据
            market_data = market_client.get_market_data(symbol) if market_client else {}
            if not market_data.get('price'):
                continue

            current_price = market_data.get('price', 0)
            funding_rate = market_data.get('funding_rate', 0)

            # 获取情绪分析
            sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol) if sentiment_analyzer else {}
            sentiment_score = sentiment.get('total_score', 0)

            # 计算信号强度（复用signals逻辑）
            signal_strength = 60
            signal_type = 'HOLD'  # 默认持有

            # 资金费率判断
            if funding_rate > 0.0015:
                signal_strength -= 15
                signal_type = 'SELL'
            elif funding_rate > 0.0005:
                signal_strength -= 5
            elif funding_rate < -0.0015:
                signal_strength += 15
                signal_type = 'BUY'
            elif funding_rate < -0.0005:
                signal_strength += 5
                signal_type = 'BUY'

            # 情绪调整
            signal_strength += sentiment_score * 0.5

            # OI加分
            if market_data.get('open_interest', 0) > 0:
                signal_strength += 5

            # 强度判断
            min_strength = config.get('min_signal_strength', 55)
            if signal_strength < min_strength - 10:
                signal_type = 'HOLD'  # 信号太弱，持币观望

            # 计算止盈止损价格
            stop_loss_pct = config.get('stop_loss_pct', 0.03)
            take_profit_pct = config.get('take_profit_pct', 0.05)

            if signal_type == 'BUY':
                entry_price = current_price
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit = current_price * (1 + take_profit_pct)
                action = '做多'
                confidence = 'high' if signal_strength >= min_strength else 'medium' if signal_strength >= min_strength - 5 else 'low'
            elif signal_type == 'SELL':
                entry_price = current_price
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit = current_price * (1 - take_profit_pct)
                action = '做空'
                confidence = 'high' if signal_strength >= min_strength else 'medium' if signal_strength >= min_strength - 5 else 'low'
            else:
                entry_price = current_price
                stop_loss = None
                take_profit = None
                action = '观望'
                confidence = 'low'

            suggestions.append({
                'symbol': symbol,
                'action': action,  # 做多/做空/观望
                'signal_type': signal_type,  # BUY/SELL/HOLD
                'confidence': confidence,  # high/medium/low
                'strength': round(signal_strength, 1),
                'entry_price': round(entry_price, 6),
                'stop_loss': round(stop_loss, 6) if stop_loss else None,
                'take_profit': round(take_profit, 6) if take_profit else None,
                'risk_reward_ratio': round(take_profit_pct / stop_loss_pct, 2) if stop_loss else None,
                'sentiment': sentiment_score,
                'funding_rate': funding_rate,
                'reason': _generate_reason(signal_type, signal_strength, sentiment_score, funding_rate),
            })

        return jsonify({
            'success': True,
            'data': suggestions,
            'count': len(suggestions)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def _generate_reason(signal_type, strength, sentiment, funding_rate):
    """生成买卖原因说明"""
    reasons = []

    if signal_type == 'BUY':
        if funding_rate < -0.001:
            reasons.append('资金费率负值（空头占优，可能反转）')
        if sentiment > 5:
            reasons.append(f'外部情绪看涨（+{sentiment}分）')
        if strength >= 70:
            reasons.append('信号强度高')
    elif signal_type == 'SELL':
        if funding_rate > 0.001:
            reasons.append('资金费率过高（多头拥挤）')
        if sentiment < -5:
            reasons.append(f'外部情绪看跌（{sentiment}分）')
        if strength >= 70:
            reasons.append('信号强度高')
    else:
        reasons.append('信号不够明确')

    return '；'.join(reasons) if reasons else '市场中性'


@app.route('/api/whale_alerts')
def get_whale_alerts():
    """获取鲸鱼动态"""
    try:
        if not sentiment_analyzer:
            return jsonify({'success': False, 'error': '情绪分析器未初始化'})

        whale_transactions = []

        # 获取主要币种的鲸鱼交易
        for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'SUI/USDT']:
            try:
                sentiment = sentiment_analyzer.get_comprehensive_sentiment(symbol)
                whale_data = sentiment.get('details', {}).get('whale', {})
                transactions = whale_data.get('transactions', [])

                # 只保留最近的大额交易
                for tx in transactions[:3]:  # 每个币种最多3条
                    whale_transactions.append({
                        'symbol': symbol.split('/')[0],
                        'amount': tx.get('amount', 0),
                        'value_usd': tx.get('value_usd', 0),
                        'type': tx.get('type', 'unknown'),
                        'timestamp': tx.get('timestamp', ''),
                        'description': tx.get('description', '')
                    })
            except Exception as e:
                continue

        # 按金额排序，取前10条
        whale_transactions.sort(key=lambda x: x.get('value_usd', 0), reverse=True)
        whale_transactions = whale_transactions[:10]

        return jsonify({
            'success': True,
            'data': whale_transactions,
            'count': len(whale_transactions)
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


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 启动量化交易监控Dashboard")
    print("="*60)

    # 初始化服务
    init_services()

    print("\n访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
