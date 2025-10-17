
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/utils/indicators.py
# Deception: Technical Indicators = MTechnical analysis indicators (RSI, MACD, Bollinger Bands, etc.)
# ============================================

# ============================================ Standard Library
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional, Union
from decimal import Decimal

# ============================================ Custom Library
from ..core.logger import get_logger
from ..core.exceptions import BotIndicatorError

logger = get_logger("indicators")

# ==================== TREND INDICATORS ====================
def sma(data: Union[List[float], pd.Series], period: int = 20) -> np.ndarray:
    """
    Simple Moving Average.

    Args:
        data: Price data
        period: Period for SMA

    Returns:
        SMA values
    """
    try:
        series = pd.Series(data)
        return series.rolling(window=period).mean().values
    except Exception as e:
        raise BotIndicatorError(f"SMA calculation failed: {e}", indicator="SMA") from e

def ema(data: Union[List[float], pd.Series], period: int = 20) -> np.ndarray:
    """
    Exponential Moving Average.

    Args:
        data: Price data
        period: Period for EMA

    Returns:
        EMA values
    """
    try:
        series = pd.Series(data)
        return series.ewm(span=period, adjust=False).mean().values
    except Exception as e:
        raise BotIndicatorError(f"EMA calculation failed: {e}", indicator="EMA")

def macd(
    data: Union[List[float], pd.Series],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    MACD (Moving Average Convergence Divergence).

    Args:
        data: Price data
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    try:
        series = pd.Series(data)

        # Calculate MACD line
        fast_ema = series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = series.ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line.values, signal_line.values, histogram.values

    except Exception as e:
        raise BotIndicatorError(f"MACD calculation failed: {e}", indicator="MACD")

def adx(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    period: int = 14,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    ADX (Average Directional Index).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for ADX

    Returns:
        Tuple of (adx, plus_di, minus_di)
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Calculate True Range
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift())
        df["tr3"] = abs(df["low"] - df["close"].shift())
        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

        # Calculate Directional Movement
        df["up_move"] = df["high"] - df["high"].shift()
        df["down_move"] = df["low"].shift() - df["low"]

        df["plus_dm"] = np.where(
            (df["up_move"] > df["down_move"]) & (df["up_move"] > 0), df["up_move"], 0
        )
        df["minus_dm"] = np.where(
            (df["down_move"] > df["up_move"]) & (df["down_move"] > 0),
            df["down_move"],
            0,
        )

        # Smooth TR and DM
        df["atr"] = df["tr"].rolling(window=period).mean()
        df["plus_dm_smooth"] = df["plus_dm"].rolling(window=period).mean()
        df["minus_dm_smooth"] = df["minus_dm"].rolling(window=period).mean()

        # Calculate DI
        df["plus_di"] = 100 * df["plus_dm_smooth"] / df["atr"]
        df["minus_di"] = 100 * df["minus_dm_smooth"] / df["atr"]

        # Calculate DX and ADX
        df["dx"] = (
            100 * abs(df["plus_di"] - df["minus_di"]) / (df["plus_di"] + df["minus_di"])
        )
        df["adx"] = df["dx"].rolling(window=period).mean()

        return df["adx"].values, df["plus_di"].values, df["minus_di"].values

    except Exception as e:
        raise BotIndicatorError(f"ADX calculation failed: {e}", indicator="ADX")

# ==================== MOMENTUM INDICATORS ====================
def rsi(data: Union[List[float], pd.Series], period: int = 14) -> np.ndarray:
    """
    RSI (Relative Strength Index).

    Args:
        data: Price data
        period: Period for RSI

    Returns:
        RSI values
    """
    try:
        series = pd.Series(data)

        # Calculate price changes
        delta = series.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    except Exception as e:
        raise BotIndicatorError(f"RSI calculation failed: {e}", indicator="RSI") from e

def stochastic(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    k_period: int = 14,
    d_period: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stochastic Oscillator.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period
        d_period: %D period

    Returns:
        Tuple of (%K, %D)
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Calculate %K
        lowest_low = df["low"].rolling(window=k_period).min()
        highest_high = df["high"].rolling(window=k_period).max()

        df["k"] = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)

        # Calculate %D (SMA of %K)
        df["d"] = df["k"].rolling(window=d_period).mean()

        return df["k"].values, df["d"].values

    except Exception as e:
        raise BotIndicatorError(
            f"Stochastic calculation failed: {e}", indicator="Stochastic"
        )

def roc(data: Union[List[float], pd.Series], period: int = 12) -> np.ndarray:
    """
    ROC (Rate of Change).

    Args:
        data: Price data
        period: Period for ROC

    Returns:
        ROC values
    """
    try:
        series = pd.Series(data)
        roc = ((series - series.shift(period)) / series.shift(period)) * 100
        return roc.values
    except Exception as e:
        raise BotIndicatorError(f"ROC calculation failed: {e}", indicator="ROC")

def cci(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    period: int = 20,
) -> np.ndarray:
    """
    CCI (Commodity Channel Index).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for CCI

    Returns:
        CCI values
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Calculate Typical Price
        df["tp"] = (df["high"] + df["low"] + df["close"]) / 3

        # Calculate SMA of TP
        df["sma_tp"] = df["tp"].rolling(window=period).mean()

        # Calculate Mean Deviation
        df["mad"] = (
            df["tp"].rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        )

        # Calculate CCI
        df["cci"] = (df["tp"] - df["sma_tp"]) / (0.015 * df["mad"])

        return df["cci"].values

    except Exception as e:
        raise BotIndicatorError(f"CCI calculation failed: {e}", indicator="CCI")

# ==================== VOLATILITY INDICATORS ====================
def bollinger_bands(
    data: Union[List[float], pd.Series], period: int = 20, std_dev: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bollinger Bands.

    Args:
        data: Price data
        period: Period for BB
        std_dev: Standard deviation multiplier

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    try:
        series = pd.Series(data)

        # Calculate middle band (SMA)
        middle = series.rolling(window=period).mean()

        # Calculate standard deviation
        std = series.rolling(window=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper.values, middle.values, lower.values

    except Exception as e:
        raise BotIndicatorError(
            f"Bollinger Bands calculation failed: {e}", indicator="BB"
        )

def atr(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    period: int = 14,
) -> np.ndarray:
    """
    ATR (Average True Range).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for ATR

    Returns:
        ATR values
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Calculate True Range
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift())
        df["tr3"] = abs(df["low"] - df["close"].shift())
        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

        # Calculate ATR
        atr = df["tr"].rolling(window=period).mean()

        return atr.values

    except Exception as e:
        raise BotIndicatorError(f"ATR calculation failed: {e}", indicator="ATR")

def keltner_channels(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    period: int = 20,
    multiplier: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Keltner Channels.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for channels
        multiplier: ATR multiplier

    Returns:
        Tuple of (upper_channel, middle_line, lower_channel)
    """
    try:
        # Calculate middle line (EMA of close)
        middle = ema(close, period)

        # Calculate ATR
        atr_values = atr(high, low, close, period)

        # Calculate channels
        upper = middle + (atr_values * multiplier)
        lower = middle - (atr_values * multiplier)

        return upper, middle, lower

    except Exception as e:
        raise BotIndicatorError(
            f"Keltner Channels calculation failed: {e}", indicator="Keltner"
        )

# ==================== VOLUME INDICATORS ====================
def obv(
    close: Union[List[float], pd.Series], volume: Union[List[float], pd.Series]
) -> np.ndarray:
    """
    OBV (On-Balance Volume).

    Args:
        close: Close prices
        volume: Volume data

    Returns:
        OBV values
    """
    try:
        df = pd.DataFrame({"close": close, "volume": volume})

        # Calculate price change direction
        df["direction"] = np.where(df["close"] > df["close"].shift(), 1, -1)
        df["direction"] = np.where(
            df["close"] == df["close"].shift(), 0, df["direction"]
        )

        # Calculate OBV
        df["obv"] = (df["direction"] * df["volume"]).cumsum()

        return df["obv"].values

    except Exception as e:
        raise BotIndicatorError(f"OBV calculation failed: {e}", indicator="OBV")

def vwap(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    volume: Union[List[float], pd.Series],
) -> np.ndarray:
    """
    VWAP (Volume Weighted Average Price).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume data

    Returns:
        VWAP values
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})

        # Calculate typical price
        df["tp"] = (df["high"] + df["low"] + df["close"]) / 3

        # Calculate VWAP
        df["tp_volume"] = df["tp"] * df["volume"]
        df["vwap"] = df["tp_volume"].cumsum() / df["volume"].cumsum()

        return df["vwap"].values

    except Exception as e:
        raise BotIndicatorError(f"VWAP calculation failed: {e}", indicator="VWAP")

def mfi(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    volume: Union[List[float], pd.Series],
    period: int = 14,
) -> np.ndarray:
    """
    MFI (Money Flow Index).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume data
        period: Period for MFI

    Returns:
        MFI values
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})

        # Calculate typical price
        df["tp"] = (df["high"] + df["low"] + df["close"]) / 3

        # Calculate raw money flow
        df["mf"] = df["tp"] * df["volume"]

        # Determine positive and negative money flow
        df["mf_positive"] = np.where(df["tp"] > df["tp"].shift(), df["mf"], 0)
        df["mf_negative"] = np.where(df["tp"] < df["tp"].shift(), df["mf"], 0)

        # Calculate money flow ratio
        positive_mf = df["mf_positive"].rolling(window=period).sum()
        negative_mf = df["mf_negative"].rolling(window=period).sum()

        mfr = positive_mf / negative_mf

        # Calculate MFI
        mfi = 100 - (100 / (1 + mfr))

        return mfi.values

    except Exception as e:
        raise BotIndicatorError(f"MFI calculation failed: {e}", indicator="MFI")

# ==================== CUSTOM INDICATORS ====================
def trend_strength(
    close: Union[List[float], pd.Series], short_period: int = 20, long_period: int = 50
) -> np.ndarray:
    """
    Calculate trend strength (0-100).

    Args:
        close: Close prices
        short_period: Short MA period
        long_period: Long MA period

    Returns:
        Trend strength values
    """
    try:
        series = pd.Series(close)

        short_ma = series.rolling(window=short_period).mean()
        long_ma = series.rolling(window=long_period).mean()

        # Calculate difference percentage
        diff_pct = ((short_ma - long_ma) / long_ma) * 100

        # Normalize to 0-100 scale
        strength = np.abs(diff_pct)
        strength = np.clip(strength * 10, 0, 100)  # Scale factor

        return strength.values

    except Exception as e:
        raise BotIndicatorError(
            f"Trend strength calculation failed: {e}", indicator="TrendStrength"
        )

def volatility_index(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    period: int = 14,
) -> np.ndarray:
    """
    Custom volatility index (0-100).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for calculation

    Returns:
        Volatility index values
    """
    try:
        # Calculate ATR
        atr_values = atr(high, low, close, period)

        # Calculate as percentage of price
        close_series = pd.Series(close)
        volatility = (atr_values / close_series) * 100

        # Normalize to 0-100
        volatility = np.clip(volatility * 10, 0, 100)

        return volatility

    except Exception as e:
        raise BotIndicatorError(
            f"Volatility index calculation failed: {e}", indicator="VolatilityIndex"
        )

def support_resistance_levels(
    high: Union[List[float], pd.Series],
    low: Union[List[float], pd.Series],
    close: Union[List[float], pd.Series],
    lookback: int = 100,
    num_levels: int = 3,
) -> Tuple[List[float], List[float]]:
    """
    Identify support and resistance levels.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        lookback: Lookback period
        num_levels: Number of levels to identify

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    try:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Get recent data
        recent_data = df.tail(lookback)

        # Find local maxima (resistance)
        resistance_candidates = []
        resistance_candidates.extend(
            recent_data["high"].iloc[i]
            for i in range(2, len(recent_data) - 2)
            if (
                recent_data["high"].iloc[i] > recent_data["high"].iloc[i - 1]
                and recent_data["high"].iloc[i]
                > recent_data["high"].iloc[i - 2]
                and recent_data["high"].iloc[i]
                > recent_data["high"].iloc[i + 1]
                and recent_data["high"].iloc[i]
                > recent_data["high"].iloc[i + 2]
            )
        )
        # Find local minima (support)
        support_candidates = []
        support_candidates.extend(
            recent_data["low"].iloc[i]
            for i in range(2, len(recent_data) - 2)
            if (
                recent_data["low"].iloc[i] < recent_data["low"].iloc[i - 1]
                and recent_data["low"].iloc[i] < recent_data["low"].iloc[i - 2]
                and recent_data["low"].iloc[i] < recent_data["low"].iloc[i + 1]
                and recent_data["low"].iloc[i] < recent_data["low"].iloc[i + 2]
            )
        )
        # Sort and get top levels
        resistance_levels = sorted(set(resistance_candidates), reverse=True)[
            :num_levels
        ]
        support_levels = sorted(set(support_candidates))[:num_levels]

        return support_levels, resistance_levels

    except Exception as e:
        raise BotIndicatorError(
            f"Support/Resistance calculation failed: {e}", indicator="SupportResistance"
        )

# ==================== HELPER FUNCTIONS ====================
def calculate_all_indicators(
    open_prices: List[float],
    high: List[float],
    low: List[float],
    close: List[float],
    volume: List[float],
) -> Dict[str, float]:  # sourcery skip: merge-dict-assign
    """
    Calculate all indicators for latest candle.

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume data

    Returns:
        Dictionary of indicator values
    """
    try:
        indicators = {}

        # Trend indicators
        indicators["sma_20"] = sma(close, 20)[-1]
        indicators["sma_50"] = sma(close, 50)[-1]
        indicators["sma_200"] = sma(close, 200)[-1]
        indicators["ema_12"] = ema(close, 12)[-1]
        indicators["ema_26"] = ema(close, 26)[-1]

        macd_line, signal_line, histogram = macd(close)
        indicators["macd_line"] = macd_line[-1]
        indicators["macd_signal"] = signal_line[-1]
        indicators["macd_histogram"] = histogram[-1]

        # Momentum indicators
        indicators["rsi_14"] = rsi(close, 14)[-1]

        k, d = stochastic(high, low, close)
        indicators["stoch_k"] = k[-1]
        indicators["stoch_d"] = d[-1]

        indicators["roc_12"] = roc(close, 12)[-1]
        indicators["cci_20"] = cci(high, low, close, 20)[-1]

        # Volatility indicators
        upper_bb, middle_bb, lower_bb = bollinger_bands(close)
        indicators["bb_upper"] = upper_bb[-1]
        indicators["bb_middle"] = middle_bb[-1]
        indicators["bb_lower"] = lower_bb[-1]
        indicators["bb_width"] = (upper_bb[-1] - lower_bb[-1]) / middle_bb[-1] * 100

        indicators["atr"] = atr(high, low, close, 14)[-1]

        # Volume indicators
        indicators["obv"] = obv(close, volume)[-1]
        indicators["vwap"] = vwap(high, low, close, volume)[-1]
        indicators["mfi"] = mfi(high, low, close, volume, 14)[-1]

        # Custom indicators
        indicators["trend_strength"] = trend_strength(close)[-1]
        indicators["volatility_index"] = volatility_index(high, low, close)[-1]

        # Clean NaN values
        indicators = {
            k: (None if np.isnan(v) else v) for k, v in indicators.items()
        }

        return indicators

    except Exception as e:
        logger.error(f"Failed to calculate indicators: {e}")
        return {}
