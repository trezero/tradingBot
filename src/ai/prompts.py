TRADE_SIGNAL_ANALYSIS = """
Analyze the following trading signal and provide insights:
Signal Details:
- Strategy: {strategy_name}
- Symbol: {symbol}
- Side: {side}
- Type: {order_type}
- Amount: {amount}
- Price: {price}

Previous Performance:
{performance_metrics}

Provide analysis covering:
1. Signal validity based on current market conditions
2. Risk assessment
3. Potential profit targets
4. Recommended adjustments to parameters
"""

STRATEGY_OPTIMIZATION = """
Review the following strategy performance metrics and suggest improvements:
Strategy: {strategy_name}

Performance Metrics:
- Total Trades: {total_trades}
- Win Rate: {win_rate}
- Profit Factor: {profit_factor}
- Max Drawdown: {max_drawdown}
- Sharpe Ratio: {sharpe_ratio}

Recent Trades:
{recent_trades}

Provide recommendations for:
1. Parameter optimization
2. Risk management adjustments
3. Entry/exit criteria improvements
4. Market condition adaptations
"""

DAILY_SUMMARY = """
Generate a comprehensive trading day summary:
Date: {date}

Performance Overview:
{daily_performance}

Strategy Analysis:
{strategy_metrics}

Notable Trades:
{notable_trades}

Provide:
1. Key performance insights
2. Strategy effectiveness analysis
3. Risk management assessment
4. Recommendations for next trading day
"""

BACKTESTING_ANALYSIS = """
Analyze the following backtesting results and provide optimization suggestions:
Strategy: {strategy_name}
Period: {start_date} to {end_date}

Performance Metrics:
{backtest_metrics}

Market Conditions:
{market_analysis}

Provide:
1. Strategy performance analysis
2. Market condition impact assessment
3. Parameter optimization recommendations
4. Risk management improvements
"""