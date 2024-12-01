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
import pandas as pd
import numpy as np

def run_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10000,
    fast_period: int = 12,
    slow_period: int = 26,
    use_trend_filter: bool = True,
    timeframe: str = '5m',
    sl_atr_multiplier: float = 2.0,
    tp_atr_multiplier: float = 4.0
) -> dict:
    """
    Run a backtest with the specified parameters
    """
    # Initialize components
    loader = HistoricalDataLoader(timeframe=timeframe)
    tester = StrategyTester(initial_capital=initial_capital)
    analyzer = PerformanceAnalyzer(initial_capital=initial_capital)
    visualizer = BacktestVisualizer()
    
    # Initialize strategy with ATR-based stops
    strategy = MovingAverageStrategy(
        fast_period=fast_period,
        slow_period=slow_period,
        params={
            'use_trend_filter': use_trend_filter,
            'sl_atr_multiplier': sl_atr_multiplier,
            'tp_atr_multiplier': tp_atr_multiplier
        }
    )
    
    # Add required EMA periods
    loader.add_ema_periods([fast_period, slow_period])
    if use_trend_filter:
        loader.add_ema_periods([200])  # Add EMA-200 for trend filter
    
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
    
    # Save results and generate plots...
    # [Previous save results code remains unchanged]
    
    return metrics

def optimize_parameters(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = '5m'
) -> None:
    """Run multiple backtests with different parameters to find optimal settings"""
    
    # Define parameter ranges to test
    fast_periods = [5, 8, 12, 15, 20]  # Shorter periods for scalping
    slow_periods = [15, 20, 26, 30, 40]  # Adjusted for shorter timeframe
    sl_multipliers = [1.5, 2.0, 2.5]  # ATR multipliers for stop-loss
    tp_multipliers = [3.0, 4.0, 5.0]  # ATR multipliers for take-profit
    
    # Create data loader and add all EMA periods upfront
    loader = HistoricalDataLoader(timeframe=timeframe)
    loader.add_ema_periods(fast_periods + slow_periods + [200])  # Include EMA-200
    
    # Load data once with all required indicators
    print(f"Loading data for {symbol}...")
    data = loader.prepare_backtest_data(symbol, start_date, end_date)
    
    if data.empty:
        raise ValueError("No data loaded for the specified period")
    
    results = []
    best_sharpe = -float('inf')
    best_params = None
    
    total_combinations = len(fast_periods) * len(slow_periods) * len(sl_multipliers) * len(tp_multipliers)
    current = 0
    
    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue
            
            for sl_mult in sl_multipliers:
                for tp_mult in tp_multipliers:
                    current += 1
                    print(f"\nTesting combination {current}/{total_combinations}")
                    print(f"Fast EMA: {fast}, Slow EMA: {slow}, SL: {sl_mult}x ATR, TP: {tp_mult}x ATR")
                    
                    try:
                        strategy = MovingAverageStrategy(
                            fast_period=fast,
                            slow_period=slow,
                            params={
                                'use_trend_filter': True,
                                'sl_atr_multiplier': sl_mult,
                                'tp_atr_multiplier': tp_mult
                            }
                        )
                        
                        tester = StrategyTester(initial_capital=10000)
                        analyzer = PerformanceAnalyzer(initial_capital=10000)
                        
                        trades = tester.backtest_strategy(
                            data,
                            strategy.generate_signals,
                            strategy.strategy_name
                        )
                        
                        if trades:
                            equity_curve = analyzer.create_equity_curve(trades)
                            metrics = analyzer.calculate_metrics(trades, equity_curve)
                            
                            results.append({
                                'fast_period': fast,
                                'slow_period': slow,
                                'sl_multiplier': sl_mult,
                                'tp_multiplier': tp_mult,
                                **metrics
                            })
                            
                            if metrics['sharpe_ratio'] > best_sharpe:
                                best_sharpe = metrics['sharpe_ratio']
                                best_params = (fast, slow, sl_mult, tp_mult)
                        
                    except Exception as e:
                        print(f"Error running backtest: {str(e)}")
                        continue
    
    if not results:
        print("No valid results found during optimization")
        return
    
    # Save optimization results
    results_df = pd.DataFrame(results)
    results_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'results')
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_df.to_csv(os.path.join(results_dir, f'optimization_results_{timestamp}.csv'), index=False)
    
    # Print optimization summary
    print("\nOptimization Results:")
    print(f"Best Parameters:")
    print(f"Fast EMA: {best_params[0]}")
    print(f"Slow EMA: {best_params[1]}")
    print(f"Stop-Loss ATR Multiplier: {best_params[2]}")
    print(f"Take-Profit ATR Multiplier: {best_params[3]}")
    print(f"Best Sharpe Ratio: {best_sharpe:.2f}")
    
    # Run final backtest with best parameters
    print("\nRunning final backtest with optimal parameters...")
    run_backtest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=timeframe,
        fast_period=best_params[0],
        slow_period=best_params[1],
        sl_atr_multiplier=best_params[2],
        tp_atr_multiplier=best_params[3]
    )

def main():
    parser = argparse.ArgumentParser(description='Run trading strategy backtest')
    
    parser.add_argument('--symbol', type=str, default='ETH/USD',
                      help='Trading pair symbol (default: ETH/USD)')
    parser.add_argument('--start', type=str, default='2023-01-01',
                      help='Start date (default: 2023-01-01)')
    parser.add_argument('--end', type=str, default=None,
                      help='End date (default: today)')
    parser.add_argument('--capital', type=float, default=10000,
                      help='Initial capital (default: 10000)')
    parser.add_argument('--fast', type=int, default=12,
                      help='Fast EMA period (default: 12)')
    parser.add_argument('--slow', type=int, default=26,
                      help='Slow EMA period (default: 26)')
    parser.add_argument('--timeframe', type=str, default='5m',
                      help='Data timeframe (default: 5m)')
    parser.add_argument('--sl-atr', type=float, default=2.0,
                      help='Stop-loss ATR multiplier (default: 2.0)')
    parser.add_argument('--tp-atr', type=float, default=4.0,
                      help='Take-profit ATR multiplier (default: 4.0)')
    parser.add_argument('--optimize', action='store_true',
                      help='Run parameter optimization')
    
    args = parser.parse_args()
    
    if args.end is None:
        args.end = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if args.optimize:
            optimize_parameters(
                symbol=args.symbol,
                start_date=args.start,
                end_date=args.end,
                timeframe=args.timeframe
            )
        else:
            run_backtest(
                symbol=args.symbol,
                start_date=args.start,
                end_date=args.end,
                initial_capital=args.capital,
                fast_period=args.fast,
                slow_period=args.slow,
                timeframe=args.timeframe,
                sl_atr_multiplier=args.sl_atr,
                tp_atr_multiplier=args.tp_atr
            )
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()