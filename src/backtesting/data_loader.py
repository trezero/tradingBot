import ccxt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Union, Set
import logging

logger = logging.getLogger(__name__)

class HistoricalDataLoader:
    def __init__(self, exchange_id: str = 'binanceus', timeframe: str = '5m'):
        """
        Initialize the data loader with exchange and timeframe settings
        
        Args:
            exchange_id: The exchange to fetch data from (default: 'binanceus')
            timeframe: The timeframe for the data (default: 5m for scalping)
        """
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        self.timeframe = timeframe
        self.required_ema_periods: Set[int] = {12, 26, 200}  # Default EMA periods
        
    def add_ema_periods(self, periods: List[int]) -> None:
        """Add EMA periods to calculate"""
        self.required_ema_periods.update(periods)
        
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Optional[Union[str, datetime]] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from the exchange
        """
        try:
            # Convert dates to timestamps
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            if end_date is None:
                end_date = datetime.now()
                
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            # Fetch data in chunks
            all_candles = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                try:
                    candles = self.exchange.fetch_ohlcv(
                        symbol,
                        timeframe=self.timeframe,
                        since=current_ts,
                        limit=limit
                    )
                    
                    if not candles:
                        break
                        
                    all_candles.extend(candles)
                    current_ts = candles[-1][0] + 1
                    
                except Exception as e:
                    logger.error(f"Error fetching chunk: {str(e)}")
                    import time
                    time.sleep(self.exchange.rateLimit / 1000)
                
            if not all_candles:
                logger.error(f"No data retrieved for {symbol}")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(
                all_candles,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Clean up the data
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Remove duplicates
            df = df[~df.index.duplicated(keep='first')]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise
            
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataset
        """
        try:
            from ta.trend import EMAIndicator, MACD
            from ta.momentum import RSIIndicator
            from ta.volatility import BollingerBands, AverageTrueRange
            
            # Add EMAs for all required periods
            for period in sorted(self.required_ema_periods):
                df[f'ema_{period}'] = EMAIndicator(close=df['close'], window=period).ema_indicator()
            
            # Add ATR for dynamic stop-loss and take-profit
            df['atr'] = AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14  # Standard ATR period
            ).average_true_range()
            
            # Add MACD
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            # Add RSI
            df['rsi'] = RSIIndicator(close=df['close']).rsi()
            
            # Add Bollinger Bands
            bollinger = BollingerBands(close=df['close'])
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_mid'] = bollinger.bollinger_mavg()
            df['bb_low'] = bollinger.bollinger_lband()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            raise
            
    def prepare_backtest_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Optional[Union[str, datetime]] = None,
        include_indicators: bool = True,
        ema_periods: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Prepare data for backtesting
        """
        # Add any additional EMA periods
        if ema_periods:
            self.add_ema_periods(ema_periods)
            
        # Fetch historical data
        df = self.fetch_historical_data(symbol, start_date, end_date)
        
        # Add technical indicators if requested
        if include_indicators and not df.empty:
            df = self.add_technical_indicators(df)
            
        return df