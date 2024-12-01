import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Position(Enum):
    LONG = 1
    SHORT = -1
    NEUTRAL = 0

@dataclass
class Trade:
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position: Position
    size: float
    pnl: float
    pnl_pct: float
    strategy_name: str

class StrategyTester:
    def __init__(
        self,
        initial_capital: float = 10000,
        position_size: float = 0.1,  # 10% of capital per trade
        max_positions: int = 1,
        commission: float = 0.001  # 0.1%
    ):
        """
        Initialize the strategy tester
        
        Args:
            initial_capital: Starting capital for backtesting
            position_size: Size of each position as fraction of capital
            max_positions: Maximum number of simultaneous positions
            commission: Commission rate per trade
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.max_positions = max_positions
        self.commission = commission
        self.reset()
        
    def reset(self):
        """Reset the strategy tester state"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.current_position = Position.NEUTRAL
        
    def calculate_position_size(self, price: float) -> float:
        """Calculate the position size based on current capital"""
        return (self.capital * self.position_size) / price
        
    def execute_trade(
        self,
        time: datetime,
        price: float,
        position: Position,
        strategy_name: str
    ) -> Optional[Trade]:
        """
        Execute a trade and update positions
        
        Args:
            time: Time of the trade
            price: Price at which to execute
            position: Position to take (LONG, SHORT, or NEUTRAL)
            strategy_name: Name of the strategy executing the trade
            
        Returns:
            Completed trade if position is closed, None otherwise
        """
        # If no position change, do nothing
        if position == self.current_position:
            return None
            
        # Close existing position if any
        trade = None
        if self.current_position != Position.NEUTRAL:
            size = self.positions[-1]['size']
            entry_price = self.positions[-1]['price']
            entry_time = self.positions[-1]['time']
            
            # Calculate PnL
            if self.current_position == Position.LONG:
                pnl = size * (price - entry_price)
            else:  # SHORT
                pnl = size * (entry_price - price)
                
            # Subtract commission
            pnl -= (size * price * self.commission)
            pnl_pct = pnl / (size * entry_price)
            
            # Update capital
            self.capital += pnl
            
            # Record trade
            trade = Trade(
                entry_time=entry_time,
                exit_time=time,
                entry_price=entry_price,
                exit_price=price,
                position=self.current_position,
                size=size,
                pnl=pnl,
                pnl_pct=pnl_pct,
                strategy_name=strategy_name
            )
            self.trades.append(trade)
            self.positions.pop()
            
        # Open new position if requested
        if position != Position.NEUTRAL:
            size = self.calculate_position_size(price)
            self.positions.append({
                'time': time,
                'price': price,
                'size': size
            })
            
        self.current_position = position
        return trade
        
    def backtest_strategy(
        self,
        data: pd.DataFrame,
        strategy_func: Callable[[pd.DataFrame], pd.Series],
        strategy_name: str
    ) -> List[Trade]:
        """
        Backtest a strategy on historical data
        
        Args:
            data: DataFrame with historical price data
            strategy_func: Function that generates position signals
            strategy_name: Name of the strategy being tested
            
        Returns:
            List of completed trades
        """
        self.reset()
        
        # Get position signals from strategy
        signals = strategy_func(data)
        
        # Execute trades based on signals
        for time, row in data.iterrows():
            signal = signals.loc[time]
            
            # Convert signal to position
            if signal > 0:
                position = Position.LONG
            elif signal < 0:
                position = Position.SHORT
            else:
                position = Position.NEUTRAL
                
            self.execute_trade(time, row['close'], position, strategy_name)
            
        # Close any remaining position at the end
        if self.current_position != Position.NEUTRAL:
            self.execute_trade(
                data.index[-1],
                data['close'].iloc[-1],
                Position.NEUTRAL,
                strategy_name
            )
            
        return self.trades
        
    def get_strategy_results(self) -> Dict:
        """
        Get summary of strategy performance
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'max_drawdown': 0
            }
            
        # Calculate metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        win_rate = winning_trades / total_trades
        
        gross_profits = sum([t.pnl for t in self.trades if t.pnl > 0])
        gross_losses = abs(sum([t.pnl for t in self.trades if t.pnl < 0]))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
        
        total_pnl = sum([t.pnl for t in self.trades])
        total_pnl_pct = total_pnl / self.initial_capital
        
        # Calculate drawdown
        capital_history = [self.initial_capital]
        for trade in self.trades:
            capital_history.append(capital_history[-1] + trade.pnl)
        
        peak = capital_history[0]
        max_drawdown = 0
        for capital in capital_history[1:]:
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'max_drawdown': max_drawdown
        }