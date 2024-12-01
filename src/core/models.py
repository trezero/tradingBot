from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class OrderSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(enum.Enum):
    MARKET = "market"
    LIMIT = "limit"

class Strategy(Base):
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trades = relationship("Trade", back_populates="strategy")
    performance_metrics = relationship("StrategyPerformance", back_populates="strategy")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float)
    executed_price = Column(Float)
    status = Column(String(20))
    executed_at = Column(DateTime)
    closed_at = Column(DateTime)
    profit_loss = Column(Float)
    fees = Column(Float)
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="trades")

class StrategyPerformance(Base):
    __tablename__ = 'strategy_performance'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    date = Column(DateTime, nullable=False)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    profit_factor = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    total_profit_loss = Column(Float, default=0)
    win_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="performance_metrics")

class DailyBalance(Base):
    __tablename__ = 'daily_balances'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    exchange = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    balance = Column(Float, nullable=False)
    usd_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)