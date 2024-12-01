import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting import (
    HistoricalDataLoader,
    StrategyTester,
    PerformanceAnalyzer,
    BacktestVisualizer
)
from strategies.moving_average_strategy import MovingAverageStrategy
import argparse
from datetime import datetime, timedelta
import json

def run_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10000,
    fast_period: int = 20,
    slow_period: int = 50,
    use_trend_filter: bool = False,
    trend_period: int = 200,
    timeframe: str = '1h'
) -> dict:
    """
    Run a backtest with the specified parameters
    
    Args:
        symbol: Trading pair to backtest
        start_date: Start date for backtest
        end_date: End date for backtest
        initial_capital: Initial capital for backtest
        fast_period: Fast moving average period
        slow_period: Slow moving average period
        use_trend_filter: Whether to use trend filter
        trend_period: Period for trend moving average
        timeframe: Timeframe for the data
    
    Returns:
        Dictionary with backtest results
    """
    # Initialize components
    loader = HistoricalDataLoader(timeframe=timeframe)
    tester = StrategyTester(initial_capital=initial_capital)
    analyzer = PerformanceAnalyzer(initial_capital=initial_capital)
    visualizer = BacktestVisualizer()
    
    # Initialize strategy
    strategy = MovingAverageStrategy(
        fast_period=fast_period,
        slow_period=slow_period,
        params={
            'use_trend_filter': use_trend_filter,
            'trend_period': trend_period
        }
    )
    
    # Load and prepare data
    print(f"Loading data for {symbol}...")
    data = loader.prepare_backtest_data(
        symbol,
        start_date,
        end_date,
        include_indicators=True
    )
    
    if data.empty:
        raise ValueError("No data loaded for the specified period")
    
    # Run backtest
    print("Running backtest...")
    trades = tester.backtest_strategy(
        data,
        strategy.generate_signals,
        strategy.strategy_name
    )
    
    if not trades:
        print("No trades generated during the backtest period")
        return {}
    
    # Analyze results
    print("Analyzing performance...")
    equity_curve = analyzer.create_equity_curve(trades)
    metrics = analyzer.calculate_metrics(trades, equity_curve)
    trade_analysis = analyzer.generate_trade_analysis(trades)
    
    # Create visualizations
    print("Generating plots...")
    price_chart = visualizer.plot_backtest_results(
        data,
        trades,
        indicators={
            f'SMA{fast_period}': data[f'sma_{fast_period}'],
            f'SMA{slow_period}': data[f'sma_{slow_period}']
        }
    )
    equity_chart = visualizer.plot_equity_curve(equity_curve, metrics)
    returns_chart = visualizer.plot_monthly_returns(equity_curve)
    
    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"{symbol.replace('/', '_')}_{strategy.strategy_name}_{timestamp}"
    
    # Save plots
    price_chart.write_html(os.path.join(results_dir, f"{base_filename}_price.html"))
    equity_chart.write_html(os.path.join(results_dir, f"{base_filename}_equity.html"))
    returns_chart.write_html(os.path.join(results_dir, f"{base_filename}_returns.html"))
    
    # Save trade analysis
    trade_analysis.to_csv(os.path.join(results_dir, f"{base_filename}_trades.csv"))
    
    # Save metrics
    with open(os.path.join(results_dir, f"{base_filename}_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=4)
    
    print(f"\nBacktest Results for {strategy.strategy_name}:")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2%}")
    print(f"Net Profit: ${metrics['net_profit']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    print(f"\nResults saved in: {results_dir}")
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description='Run trading strategy backtest')
    
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                      help='Trading pair symbol (default: BTC/USDT)')
    parser.add_argument('--start', type=str, default='2023-01-01',
                      help='Start date (default: 2023-01-01)')
    parser.add_argument('--end', type=str, default=None,
                      help='End date (default: today)')
    parser.add_argument('--capital', type=float, default=10000,
                      help='Initial capital (default: 10000)')
    parser.add_argument('--fast', type=int, default=20,
                      help='Fast MA period (default: 20)')
    parser.add_argument('--slow', type=int, default=50,
                      help='Slow MA period (default: 50)')
    parser.add_argument('--trend', action='store_true',
                      help='Use trend filter')
    parser.add_argument('--trend-period', type=int, default=200,
                      help='Trend MA period (default: 200)')
    parser.add_argument('--timeframe', type=str, default='1h',
                      help='Data timeframe (default: 1h)')
    
    args = parser.parse_args()
    
    if args.end is None:
        args.end = datetime.now().strftime('%Y-%m-%d')
    
    try:
        run_backtest(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            fast_period=args.fast,
            slow_period=args.slow,
            use_trend_filter=args.trend,
            trend_period=args.trend_period,
            timeframe=args.timeframe
        )
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()