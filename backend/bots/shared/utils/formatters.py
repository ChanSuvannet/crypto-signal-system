
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/utils/validators.py
# Deception: Formatters = Data formatting utilities.
# ============================================

from typing import Any, Union, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..core.logger import get_logger

logger = get_logger('formatters')


class DataFormatter:
    """Format data for display and storage."""
    
    @staticmethod
    def format_price(
        price: Union[float, Decimal],
        decimals: int = 2,
        include_currency: bool = True,
        currency_symbol: str = "$"
    ) -> str:
        """
        Format price for display.
        
        Args:
            price: Price value
            decimals: Number of decimal places
            include_currency: Include currency symbol
            currency_symbol: Currency symbol to use
            
        Returns:
            Formatted price string
        """
        try:
            price_float = float(price)
            
            # Format with commas and decimals
            formatted = f"{price_float:,.{decimals}f}"
            
            if include_currency:
                formatted = f"{currency_symbol}{formatted}"
            
            return formatted
            
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_percentage(
        value: Union[float, Decimal],
        decimals: int = 2,
        include_sign: bool = True
    ) -> str:
        """
        Format percentage value.
        
        Args:
            value: Percentage value
            decimals: Number of decimal places
            include_sign: Include + sign for positive values
            
        Returns:
            Formatted percentage string
        """
        try:
            value_float = float(value)
            
            formatted = f"{value_float:.{decimals}f}%"
            
            if include_sign and value_float > 0:
                formatted = f"+{formatted}"
            
            return formatted
            
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_volume(
        volume: Union[float, Decimal],
        compact: bool = True
    ) -> str:
        """
        Format volume for display.
        
        Args:
            volume: Volume value
            compact: Use compact notation (K, M, B)
            
        Returns:
            Formatted volume string
        """
        try:
            volume_float = float(volume)
            
            if not compact:
                return f"{volume_float:,.2f}"
            
            # Use compact notation
            if volume_float >= 1_000_000_000:
                return f"{volume_float / 1_000_000_000:.2f}B"
            elif volume_float >= 1_000_000:
                return f"{volume_float / 1_000_000:.2f}M"
            elif volume_float >= 1_000:
                return f"{volume_float / 1_000:.2f}K"
            else:
                return f"{volume_float:.2f}"
            
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_timestamp(
        timestamp: datetime,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        include_timezone: bool = False
    ) -> str:
        """
        Format timestamp for display.
        
        Args:
            timestamp: Datetime object
            format_str: Format string
            include_timezone: Include timezone info
            
        Returns:
            Formatted timestamp string
        """
        try:
            formatted = timestamp.strftime(format_str)
            
            if include_timezone:
                formatted += " UTC"
            
            return formatted
            
        except (AttributeError, ValueError):
            return "N/A"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        try:
            duration = timedelta(seconds=seconds)
            
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if seconds > 0 or not parts:
                parts.append(f"{seconds}s")
            
            return " ".join(parts)
            
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_signal(signal_data: dict) -> str:
        """
        Format signal for display.
        
        Args:
            signal_data: Signal dictionary
            
        Returns:
            Formatted signal string
        """
        try:
            return f"""
📊 SIGNAL: {signal_data.get('signal_type')} {signal_data.get('symbol')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry:       {DataFormatter.format_price(signal_data.get('entry_price'))}
Stop Loss:   {DataFormatter.format_price(signal_data.get('stop_loss'))}
Take Profit: {DataFormatter.format_price(signal_data.get('take_profit_1'))}
R/R Ratio:   1:{signal_data.get('risk_reward_ratio', 0):.1f}
Confidence:  {DataFormatter.format_percentage(signal_data.get('final_confidence', 0))}
Timeframe:   {signal_data.get('timeframe')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """.strip()
            
        except Exception as e:
            logger.error(f"Signal formatting failed: {e}")
            return "Signal formatting error"
    
    @staticmethod
    def format_trade_result(result_data: dict) -> str:
        """
        Format trade result for display.
        
        Args:
            result_data: Trade result dictionary
            
        Returns:
            Formatted result string
        """
        try:
            pnl = result_data.get('profit_loss', 0)
            pnl_pct = result_data.get('profit_loss_percentage', 0)
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            
            return f"""
{emoji} TRADE RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signal:     {result_data.get('signal_id')}
P/L:        {DataFormatter.format_price(pnl)} ({DataFormatter.format_percentage(pnl_pct)})
Outcome:    {result_data.get('outcome')}
Duration:   {DataFormatter.format_duration(result_data.get('holding_duration_minutes', 0) * 60)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """.strip()
            
        except Exception as e:
            logger.error(f"Trade result formatting failed: {e}")
            return "Trade result formatting error"
    
    @staticmethod
    def format_news_article(article_data: dict) -> str:
        """
        Format news article for display.
        
        Args:
            article_data: News article dictionary
            
        Returns:
            Formatted article string
        """
        try:
            sentiment = article_data.get('sentiment_label', 'NEUTRAL')
            impact = article_data.get('impact_level', 'LOW')
            
            sentiment_emoji = {
                'VERY_BULLISH': '🚀',
                'BULLISH': '📈',
                'NEUTRAL': '➖',
                'BEARISH': '📉',
                'VERY_BEARISH': '💥'
            }.get(sentiment, '❓')
            
            return f"""
{sentiment_emoji} {article_data.get('title')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source:     {article_data.get('source')}
Sentiment:  {sentiment}
Impact:     {impact}
Symbol:     {article_data.get('symbol')}
Published:  {DataFormatter.format_timestamp(article_data.get('published_at'))}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """.strip()
            
        except Exception as e:
            logger.error(f"News formatting failed: {e}")
            return "News formatting error"
    
    # @staticmethod
    # def format_performance_summary(metrics: dict) ->