import pandas as pd
from typing import Dict, Any, List

class MovingAverageStrategy:
    """
    Enhanced Moving Average Crossover Strategy with EMA and ATR
    
    Features:
    - Uses EMA for faster signal generation
    - ATR-based dynamic stop-loss and take-profit
    - EMA-200 trend filter
    - Optimized for shorter timeframes
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        params: Dict[str, Any] = None
    ):
        """
        Initialize strategy parameters
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.params = params or {}
        self.sl_multiplier = self.params.get('sl_atr_multiplier', 2.0)
        self.tp_multiplier = self.params.get('tp_atr_multiplier', 4.0)
        self.use_trend_filter = self.params.get('use_trend_filter', True)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals with dynamic stop-loss and take-profit levels
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        
        # Get indicator values
        fast_ema = data[f'ema_{self.fast_period}']
        slow_ema = data[f'ema_{self.slow_period}']
        atr = data['atr']
        
        # Generate crossover signals
        previous_fast = fast_ema.shift(1)
        previous_slow = slow_ema.shift(1)
        
        # Detect crossovers
        bullish_cross = (previous_fast <= previous_slow) & (fast_ema > slow_ema)
        bearish_cross = (previous_fast >= previous_slow) & (fast_ema < slow_ema)
        
        # Apply trend filter if enabled
        if self.use_trend_filter:
            trend_ema = data['ema_200']
            # Counter-trend scalping on shorter timeframes
            price_above_trend = data['close'] > trend_ema
            # Reverse signals based on trend
            signals.loc[bullish_cross & ~price_above_trend, 'signal'] = 1  # Long when price below trend
            signals.loc[bearish_cross & price_above_trend, 'signal'] = -1  # Short when price above trend
        else:
            signals.loc[bullish_cross, 'signal'] = 1
            signals.loc[bearish_cross, 'signal'] = -1
        
        # Calculate stop-loss and take-profit levels
        signals['stop_loss'] = 0.0
        signals['take_profit'] = 0.0
        
        # Long position risk levels
        long_mask = signals['signal'] == 1
        signals.loc[long_mask, 'stop_loss'] = data.loc[long_mask, 'close'] - (atr[long_mask] * self.sl_multiplier)
        signals.loc[long_mask, 'take_profit'] = data.loc[long_mask, 'close'] + (atr[long_mask] * self.tp_multiplier)
        
        # Short position risk levels
        short_mask = signals['signal'] == -1
        signals.loc[short_mask, 'stop_loss'] = data.loc[short_mask, 'close'] + (atr[short_mask] * self.sl_multiplier)
        signals.loc[short_mask, 'take_profit'] = data.loc[short_mask, 'close'] - (atr[short_mask] * self.tp_multiplier)
        
        return signals
    
    @property
    def required_indicators(self) -> List[str]:
        """List of required indicators for the strategy"""
        indicators = [
            f'ema_{self.fast_period}',
            f'ema_{self.slow_period}',
            'atr'
        ]
        if self.use_trend_filter:
            indicators.append('ema_200')
        return indicators
    
    @property
    def strategy_name(self) -> str:
        """Get the strategy name"""
        return f"MA_{self.fast_period}_{self.slow_period}"