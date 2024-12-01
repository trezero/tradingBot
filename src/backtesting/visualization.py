import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Optional
from .strategy_tester import Trade, Position
import logging

logger = logging.getLogger(__name__)

class BacktestVisualizer:
    def __init__(self, width: int = 1200, height: int = 800):
        """
        Initialize the backtest visualizer
        
        Args:
            width: Width of the plots
            height: Height of the plots
        """
        self.width = width
        self.height = height
        
    def plot_backtest_results(
        self,
        price_data: pd.DataFrame,
        trades: List[Trade],
        indicators: Optional[Dict[str, pd.Series]] = None,
        show_volume: bool = True
    ) -> go.Figure:
        """
        Create interactive plot of backtest results
        
        Args:
            price_data: DataFrame with OHLCV data
            trades: List of completed trades
            indicators: Dictionary of technical indicators to plot
            show_volume: Whether to show volume subplot
            
        Returns:
            Plotly figure object
        """
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2 if show_volume else 1,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3] if show_volume else [1]
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=price_data.index,
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add volume bars if requested
        if show_volume:
            colors = ['red' if close < open else 'green'
                     for close, open in zip(price_data['close'], price_data['open'])]
            
            fig.add_trace(
                go.Bar(
                    x=price_data.index,
                    y=price_data['volume'],
                    name='Volume',
                    marker_color=colors
                ),
                row=2, col=1
            )
        
        # Add indicators
        if indicators:
            for name, data in indicators.items():
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data,
                        name=name,
                        line=dict(width=1)
                    ),
                    row=1, col=1
                )
        
        # Add trade markers
        for trade in trades:
            # Entry markers
            fig.add_trace(
                go.Scatter(
                    x=[trade.entry_time],
                    y=[trade.entry_price],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up' if trade.position == Position.LONG else 'triangle-down',
                        size=12,
                        color='green' if trade.position == Position.LONG else 'red'
                    ),
                    name=f"{trade.position.name} Entry"
                ),
                row=1, col=1
            )
            
            # Exit markers
            fig.add_trace(
                go.Scatter(
                    x=[trade.exit_time],
                    y=[trade.exit_price],
                    mode='markers',
                    marker=dict(
                        symbol='x',
                        size=12,
                        color='red' if trade.position == Position.LONG else 'green'
                    ),
                    name=f"{trade.position.name} Exit"
                ),
                row=1, col=1
            )
        
        # Update layout
        fig.update_layout(
            title='Backtest Results',
            width=self.width,
            height=self.height,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        return fig
        
    def plot_equity_curve(
        self,
        equity_curve: pd.DataFrame,
        metrics: Dict
    ) -> go.Figure:
        """
        Create interactive equity curve plot
        
        Args:
            equity_curve: DataFrame with equity curve data
            metrics: Dictionary of performance metrics
            
        Returns:
            Plotly figure object
        """
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('Equity Curve', 'Drawdown')
        )
        
        # Add equity curve
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['equity'],
                name='Equity',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # Add drawdown
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['drawdown_pct'] * 100,
                name='Drawdown %',
                fill='tozeroy',
                line=dict(color='red', width=1)
            ),
            row=2, col=1
        )
        
        # Add performance metrics as annotations
        metrics_text = (
            f"Net Profit: ${metrics['net_profit']:.2f}<br>"
            f"Win Rate: {metrics['win_rate']:.1%}<br>"
            f"Profit Factor: {metrics['profit_factor']:.2f}<br>"
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}<br>"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.1%}"
        )
        
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            text=metrics_text,
            showarrow=False,
            font=dict(size=12),
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        # Update layout
        fig.update_layout(
            title='Strategy Performance',
            width=self.width,
            height=self.height,
            showlegend=True,
            yaxis2_tickformat='.1%'
        )
        
        return fig
        
    def plot_monthly_returns(self, equity_curve: pd.DataFrame) -> go.Figure:
        """
        Create monthly returns heatmap
        
        Args:
            equity_curve: DataFrame with equity curve data
            
        Returns:
            Plotly figure object
        """
        # Calculate monthly returns
        monthly_returns = (
            equity_curve['equity']
            .resample('M')
            .last()
            .pct_change()
            .mul(100)
            .round(2)
        )
        
        # Create monthly returns matrix
        returns_matrix = (
            monthly_returns
            .groupby([monthly_returns.index.year, monthly_returns.index.month])
            .first()
            .unstack()
        )
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=returns_matrix.values,
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            y=returns_matrix.index,
            colorscale='RdYlGn',
            text=returns_matrix.values.round(1),
            texttemplate='%{text}%',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Returns (%)',
            width=self.width,
            height=self.height // 2
        )
        
        return fig