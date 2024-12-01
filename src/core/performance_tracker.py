from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func
from .models import Trade, Strategy, StrategyPerformance, DailyBalance
from utils.logger import setup_logger

class PerformanceTracker:
    def __init__(self, db):
        self.db = db
        self.logger = setup_logger()
        
    def calculate_strategy_metrics(self, strategy_id, timeframe='1d'):
        """Calculate comprehensive strategy performance metrics"""
        session = self.db.get_session()
        try:
            # Get time range based on timeframe
            end_date = datetime.utcnow()
            if timeframe == '1d':
                start_date = end_date - timedelta(days=1)
            elif timeframe == '1w':
                start_date = end_date - timedelta(weeks=1)
            elif timeframe == '1m':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)
                
            # Query trades for the period
            trades = session.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.executed_at >= start_date,
                Trade.executed_at <= end_date
            ).all()
            
            if not trades:
                return None
                
            # Calculate metrics
            profits = [t.profit_loss for t in trades if t.profit_loss is not None]
            winning_trades = len([p for p in profits if p > 0])
            losing_trades = len([p for p in profits if p < 0])
            
            metrics = {
                'total_trades': len(trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': winning_trades / len(trades) if trades else 0,
                'total_profit_loss': sum(profits),
                'avg_profit_per_trade': np.mean(profits) if profits else 0,
                'max_drawdown': self._calculate_max_drawdown(profits),
                'sharpe_ratio': self._calculate_sharpe_ratio(profits),
                'profit_factor': self._calculate_profit_factor(profits)
            }
            
            return metrics
            
        finally:
            session.close()
            
    def _calculate_max_drawdown(self, profits):
        """Calculate maximum drawdown from profit/loss series"""
        if not profits:
            return 0
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        return np.max(drawdown) if len(drawdown) > 0 else 0
        
    def _calculate_sharpe_ratio(self, profits, risk_free_rate=0.02):
        """Calculate Sharpe ratio of returns"""
        if not profits or len(profits) < 2:
            return 0
        returns = pd.Series(profits)
        excess_returns = returns.mean() - risk_free_rate/252  # Daily risk-free rate
        return excess_returns / returns.std() if returns.std() != 0 else 0
        
    def _calculate_profit_factor(self, profits):
        """Calculate profit factor (gross profit / gross loss)"""
        if not profits:
            return 0
        gross_profit = sum([p for p in profits if p > 0]) or 0
        gross_loss = abs(sum([p for p in profits if p < 0])) or 1  # Avoid division by zero
        return gross_profit / gross_loss
        
    def update_daily_performance(self, strategy_id):
        """Update daily performance metrics for a strategy"""
        metrics = self.calculate_strategy_metrics(strategy_id, '1d')
        if not metrics:
            return
            
        session = self.db.get_session()
        try:
            today = datetime.utcnow().date()
            performance = session.query(StrategyPerformance).filter_by(
                strategy_id=strategy_id,
                date=today
            ).first()
            
            if not performance:
                performance = StrategyPerformance(
                    strategy_id=strategy_id,
                    date=today
                )
                session.add(performance)
            
            # Update metrics
            performance.total_trades = metrics['total_trades']
            performance.winning_trades = metrics['winning_trades']
            performance.losing_trades = metrics['losing_trades']
            performance.win_rate = metrics['win_rate']
            performance.profit_factor = metrics['profit_factor']
            performance.sharpe_ratio = metrics['sharpe_ratio']
            performance.max_drawdown = metrics['max_drawdown']
            performance.total_profit_loss = metrics['total_profit_loss']
            
            session.commit()
            self.logger.info(f"Updated performance metrics for strategy {strategy_id}")
            
        finally:
            session.close()
            
    def get_strategy_summary(self, strategy_id, timeframe='1w'):
        """Get strategy performance summary for reporting"""
        metrics = self.calculate_strategy_metrics(strategy_id, timeframe)
        if not metrics:
            return "No trades executed in the specified timeframe"
            
        return f"""
        Strategy Performance Summary ({timeframe}):
        Total Trades: {metrics['total_trades']}
        Win Rate: {metrics['win_rate']:.2%}
        Total P/L: {metrics['total_profit_loss']:.2f}
        Profit Factor: {metrics['profit_factor']:.2f}
        Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
        Max Drawdown: {metrics['max_drawdown']:.2f}
        Average Profit per Trade: {metrics['avg_profit_per_trade']:.2f}
        """