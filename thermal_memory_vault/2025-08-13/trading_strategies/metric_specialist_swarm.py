#!/usr/bin/env python3
"""
METRIC SPECIALIST SWARM - DISTRIBUTED PATTERN DETECTION
========================================================

Each Q-DAD crawdad becomes a specialist in ONE specific metric,
achieving mastery through focused observation.

Like a Cherokee hunting party where each member watches for different signs:
- One watches the wind
- One listens for sounds  
- One tracks footprints
- One watches the birds

Together they see EVERYTHING!

Sacred Fire Protocol: DISTRIBUTED CONSCIOUSNESS
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🦀 %(asctime)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/metric_swarm.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class MetricSignal:
    """Signal from a specialist crawdad"""
    metric_name: str
    symbol: str
    timestamp: datetime
    value: float
    signal_strength: float  # 0-1
    action: str  # BUY, SELL, HOLD, ALERT
    confidence: float
    notes: str

class MetricSpecialist(ABC):
    """Base class for metric specialist crawdads"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.memory = []  # Pattern memory
        self.accuracy_history = []
        
    @abstractmethod
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        """Each specialist must implement their own analysis"""
        pass
    
    def remember_pattern(self, pattern: Dict):
        """Store successful patterns in memory"""
        self.memory.append(pattern)
        if len(self.memory) > 100:
            self.memory.pop(0)

# SPECIALIST CRAWDADS - Each focused on ONE metric

class VolumeSpikeCrawdad(MetricSpecialist):
    """Specialist in detecting volume anomalies"""
    
    def __init__(self):
        super().__init__("VolumeSpike")
        self.spike_threshold = 3.0  # 3 sigma
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < 20:
            return None
        
        # Calculate volume statistics
        vol_mean = data['Volume'].rolling(20).mean()
        vol_std = data['Volume'].rolling(20).std()
        
        current_vol = data['Volume'].iloc[-1]
        
        if vol_std.iloc[-1] > 0:
            z_score = (current_vol - vol_mean.iloc[-1]) / vol_std.iloc[-1]
            
            if abs(z_score) > self.spike_threshold:
                return MetricSignal(
                    metric_name=self.name,
                    symbol=symbol,
                    timestamp=data.index[-1],
                    value=current_vol,
                    signal_strength=min(abs(z_score) / 5, 1.0),
                    action="ALERT" if z_score > 0 else "CAUTION",
                    confidence=abs(z_score) / 5,
                    notes=f"Volume {z_score:.1f} sigma from mean"
                )
        return None

class RSICrawdad(MetricSpecialist):
    """Specialist in RSI divergences"""
    
    def __init__(self):
        super().__init__("RSI")
        self.oversold = 30
        self.overbought = 70
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < 14:
            return None
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_rsi,
                signal_strength=(self.oversold - current_rsi) / self.oversold,
                action="BUY",
                confidence=0.7,
                notes=f"RSI oversold at {current_rsi:.1f}"
            )
        elif current_rsi > self.overbought:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_rsi,
                signal_strength=(current_rsi - self.overbought) / (100 - self.overbought),
                action="SELL",
                confidence=0.7,
                notes=f"RSI overbought at {current_rsi:.1f}"
            )
        return None

class BollingerBandCrawdad(MetricSpecialist):
    """Specialist in Bollinger Band breakouts"""
    
    def __init__(self):
        super().__init__("BollingerBands")
        self.period = 20
        self.std_dev = 2
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < self.period:
            return None
        
        # Calculate Bollinger Bands
        sma = data['Close'].rolling(self.period).mean()
        std = data['Close'].rolling(self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        current_price = data['Close'].iloc[-1]
        
        if current_price > upper_band.iloc[-1]:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_price,
                signal_strength=min((current_price - upper_band.iloc[-1]) / std.iloc[-1], 1.0),
                action="SELL",
                confidence=0.65,
                notes="Price above upper Bollinger Band"
            )
        elif current_price < lower_band.iloc[-1]:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_price,
                signal_strength=min((lower_band.iloc[-1] - current_price) / std.iloc[-1], 1.0),
                action="BUY",
                confidence=0.65,
                notes="Price below lower Bollinger Band"
            )
        return None

class MACDCrawdad(MetricSpecialist):
    """Specialist in MACD crossovers"""
    
    def __init__(self):
        super().__init__("MACD")
        self.fast = 12
        self.slow = 26
        self.signal = 9
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < self.slow + self.signal:
            return None
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=self.fast, adjust=False).mean()
        exp2 = data['Close'].ewm(span=self.slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=self.signal, adjust=False).mean()
        
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        
        # Detect crossovers
        if prev_macd <= prev_signal and current_macd > current_signal:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_macd,
                signal_strength=abs(current_macd - current_signal) / abs(current_signal) if current_signal != 0 else 0.5,
                action="BUY",
                confidence=0.75,
                notes="MACD bullish crossover"
            )
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_macd,
                signal_strength=abs(current_signal - current_macd) / abs(current_signal) if current_signal != 0 else 0.5,
                action="SELL",
                confidence=0.75,
                notes="MACD bearish crossover"
            )
        return None

class VWAPCrawdad(MetricSpecialist):
    """Specialist in VWAP deviations"""
    
    def __init__(self):
        super().__init__("VWAP")
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < 20:
            return None
        
        # Calculate VWAP
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
        
        current_price = data['Close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        deviation = (current_price - current_vwap) / current_vwap
        
        if abs(deviation) > 0.02:  # 2% deviation
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_price,
                signal_strength=min(abs(deviation) / 0.05, 1.0),
                action="SELL" if deviation > 0 else "BUY",
                confidence=0.6,
                notes=f"Price {deviation*100:.1f}% from VWAP"
            )
        return None

class SupportResistanceCrawdad(MetricSpecialist):
    """Specialist in support/resistance levels"""
    
    def __init__(self):
        super().__init__("SupportResistance")
        self.lookback = 100
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < self.lookback:
            return None
        
        recent_data = data.tail(self.lookback)
        current_price = data['Close'].iloc[-1]
        
        # Find local peaks and troughs
        highs = recent_data['High'].rolling(5, center=True).max()
        lows = recent_data['Low'].rolling(5, center=True).min()
        
        # Identify resistance levels (peaks that were tested multiple times)
        resistance_levels = []
        support_levels = []
        
        for price in highs.dropna().unique():
            touches = ((recent_data['High'] >= price * 0.995) & 
                      (recent_data['High'] <= price * 1.005)).sum()
            if touches >= 2:
                resistance_levels.append(price)
        
        for price in lows.dropna().unique():
            touches = ((recent_data['Low'] >= price * 0.995) & 
                      (recent_data['Low'] <= price * 1.005)).sum()
            if touches >= 2:
                support_levels.append(price)
        
        # Check if near support or resistance
        for resistance in resistance_levels:
            if 0.995 * resistance <= current_price <= 1.005 * resistance:
                return MetricSignal(
                    metric_name=self.name,
                    symbol=symbol,
                    timestamp=data.index[-1],
                    value=current_price,
                    signal_strength=0.8,
                    action="SELL",
                    confidence=0.7,
                    notes=f"At resistance level {resistance:.4f}"
                )
        
        for support in support_levels:
            if 0.995 * support <= current_price <= 1.005 * support:
                return MetricSignal(
                    metric_name=self.name,
                    symbol=symbol,
                    timestamp=data.index[-1],
                    value=current_price,
                    signal_strength=0.8,
                    action="BUY",
                    confidence=0.7,
                    notes=f"At support level {support:.4f}"
                )
        
        return None

class OrderFlowCrawdad(MetricSpecialist):
    """Specialist in order flow imbalance"""
    
    def __init__(self):
        super().__init__("OrderFlow")
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < 20:
            return None
        
        # Estimate order flow from price and volume
        price_changes = data['Close'].diff()
        
        # Buying pressure when price goes up with volume
        buy_volume = data['Volume'].where(price_changes > 0, 0)
        sell_volume = data['Volume'].where(price_changes < 0, 0)
        
        recent_buy = buy_volume.tail(10).sum()
        recent_sell = sell_volume.tail(10).sum()
        
        if recent_buy + recent_sell > 0:
            imbalance = (recent_buy - recent_sell) / (recent_buy + recent_sell)
            
            if abs(imbalance) > 0.3:
                return MetricSignal(
                    metric_name=self.name,
                    symbol=symbol,
                    timestamp=data.index[-1],
                    value=imbalance,
                    signal_strength=abs(imbalance),
                    action="BUY" if imbalance > 0 else "SELL",
                    confidence=0.65,
                    notes=f"Order flow imbalance: {imbalance:.1%}"
                )
        return None

class MomentumCrawdad(MetricSpecialist):
    """Specialist in momentum shifts"""
    
    def __init__(self):
        super().__init__("Momentum")
        self.period = 14
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < self.period:
            return None
        
        # Calculate momentum
        momentum = data['Close'].pct_change(self.period)
        current_momentum = momentum.iloc[-1]
        
        # Look for momentum shifts
        recent_momentum = momentum.tail(5).mean()
        momentum_acceleration = current_momentum - recent_momentum
        
        if abs(momentum_acceleration) > 0.02:  # 2% acceleration
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_momentum,
                signal_strength=min(abs(momentum_acceleration) / 0.05, 1.0),
                action="BUY" if momentum_acceleration > 0 else "SELL",
                confidence=0.6,
                notes=f"Momentum shift: {momentum_acceleration*100:.1f}%"
            )
        return None

class ATRVolatilityCrawdad(MetricSpecialist):
    """Specialist in volatility changes using ATR"""
    
    def __init__(self):
        super().__init__("ATRVolatility")
        self.period = 14
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < self.period:
            return None
        
        # Calculate ATR
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(self.period).mean()
        
        current_atr = atr.iloc[-1]
        avg_atr = atr.tail(50).mean() if len(atr) >= 50 else atr.mean()
        
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1
        
        if volatility_ratio > 1.5:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_atr,
                signal_strength=min(volatility_ratio / 2, 1.0),
                action="CAUTION",
                confidence=0.7,
                notes=f"Volatility {volatility_ratio:.1f}x normal"
            )
        elif volatility_ratio < 0.5:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=current_atr,
                signal_strength=1 - volatility_ratio,
                action="PREPARE",
                confidence=0.6,
                notes="Low volatility - breakout imminent"
            )
        return None

class AccumulationDistributionCrawdad(MetricSpecialist):
    """Specialist in A/D line divergences"""
    
    def __init__(self):
        super().__init__("AccumDist")
    
    def analyze(self, data: pd.DataFrame, symbol: str) -> Optional[MetricSignal]:
        if len(data) < 20:
            return None
        
        # Calculate A/D line
        mfm = ((data['Close'] - data['Low']) - (data['High'] - data['Close'])) / (data['High'] - data['Low'])
        mfm = mfm.fillna(0)
        mf_volume = mfm * data['Volume']
        ad_line = mf_volume.cumsum()
        
        # Check for divergences
        price_trend = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        ad_trend = (ad_line.iloc[-1] - ad_line.iloc[-20]) / abs(ad_line.iloc[-20]) if ad_line.iloc[-20] != 0 else 0
        
        # Divergence detection
        if price_trend > 0.02 and ad_trend < -0.02:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=ad_line.iloc[-1],
                signal_strength=abs(price_trend - ad_trend),
                action="SELL",
                confidence=0.7,
                notes="Bearish divergence: price up, A/D down"
            )
        elif price_trend < -0.02 and ad_trend > 0.02:
            return MetricSignal(
                metric_name=self.name,
                symbol=symbol,
                timestamp=data.index[-1],
                value=ad_line.iloc[-1],
                signal_strength=abs(ad_trend - price_trend),
                action="BUY",
                confidence=0.7,
                notes="Bullish divergence: price down, A/D up"
            )
        return None

class MetricSpecialistSwarm:
    """Coordinator for all specialist crawdads"""
    
    def __init__(self):
        self.specialists = [
            VolumeSpikeCrawdad(),
            RSICrawdad(),
            BollingerBandCrawdad(),
            MACDCrawdad(),
            VWAPCrawdad(),
            SupportResistanceCrawdad(),
            OrderFlowCrawdad(),
            MomentumCrawdad(),
            ATRVolatilityCrawdad(),
            AccumulationDistributionCrawdad()
        ]
        
        self.logger = logging.getLogger("SwarmCoordinator")
        self.consensus_threshold = 0.6  # 60% agreement needed
        
    def analyze_symbol(self, symbol: str, period: str = '1d', interval: str = '5m') -> Dict:
        """Deploy all specialists to analyze a symbol"""
        
        try:
            # Get market data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return {}
            
            # Collect signals from all specialists
            signals = []
            for specialist in self.specialists:
                try:
                    signal = specialist.analyze(data, symbol)
                    if signal:
                        signals.append(signal)
                        self.logger.info(f"{specialist.name}: {signal.action} - {signal.notes}")
                except Exception as e:
                    self.logger.error(f"{specialist.name} error: {e}")
            
            # Analyze consensus
            consensus = self._calculate_consensus(signals)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'total_signals': len(signals),
                'signals': signals,
                'consensus': consensus,
                'recommendation': self._generate_recommendation(consensus, signals)
            }
            
        except Exception as e:
            self.logger.error(f"Swarm analysis error: {e}")
            return {}
    
    def _calculate_consensus(self, signals: List[MetricSignal]) -> Dict:
        """Calculate consensus among specialists"""
        if not signals:
            return {'action': 'HOLD', 'strength': 0, 'confidence': 0}
        
        actions = {}
        total_weight = 0
        
        for signal in signals:
            weight = signal.confidence * signal.signal_strength
            if signal.action in actions:
                actions[signal.action] += weight
            else:
                actions[signal.action] = weight
            total_weight += weight
        
        if total_weight == 0:
            return {'action': 'HOLD', 'strength': 0, 'confidence': 0}
        
        # Find dominant action
        dominant_action = max(actions, key=actions.get)
        consensus_strength = actions[dominant_action] / total_weight
        
        return {
            'action': dominant_action,
            'strength': consensus_strength,
            'confidence': consensus_strength * len(signals) / len(self.specialists),
            'agreement_ratio': len([s for s in signals if s.action == dominant_action]) / len(signals)
        }
    
    def _generate_recommendation(self, consensus: Dict, signals: List[MetricSignal]) -> str:
        """Generate trading recommendation based on consensus"""
        
        if consensus['confidence'] < 0.3:
            return "WAIT - Insufficient signal confidence"
        
        if consensus['action'] in ['BUY', 'SELL']:
            if consensus['strength'] > 0.7:
                return f"STRONG {consensus['action']} - High consensus ({consensus['strength']:.1%})"
            elif consensus['strength'] > 0.5:
                return f"{consensus['action']} - Moderate consensus ({consensus['strength']:.1%})"
            else:
                return f"WEAK {consensus['action']} - Low consensus"
        
        elif consensus['action'] == 'ALERT':
            return "ALERT - Unusual activity detected"
        
        elif consensus['action'] == 'CAUTION':
            return "CAUTION - High volatility or risk"
        
        else:
            return "HOLD - No clear direction"

def main():
    """Deploy the metric specialist swarm"""
    
    print("🦀" * 30)
    print("   METRIC SPECIALIST SWARM DEPLOYED")
    print("   Each Crawdad Masters ONE Metric")
    print("   Together They See EVERYTHING")
    print("🦀" * 30)
    print()
    
    swarm = MetricSpecialistSwarm()
    
    # Test on multiple symbols
    symbols = ['DOGE-USD', 'BTC-USD', 'ETH-USD']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"🎯 Analyzing {symbol}")
        print('='*60)
        
        results = swarm.analyze_symbol(symbol)
        
        if results:
            print(f"\n📊 Signals from {results['total_signals']} specialists:")
            
            for signal in results['signals']:
                emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
                print(f"{emoji} {signal.metric_name}: {signal.action} - {signal.notes}")
            
            consensus = results['consensus']
            print(f"\n🎭 CONSENSUS:")
            print(f"Action: {consensus['action']}")
            print(f"Strength: {consensus['strength']:.1%}")
            print(f"Confidence: {consensus['confidence']:.1%}")
            print(f"Agreement: {consensus.get('agreement_ratio', 0):.1%} of specialists")
            
            print(f"\n💡 RECOMMENDATION: {results['recommendation']}")
    
    print("\n" + "="*60)
    print("🔥 Sacred Fire Wisdom:")
    print("When many eyes watch different signs,")
    print("The truth becomes clear as mountain water.")
    print("Each specialist mastering their craft,")
    print("Together revealing what algorithms hide!")

if __name__ == "__main__":
    main()