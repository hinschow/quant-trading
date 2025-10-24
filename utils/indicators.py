"""
技术指标计算库
整合常用技术指标：EMA, RSI, MACD, ADX, ATR, Bollinger Bands 等
"""
import pandas as pd
import numpy as np
import talib


def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """
    计算指数移动平均线 (EMA)

    Args:
        df: 数据框
        period: 周期
        column: 计算列名

    Returns:
        EMA 序列
    """
    return talib.EMA(df[column], timeperiod=period)


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    计算相对强弱指标 (RSI)

    Args:
        df: 数据框
        period: 周期，默认 14
        column: 计算列名

    Returns:
        RSI 序列 (0-100)
    """
    return talib.RSI(df[column], timeperiod=period)


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    计算 MACD 指标

    Args:
        df: 数据框
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期

    Returns:
        (macd, signal, hist) 元组
    """
    macd, signal_line, hist = talib.MACD(
        df['close'],
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal
    )
    return macd, signal_line, hist


def calculate_adx(df: pd.DataFrame, period: int = 14):
    """
    计算平均趋向指数 (ADX) 及方向指标

    Args:
        df: 数据框（需包含 high, low, close）
        period: 周期，默认 14

    Returns:
        (adx, plus_di, minus_di) 元组
    """
    adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=period)
    plus_di = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=period)
    minus_di = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=period)
    return adx, plus_di, minus_di


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算真实波动幅度 (ATR)

    Args:
        df: 数据框（需包含 high, low, close）
        period: 周期，默认 14

    Returns:
        ATR 序列
    """
    return talib.ATR(df['high'], df['low'], df['close'], timeperiod=period)


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0):
    """
    计算布林带

    Args:
        df: 数据框
        period: 周期，默认 20
        std_dev: 标准差倍数，默认 2.0

    Returns:
        (upper, middle, lower) 元组
    """
    upper, middle, lower = talib.BBANDS(
        df['close'],
        timeperiod=period,
        nbdevup=std_dev,
        nbdevdn=std_dev,
        matype=0
    )
    return upper, middle, lower


def calculate_kdj(df: pd.DataFrame, fastk_period: int = 9, slowk_period: int = 3, slowd_period: int = 3):
    """
    计算 KDJ 指标（随机指标）

    KDJ是在KD指标基础上的优化，J值更敏感
    - K值：快线（Stochastic %K）
    - D值：慢线（%K的移动平均）
    - J值：超快线（3K - 2D），更灵敏

    Args:
        df: 数据框（需包含 high, low, close）
        fastk_period: RSV周期，默认9
        slowk_period: K平滑周期，默认3
        slowd_period: D平滑周期，默认3

    Returns:
        (k, d, j) 元组
    """
    # 使用talib的STOCH函数计算K和D
    k, d = talib.STOCH(
        df['high'],
        df['low'],
        df['close'],
        fastk_period=fastk_period,
        slowk_period=slowk_period,
        slowk_matype=1,  # EMA
        slowd_period=slowd_period,
        slowd_matype=1   # EMA
    )

    # 计算J值：J = 3K - 2D
    j = 3 * k - 2 * d

    return k, d, j


def calculate_bbw(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.Series:
    """
    计算布林带宽度 (Bollinger Band Width)

    Args:
        df: 数据框
        period: 周期
        std_dev: 标准差倍数

    Returns:
        BBW 序列（归一化）
    """
    upper, middle, lower = calculate_bollinger_bands(df, period, std_dev)
    bbw = (upper - lower) / middle
    return bbw


def calculate_bbw_ratio(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, ma_period: int = 20) -> pd.Series:
    """
    计算布林带宽度比率（相对于均值）

    Args:
        df: 数据框
        period: 布林带周期
        std_dev: 标准差倍数
        ma_period: BBW 均值周期

    Returns:
        BBW Ratio 序列
    """
    bbw = calculate_bbw(df, period, std_dev)
    bbw_ma = bbw.rolling(ma_period).mean()
    return bbw / bbw_ma


def calculate_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    计算成交量移动平均

    Args:
        df: 数据框
        period: 周期

    Returns:
        成交量均线序列
    """
    return df['volume'].rolling(period).mean()


def calculate_all_indicators(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    一次性计算所有技术指标

    Args:
        df: 数据框（需包含 OHLCV 数据）
        params: 参数字典（可选）

    Returns:
        包含所有指标的数据框
    """
    if params is None:
        from config.strategy_params import TREND_FOLLOWING_PARAMS, MEAN_REVERSION_PARAMS, MARKET_REGIME_PARAMS
        params = {
            **TREND_FOLLOWING_PARAMS,
            **MEAN_REVERSION_PARAMS,
            **MARKET_REGIME_PARAMS
        }

    result = df.copy()

    # EMA
    result['ema_fast'] = calculate_ema(df, params.get('ema_fast', 50))
    result['ema_slow'] = calculate_ema(df, params.get('ema_slow', 200))

    # RSI
    result['rsi'] = calculate_rsi(df, params.get('rsi_period', 14))

    # MACD
    macd, signal, hist = calculate_macd(
        df,
        params.get('macd_fast', 12),
        params.get('macd_slow', 26),
        params.get('macd_signal', 9)
    )
    result['macd'] = macd
    result['macd_signal'] = signal
    result['macd_hist'] = hist

    # ADX
    adx, plus_di, minus_di = calculate_adx(df, params.get('adx_period', 14))
    result['adx'] = adx
    result['plus_di'] = plus_di
    result['minus_di'] = minus_di

    # ATR
    result['atr'] = calculate_atr(df, params.get('atr_period', 14))

    # 布林带
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
        df,
        params.get('bb_period', 20),
        params.get('bb_std', 2.0)
    )
    result['bb_upper'] = bb_upper
    result['bb_middle'] = bb_middle
    result['bb_lower'] = bb_lower

    # 布林带宽度
    result['bbw'] = calculate_bbw(df, params.get('bb_period', 20), params.get('bb_std', 2.0))
    result['bbw_ratio'] = calculate_bbw_ratio(
        df,
        params.get('bbw_period', 20),
        params.get('bb_std', 2.0),
        params.get('bbw_ma_period', 20)
    )

    # 成交量均线
    result['volume_ma'] = calculate_volume_ma(df, params.get('volume_ma_period', 20))

    return result


def identify_candlestick_pattern(df: pd.DataFrame) -> dict:
    """
    识别 K 线形态

    Args:
        df: 数据框

    Returns:
        K 线形态字典
    """
    patterns = {}

    # 锤子线（看涨）
    patterns['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])

    # 倒锤子线（看涨）
    patterns['inverted_hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])

    # 吞没形态（看涨）
    patterns['bullish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])

    # 流星线（看跌）
    patterns['shooting_star'] = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])

    # 上吊线（看跌）
    patterns['hanging_man'] = talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])

    return patterns
