# ============================================
# Crypto Trading Signal System
# backed/bots/shared/utils/risk_calculator.py
# Deception: Risk Calculator = Position sizing and risk/reward calculations.
# ============================================

from typing import Tuple, Optional, Dict, Any
from decimal import Decimal
import math

from ..core.logger import get_logger
from ..core.exceptions import BotValidationError

logger = get_logger("risk_calculator")


class RiskCalculator:
    """
    Calculate position sizes, risk/reward ratios, and risk metrics.
    """

    def __init__(
        self,
        account_balance: float,
        default_risk_percentage: float = 1.0,
        min_rr_ratio: float = 4.0,
    ):
        """
        Initialize risk calculator.

        Args:
            account_balance: Total account balance
            default_risk_percentage: Default risk per trade (%)
            min_rr_ratio: Minimum acceptable risk/reward ratio
        """
        self.account_balance = account_balance
        self.default_risk_percentage = default_risk_percentage
        self.min_rr_ratio = min_rr_ratio

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_percentage: Optional[float] = None,
    ) -> float:
        """
        Calculate position size based on risk.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percentage: Risk percentage (uses default if None)

        Returns:
            Position size in base currency
        """
        try:
            risk_pct = risk_percentage or self.default_risk_percentage

            # Calculate risk amount in currency
            risk_amount = self.account_balance * (risk_pct / 100)

            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)

            if risk_per_unit == 0:
                raise BotValidationError("Stop loss cannot equal entry price")

            # Calculate position size
            position_size = risk_amount / risk_per_unit

            return position_size

        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            raise BotValidationError(f"Position size calculation failed: {str(e)}")

    def calculate_risk_reward_ratio(
        self, entry_price: float, stop_loss: float, take_profit: float
    ) -> float:
        """
        Calculate risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Risk/reward ratio
        """
        try:
            risk = abs(entry_price - stop_loss)
            if risk == 0:
                raise BotValidationError("Risk cannot be zero")

            reward = abs(take_profit - entry_price)

            return reward / risk

        except Exception as e:
            logger.error(f"R/R ratio calculation failed: {e}")
            raise BotValidationError(f"R/R ratio calculation failed: {str(e)}") from e

    def calculate_take_profit_for_rr(
        self,
        entry_price: float,
        stop_loss: float,
        signal_type: str,
        target_rr: float = 4.0,
    ) -> float:
        """
        Calculate take profit price for target R/R ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            signal_type: 'BUY' or 'SELL'
            target_rr: Target risk/reward ratio

        Returns:
            Take profit price
        """
        try:
            risk = abs(entry_price - stop_loss)
            reward = risk * target_rr

            if signal_type.upper() == "BUY":
                return entry_price + reward
            else:  # SELL
                return entry_price - reward

        except Exception as e:
            logger.error(f"Take profit calculation failed: {e}")
            raise BotValidationError(f"Take profit calculation failed: {str(e)}") from e

    def validate_signal_risk(
        self, entry_price: float, stop_loss: float, take_profit: float, signal_type: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        # sourcery skip: merge-dict-assign, move-assign-in-block
        """
        Validate if signal meets risk requirements.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            signal_type: 'BUY' or 'SELL'

        Returns:
            Tuple of (is_valid, reason, metrics)
        """
        try:
            metrics = {}

            # Calculate R/R ratio
            rr_ratio = self.calculate_risk_reward_ratio(
                entry_price, stop_loss, take_profit
            )
            metrics["rr_ratio"] = rr_ratio

            # Validate price logic
            if signal_type.upper() == "BUY":
                if not (stop_loss < entry_price < take_profit):
                    return False, "Invalid price levels for BUY signal", metrics
            elif not (take_profit < entry_price < stop_loss):
                return False, "Invalid price levels for SELL signal", metrics

            # Check minimum R/R ratio
            if rr_ratio < self.min_rr_ratio:
                return (
                    False,
                    f"R/R ratio {rr_ratio:.2f} below minimum {self.min_rr_ratio}",
                    metrics,
                )

            # Calculate potential profit/loss
            risk_amount = self.account_balance * (self.default_risk_percentage / 100)
            risk_per_unit = abs(entry_price - stop_loss)
            position_size = risk_amount / risk_per_unit

            potential_loss = risk_amount
            potential_profit = position_size * abs
            metrics["potential_loss"] = potential_loss
            metrics["potential_profit"] = potential_profit
            metrics["position_size"] = position_size
            metrics["risk_percentage"] = self.default_risk_percentage

            return True, "Signal meets risk requirements", metrics

        except Exception as e:
            logger.error(f"Signal validation failed: {e}")
            return False, f"Validation error: {str(e)}", {}

    def calculate_multiple_targets(
        self,
        entry_price: float,
        stop_loss: float,
        signal_type: str,
        target_ratios: list = None,
    ) -> list:
        """
        Calculate multiple take profit targets.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            signal_type: 'BUY' or 'SELL'
            target_ratios: List of R/R ratios for each target

        Returns:
            List of take profit prices
        """
        if target_ratios is None:
            target_ratios = [2.0, 4.0, 6.0]  # Default targets

        targets = []
        for ratio in target_ratios:
            tp = self.calculate_take_profit_for_rr(
                entry_price, stop_loss, signal_type, ratio
            )
            targets.append(tp)

        return targets

    def calculate_breakeven_point(
        self, entry_price: float, stop_loss: float, signal_type: str
    ) -> float:
        """
        Calculate breakeven stop loss level.

        Args:
            entry_price: Entry price
            stop_loss: Original stop loss
            signal_type: 'BUY' or 'SELL'

        Returns:
            Breakeven price (typically entry + small profit)
        """
        risk = abs(entry_price - stop_loss)
        buffer = risk * 0.05  # 5% of risk as buffer

        if signal_type.upper() == "BUY":
            return entry_price + buffer
        else:
            return entry_price - buffer

    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        signal_type: str,
        trailing_percentage: float = 2.0,
    ) -> float:
        """
        Calculate trailing stop loss.

        Args:
            entry_price: Entry price
            current_price: Current market price
            signal_type: 'BUY' or 'SELL'
            trailing_percentage: Trailing stop percentage

        Returns:
            Trailing stop price
        """
        if signal_type.upper() == "BUY":
            # For long position
            return (
                current_price * (1 - trailing_percentage / 100)
                if current_price > entry_price
                else entry_price * (1 - trailing_percentage / 100)
            )
        elif current_price < entry_price:
            return current_price * (1 + trailing_percentage / 100)
        else:
            return entry_price * (1 + trailing_percentage / 100)

    def calculate_kelly_criterion(
        self, win_rate: float, avg_win: float, avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing.

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount

        Returns:
            Optimal position size percentage (0-1)
        """
        try:
            if avg_loss == 0:
                return 0.0

            win_loss_ratio = avg_win / avg_loss
            kelly_percentage = (
                win_rate * win_loss_ratio - (1 - win_rate)
            ) / win_loss_ratio

            # Cap at 25% for safety (fractional Kelly)
            kelly_percentage = max(0, min(kelly_percentage * 0.5, 0.25))

            return kelly_percentage

        except Exception as e:
            logger.error(f"Kelly Criterion calculation failed: {e}")
            return 0.01  # Default to 1% if calculation fails

    def calculate_sharpe_ratio(
        self, returns: list, risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: List of trade returns
            risk_free_rate: Risk-free rate

        Returns:
            Sharpe ratio
        """
        try:
            if not returns or len(returns) < 2:
                return 0.0

            import numpy as np

            returns_array = np.array(returns)

            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)

            if std_return == 0:
                return 0.0

            sharpe = (mean_return - risk_free_rate) / std_return

            return sharpe

        except Exception as e:
            logger.error(f"Sharpe ratio calculation failed: {e}")
            return 0.0

    def calculate_max_drawdown(self, equity_curve: list) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: List of equity values

        Returns:
            Tuple of (max_drawdown_pct, start_idx, end_idx)
        """
        try:
            import numpy as np

            equity = np.array(equity_curve)

            # Calculate running maximum
            running_max = np.maximum.accumulate(equity)

            # Calculate drawdown
            drawdown = (equity - running_max) / running_max * 100

            # Find maximum drawdown
            max_dd = np.min(drawdown)
            max_dd_idx = np.argmin(drawdown)

            # Find start of drawdown period
            start_idx = np.argmax(running_max[: max_dd_idx + 1])

            return abs(max_dd), start_idx, max_dd_idx

        except Exception as e:
            logger.error(f"Max drawdown calculation failed: {e}")
            return 0.0, 0, 0

    def calculate_profit_factor(
        self, winning_trades: list, losing_trades: list
    ) -> float:
        """
        Calculate profit factor.

        Args:
            winning_trades: List of winning trade amounts
            losing_trades: List of losing trade amounts

        Returns:
            Profit factor
        """
        try:
            total_wins = sum(winning_trades) if winning_trades else 0
            total_losses = abs(sum(losing_trades)) if losing_trades else 0

            if total_losses == 0:
                return float("inf") if total_wins > 0 else 0.0

            return total_wins / total_losses

        except Exception as e:
            logger.error(f"Profit factor calculation failed: {e}")
            return 0.0

    def calculate_win_rate(self, winning_trades: int, total_trades: int) -> float:
        """
        Calculate win rate percentage.

        Args:
            winning_trades: Number of winning trades
            total_trades: Total number of trades

        Returns:
            Win rate percentage
        """
        if total_trades == 0:
            return 0.0

        return (winning_trades / total_trades) * 100

    def calculate_expectancy(
        self, win_rate: float, avg_win: float, avg_loss: float
    ) -> float:
        """
        Calculate expectancy (average profit per trade).

        Args:
            win_rate: Win rate (0-100)
            avg_win: Average winning trade
            avg_loss: Average losing trade

        Returns:
            Expectancy value
        """
        win_rate_decimal = win_rate / 100
        loss_rate = 1 - win_rate_decimal

        expectancy = (win_rate_decimal * avg_win) - (loss_rate * avg_loss)

        return expectancy

    def calculate_position_size(
        self, entry_price: float, stop_loss: float, risk_percentage: float = 1.0
    ) -> float:
        """
        Args:
        account_balance: Account balance
        entry_price: Entry price
        stop_loss: Stop loss price
        risk_percentage: Risk percentage

        Returns:
            Position size
        """
        calculator = RiskCalculator(self, risk_percentage)
        return calculator.calculate_position_size(entry_price, stop_loss)

    def calculate_rr_ratio(self, stop_loss: float, take_profit: float) -> float:
        """
        Args:
        entry_price: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price

        Returns:
            Risk/reward ratio
        """
        calculator = RiskCalculator(10000)  # Dummy balance
        return calculator.calculate_risk_reward_ratio(self, stop_loss, take_profit)

    def validate_signal(
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        signal_type: str,
        min_rr: float = 4.0,
    ) -> Tuple[bool, str]:
        """
        Validate a signal quickly using RiskCalculator.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            signal_type: 'BUY' or 'SELL'
            min_rr: Minimum R/R ratio

        Returns:
            Tuple of (is_valid, reason)
        """
        calculator = RiskCalculator(10000, min_rr_ratio=min_rr)
        is_valid, reason, _ = calculator.validate_signal_risk(
            entry_price, stop_loss, take_profit, signal_type
        )
        return is_valid, reason
