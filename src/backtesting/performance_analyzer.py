import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from .strategy_tester import Trade
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self, initial_capital: float = 10000):
        """
        Initialize the performance analyzer
        
        Args:
            initial_capital: Starting capital for calculations
        """
        self.initial_capital = initial_capital
        
    def create_equity_curve(self, trades: List[Trade]) -> pd.DataFrame:
        """
        Create equity curve from list of trades
        
        Args:
            trades: List of completed trades
            
        Returns:
            DataFrame with equity curve data
        """
        if not trades:
            return pd.DataFrame()
            
        # Create timeline of equity changes
        equity_changes = []
        
        for trade in trades:
            equity_changes.append({
                'timestamp': trade.exit_time,
                'pnl': trade.pnl
            })
            
        # Convert to DataFrame
        df = pd.DataFrame(equity_changes)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate cumulative equity
        df['equity'] = self.initial_capital + df['pnl'].cumsum()
        df['drawdown'] = df['equity'].cummax() - df['equity']
        df['drawdown_pct'] = df['drawdown'] / df['equity'].cummax()
        
        return df
        
    def calculate_metrics(self, trades: List[Trade], equity_curve: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades: List of completed trades
            equity_curve: DataFrame with equity curve data
            
        Returns:
            Dictionary with performance metrics
        """
        if not trades or equity_curve.empty:
            return {}
            
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # PnL metrics
        gross_profits = sum([t.pnl for t in trades if t.pnl > 0])
        gross_losses = abs(sum([t.pnl for t in trades if t.pnl < 0]))
        net_profit = gross_profits - gross_losses
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
        
        # Average trade metrics
        avg_profit = np.mean([t.pnl for t in trades if t.pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t.pnl for t in trades if t.pnl < 0]) if losing_trades > 0 else 0
        avg_trade = np.mean([t.pnl for t in trades])
        
        # Risk metrics
        max_drawdown = equity_curve['drawdown'].max()
        max_drawdown_pct = equity_curve['drawdown_pct'].max()
        
        # Calculate daily returns
        daily_returns = equity_curve['equity'].pct_change().dropna()
        
        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        
        # Statistical metrics
        pnl_series = pd.Series([t.pnl for t in trades])
        std_dev = pnl_series.std()
        skewness = stats.skew(pnl_series)
        kurtosis = stats.kurtosis(pnl_series)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'gross_profits': gross_profits,
            'gross_losses': gross_losses,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'avg_trade': avg_trade,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'std_dev': std_dev,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
        
    def _calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252
    ) -> float:
        """Calculate annualized Sharpe ratio"""
        excess_returns = returns - risk_free_rate/periods_per_year
        if excess_returns.std() == 0:
            return 0
        return np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()
        
    def _calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252
    ) -> float:
        """Calculate annualized Sortino ratio"""
        excess_returns = returns - risk_free_rate/periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        downside_std = np.sqrt(np.mean(downside_returns**2))
        if downside_std == 0:
            return 0
        return np.sqrt(periods_per_year) * excess_returns.mean() / downside_std
        
    def generate_trade_analysis(self, trades: List[Trade]) -> pd.DataFrame:
        """
        Generate detailed analysis of individual trades
        
        Args:
            trades: List of completed trades
            
        Returns:
            DataFrame with trade analysis
        """
        if not trades:
            return pd.DataFrame()
            
        trade_data = []
        for trade in trades:
            trade_data.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'duration': trade.exit_time - trade.entry_time,
                'position': trade.position.name,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'size': trade.size,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'strategy': trade.strategy_name
            })
            
        return pd.DataFrame(trade_data)