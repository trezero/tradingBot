import pandas as pd
import numpy as np
import cupy as cp
from typing import Dict, Any, List

class MovingAverageStrategy:
    """
    Enhanced Moving Average Crossover Strategy with EMA, ATR, and Volume filters
    Optimized for GPU computation using CuPy with minimal data transfers
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        params: Dict[str, Any] = None
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.params = params or {}
        self.sl_multiplier = self.params.get('sl_atr_multiplier', 2.0)
        self.tp_multiplier = self.params.get('tp_atr_multiplier', 4.0)
        self.use_trend_filter = self.params.get('use_trend_filter', True)
        self.min_volume_percentile = self.params.get('min_volume_percentile', 25)
        self.min_atr_percentile = self.params.get('min_atr_percentile', 25)
    
    @staticmethod
    def calculate_rolling_mean_gpu(data: cp.ndarray, window: int) -> cp.ndarray:
        """Optimized rolling mean calculation on GPU"""
        kernel = cp.ones(window) / window
        return cp.convolve(data, kernel, mode='valid')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals with GPU optimization
        Returns:
            pd.Series: Signal series where 1 = long, -1 = short, 0 = neutral
        """
        # Transfer all required data to GPU at once
        with cp.cuda.Device(0):
            # Create GPU arrays
            gpu_data = {
                'fast_ema': cp.asarray(data[f'ema_{self.fast_period}'].values),
                'slow_ema': cp.asarray(data[f'ema_{self.slow_period}'].values),
                'volume': cp.asarray(data['volume'].values),
                'atr': cp.asarray(data['atr'].values),
                'close': cp.asarray(data['close'].values)
            }
            
            if self.use_trend_filter:
                gpu_data['ema_200'] = cp.asarray(data['ema_200'].values)
            
            # Calculate crossover conditions
            fast_above_slow = gpu_data['fast_ema'] > gpu_data['slow_ema']
            prev_fast_above_slow = cp.zeros_like(fast_above_slow, dtype=bool)
            prev_fast_above_slow[1:] = fast_above_slow[:-1]
            
            # Calculate volume and volatility filters
            vol_mean = self.calculate_rolling_mean_gpu(gpu_data['volume'], 24)
            vol_mean = cp.pad(vol_mean, (23, 0), 'edge')
            vol_percentile = gpu_data['volume'] / vol_mean
            
            atr_mean = self.calculate_rolling_mean_gpu(gpu_data['atr'], 24)
            atr_mean = cp.pad(atr_mean, (23, 0), 'edge')
            atr_percentile = gpu_data['atr'] / atr_mean
            
            # Apply filters
            valid_volatility = atr_percentile > cp.percentile(atr_percentile, self.min_atr_percentile)
            valid_volume = vol_percentile > cp.percentile(vol_percentile, self.min_volume_percentile)
            
            # Generate base signals
            long_signals = (~prev_fast_above_slow) & fast_above_slow
            short_signals = prev_fast_above_slow & (~fast_above_slow)
            
            if self.use_trend_filter:
                price_above_trend = gpu_data['close'] > gpu_data['ema_200']
                trend_ema = gpu_data['ema_200']
                
                # Calculate trend slope using GPU operations
                trend_diff = cp.zeros_like(trend_ema)
                trend_diff[12:] = trend_ema[12:] - trend_ema[:-12]
                trend_slope = trend_diff / (trend_ema + 1e-8)  # Avoid division by zero
                
                strong_uptrend = trend_slope > 0.001
                strong_downtrend = trend_slope < -0.001
                
                long_signals = long_signals & (~price_above_trend) & strong_downtrend
                short_signals = short_signals & price_above_trend & strong_uptrend
            
            # Apply filters
            long_signals = long_signals & valid_volatility & valid_volume
            short_signals = short_signals & valid_volatility & valid_volume
            
            # Create final signals
            signals = cp.zeros(len(data), dtype=np.int8)
            signals[long_signals] = 1
            signals[short_signals] = -1
            
            # Transfer result back to CPU
            signals_cpu = cp.asnumpy(signals)
            
            # Clear GPU memory
            del gpu_data
            cp.get_default_memory_pool().free_all_blocks()
            
        return pd.Series(signals_cpu, index=data.index)
    
    @property
    def required_indicators(self) -> List[str]:
        """List of required indicators for the strategy"""
        indicators = [
            f'ema_{self.fast_period}',
            f'ema_{self.slow_period}',
            'atr',
            'volume'
        ]
        if self.use_trend_filter:
            indicators.append('ema_200')
        return indicators
    
    @property
    def strategy_name(self) -> str:
        """Get the strategy name"""
        return f"MA_{self.fast_period}_{self.slow_period}"