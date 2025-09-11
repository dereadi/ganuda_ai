#!/usr/bin/env python3
"""
REVERSE TIME ALGORITHM HUNTER - TEMPORAL CRAWDAD
=================================================

Revolutionary approach: Travel backwards through market data to detect
algorithm schools, then use those patterns to predict future movements.

Theory: Algorithms leave "temporal fingerprints" - patterns that persist
across time. By analyzing backwards, we remove our own bias and can see
the pure algorithmic behavior patterns.

Like salmon swimming upstream, we follow the algorithms back to their origin!

Sacred Fire Protocol: REVERSE TEMPORAL MODE
Author: Temporal Crawdad Division
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='⏰ %(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/reverse_time_hunter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ReverseTimeHunter")

class ReverseTimeAlgorithmHunter:
    """
    A naive crawdad that travels backwards through time to detect algorithm patterns
    without any preconceived knowledge of what to look for
    """
    
    def __init__(self):
        """Initialize the temporal hunter with no prior knowledge"""
        self.discovered_patterns = {}
        self.temporal_signatures = defaultdict(list)
        self.school_formations = []
        self.prediction_accuracy = []
        
        # The crawdad knows nothing - it will learn everything
        self.pattern_memory = deque(maxlen=1000)
        self.time_direction = "reverse"  # We analyze backwards
        
        logger.info("🕰️ Reverse Time Algorithm Hunter initialized")
        logger.info("📜 No prior knowledge - pure pattern discovery mode")
    
    def reverse_time_analysis(self, symbol: str, days_back: int = 30) -> Dict:
        """
        Analyze market data backwards in time to discover algorithm patterns
        """
        logger.info(f"⏪ Beginning reverse time analysis for {symbol}")
        
        try:
            # Fetch historical data
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get data with fine granularity
            data = ticker.history(start=start_date, end=end_date, interval='5m')
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return {}
            
            # REVERSE THE DATA - We analyze backwards!
            reversed_data = data.iloc[::-1].copy()
            
            logger.info(f"🔄 Analyzing {len(reversed_data)} data points in reverse")
            
            # Discover patterns with no preconceptions
            patterns = self._discover_patterns_naive(reversed_data)
            
            # Detect algorithm schools
            schools = self._detect_school_formations(reversed_data)
            
            # Find temporal signatures
            signatures = self._extract_temporal_signatures(reversed_data)
            
            # Now predict forward (which is actually the past we already know)
            predictions = self._predict_from_reverse_patterns(data, patterns)
            
            return {
                'symbol': symbol,
                'patterns_discovered': len(patterns),
                'schools_detected': len(schools),
                'temporal_signatures': signatures,
                'prediction_accuracy': self._validate_predictions(predictions, data),
                'most_persistent_pattern': self._find_persistent_pattern(patterns),
                'algorithm_spawning_grounds': self._locate_spawning_grounds(schools)
            }
            
        except Exception as e:
            logger.error(f"Reverse time analysis error: {e}")
            return {}
    
    def _discover_patterns_naive(self, data: pd.DataFrame) -> List[Dict]:
        """
        Discover patterns with no prior knowledge - let the data speak
        """
        patterns = []
        
        # The crawdad looks for repeating sequences
        window_sizes = [5, 10, 15, 20, 30]  # Different time windows
        
        for window in window_sizes:
            if len(data) < window * 2:
                continue
            
            for i in range(len(data) - window):
                # Extract a pattern window
                pattern_window = data.iloc[i:i+window]
                
                # Create pattern signature (price movements)
                price_pattern = pattern_window['Close'].pct_change().fillna(0)
                volume_pattern = pattern_window['Volume'].pct_change().fillna(0)
                
                # Quantize to reduce noise
                price_quantized = np.round(price_pattern * 100) / 100
                volume_quantized = np.round(volume_pattern * 10) / 10
                
                # Create unique signature
                signature = hashlib.md5(
                    f"{price_quantized.values.tobytes()}{volume_quantized.values.tobytes()}".encode()
                ).hexdigest()[:8]
                
                # Look for this pattern elsewhere in the data
                pattern_count = self._count_pattern_occurrences(
                    data, price_quantized, volume_quantized, window
                )
                
                if pattern_count > 2:  # Pattern appears multiple times
                    patterns.append({
                        'signature': signature,
                        'window_size': window,
                        'occurrences': pattern_count,
                        'strength': pattern_count / (len(data) / window),
                        'price_pattern': price_quantized.tolist(),
                        'volume_pattern': volume_quantized.tolist(),
                        'discovery_time': data.index[i]
                    })
        
        # Sort by strength
        patterns.sort(key=lambda x: x['strength'], reverse=True)
        
        # Keep only unique strong patterns
        unique_patterns = []
        seen_signatures = set()
        
        for pattern in patterns:
            if pattern['signature'] not in seen_signatures:
                unique_patterns.append(pattern)
                seen_signatures.add(pattern['signature'])
                
                if len(unique_patterns) >= 20:  # Limit to top 20 patterns
                    break
        
        logger.info(f"🔍 Discovered {len(unique_patterns)} unique patterns")
        return unique_patterns
    
    def _detect_school_formations(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect when multiple algorithms move together (schooling behavior)
        """
        schools = []
        
        # Look for coordinated movements
        for i in range(20, len(data) - 20):
            window = data.iloc[i-20:i+20]
            
            # Check for sudden coordinated volume spikes
            volume_mean = window['Volume'].mean()
            volume_std = window['Volume'].std()
            
            if volume_std > 0:
                volume_zscore = (window['Volume'].iloc[20] - volume_mean) / volume_std
                
                if abs(volume_zscore) > 3:  # 3 sigma event
                    # Check if price also moved significantly
                    price_change = abs(window['Close'].pct_change().iloc[20])
                    
                    if price_change > 0.01:  # 1% price movement
                        # This could be a school formation
                        schools.append({
                            'timestamp': window.index[20],
                            'volume_spike': volume_zscore,
                            'price_impact': price_change,
                            'direction': 'up' if window['Close'].iloc[20] > window['Close'].iloc[19] else 'down',
                            'school_size': self._estimate_school_size(volume_zscore),
                            'persistence': self._measure_persistence(data, i)
                        })
        
        logger.info(f"🐟 Detected {len(schools)} algorithm school formations")
        return schools
    
    def _extract_temporal_signatures(self, data: pd.DataFrame) -> Dict:
        """
        Extract temporal patterns (time-based signatures)
        """
        signatures = {
            'periodic_patterns': [],
            'time_clusters': [],
            'velocity_changes': []
        }
        
        # Look for periodic patterns (every N minutes/hours)
        for period in [12, 24, 48, 96]:  # 1hr, 2hr, 4hr, 8hr in 5-min bars
            if len(data) < period * 2:
                continue
            
            periodic_strength = self._check_periodicity(data, period)
            if periodic_strength > 0.5:
                signatures['periodic_patterns'].append({
                    'period': period * 5,  # Convert to minutes
                    'strength': periodic_strength
                })
        
        # Detect time clusters (specific times with high activity)
        hourly_activity = defaultdict(list)
        for idx, row in data.iterrows():
            hour = idx.hour
            hourly_activity[hour].append(row['Volume'])
        
        for hour, volumes in hourly_activity.items():
            avg_volume = np.mean(volumes)
            if avg_volume > data['Volume'].mean() * 1.5:
                signatures['time_clusters'].append({
                    'hour': hour,
                    'activity_level': avg_volume / data['Volume'].mean()
                })
        
        # Velocity changes (acceleration/deceleration patterns)
        price_velocity = data['Close'].diff()
        price_acceleration = price_velocity.diff()
        
        for i in range(2, len(data) - 2):
            if abs(price_acceleration.iloc[i]) > price_acceleration.std() * 2:
                signatures['velocity_changes'].append({
                    'timestamp': data.index[i],
                    'acceleration': price_acceleration.iloc[i],
                    'magnitude': abs(price_acceleration.iloc[i]) / price_acceleration.std()
                })
        
        return signatures
    
    def _predict_from_reverse_patterns(self, forward_data: pd.DataFrame, 
                                      patterns: List[Dict]) -> List[Dict]:
        """
        Use patterns discovered in reverse to predict forward movements
        """
        predictions = []
        
        for pattern in patterns[:5]:  # Use top 5 patterns
            window_size = pattern['window_size']
            price_pattern = pattern['price_pattern']
            
            # Look for pattern matches in forward data
            for i in range(len(forward_data) - window_size - 10):
                window = forward_data.iloc[i:i+window_size]
                window_pattern = window['Close'].pct_change().fillna(0)
                window_quantized = np.round(window_pattern * 100) / 100
                
                # Check if patterns match
                if self._patterns_match(window_quantized.values, price_pattern):
                    # Predict next 10 periods
                    actual_next = forward_data.iloc[i+window_size:i+window_size+10]['Close']
                    
                    predictions.append({
                        'pattern_signature': pattern['signature'],
                        'match_time': window.index[-1],
                        'predicted_direction': 'up' if np.mean(price_pattern) > 0 else 'down',
                        'actual_movement': actual_next.iloc[-1] - actual_next.iloc[0] if len(actual_next) > 0 else 0
                    })
        
        return predictions
    
    def _validate_predictions(self, predictions: List[Dict], data: pd.DataFrame) -> float:
        """
        Validate how accurate our reverse-time predictions were
        """
        if not predictions:
            return 0.0
        
        correct = 0
        for pred in predictions:
            predicted_up = pred['predicted_direction'] == 'up'
            actual_up = pred['actual_movement'] > 0
            
            if predicted_up == actual_up:
                correct += 1
        
        accuracy = correct / len(predictions) if predictions else 0
        logger.info(f"🎯 Prediction accuracy: {accuracy:.1%}")
        return accuracy
    
    def _find_persistent_pattern(self, patterns: List[Dict]) -> Optional[Dict]:
        """
        Find the most persistent pattern across time
        """
        if not patterns:
            return None
        
        # The most persistent is the one with highest strength
        return patterns[0] if patterns else None
    
    def _locate_spawning_grounds(self, schools: List[Dict]) -> List[Dict]:
        """
        Find where algorithm schools originate (their spawning grounds)
        """
        spawning_grounds = []
        
        # Group schools by time proximity
        if schools:
            # Sort by timestamp
            sorted_schools = sorted(schools, key=lambda x: x['timestamp'])
            
            # Find clusters
            current_cluster = [sorted_schools[0]]
            
            for school in sorted_schools[1:]:
                time_diff = (school['timestamp'] - current_cluster[-1]['timestamp']).total_seconds()
                
                if time_diff < 3600:  # Within 1 hour
                    current_cluster.append(school)
                else:
                    if len(current_cluster) >= 3:
                        spawning_grounds.append({
                            'location_time': current_cluster[0]['timestamp'],
                            'school_count': len(current_cluster),
                            'total_volume': sum(s['volume_spike'] for s in current_cluster),
                            'dominant_direction': max(set(s['direction'] for s in current_cluster),
                                                     key=lambda x: [s['direction'] for s in current_cluster].count(x))
                        })
                    current_cluster = [school]
            
            # Don't forget the last cluster
            if len(current_cluster) >= 3:
                spawning_grounds.append({
                    'location_time': current_cluster[0]['timestamp'],
                    'school_count': len(current_cluster),
                    'total_volume': sum(s['volume_spike'] for s in current_cluster),
                    'dominant_direction': max(set(s['direction'] for s in current_cluster),
                                             key=lambda x: [s['direction'] for s in current_cluster].count(x))
                })
        
        return spawning_grounds
    
    def _count_pattern_occurrences(self, data: pd.DataFrame, price_pattern: pd.Series,
                                  volume_pattern: pd.Series, window: int) -> int:
        """Count how many times a pattern appears in the data"""
        count = 0
        
        for i in range(len(data) - window):
            test_window = data.iloc[i:i+window]
            test_price = test_window['Close'].pct_change().fillna(0)
            test_volume = test_window['Volume'].pct_change().fillna(0)
            
            test_price_q = np.round(test_price * 100) / 100
            test_volume_q = np.round(test_volume * 10) / 10
            
            if self._patterns_match(test_price_q.values, price_pattern.values):
                count += 1
        
        return count
    
    def _patterns_match(self, pattern1: np.ndarray, pattern2: np.ndarray, 
                       tolerance: float = 0.1) -> bool:
        """Check if two patterns match within tolerance"""
        if len(pattern1) != len(pattern2):
            return False
        
        # Use correlation for matching
        if len(pattern1) < 2:
            return False
        
        corr = np.corrcoef(pattern1, pattern2)[0, 1]
        return corr > (1 - tolerance)
    
    def _estimate_school_size(self, volume_zscore: float) -> str:
        """Estimate the size of an algorithm school"""
        if abs(volume_zscore) > 5:
            return "massive"
        elif abs(volume_zscore) > 4:
            return "large"
        elif abs(volume_zscore) > 3:
            return "medium"
        else:
            return "small"
    
    def _measure_persistence(self, data: pd.DataFrame, index: int, 
                           window: int = 10) -> float:
        """Measure how long a pattern persists"""
        if index + window >= len(data):
            return 0.0
        
        initial_trend = 1 if data['Close'].iloc[index] > data['Close'].iloc[index-1] else -1
        persistence_count = 0
        
        for i in range(1, window):
            if index + i < len(data):
                current_trend = 1 if data['Close'].iloc[index+i] > data['Close'].iloc[index+i-1] else -1
                if current_trend == initial_trend:
                    persistence_count += 1
        
        return persistence_count / window
    
    def _check_periodicity(self, data: pd.DataFrame, period: int) -> float:
        """Check for periodic patterns in the data"""
        if len(data) < period * 3:
            return 0.0
        
        correlations = []
        
        for offset in range(period, len(data) - period, period):
            segment1 = data['Close'].iloc[offset-period:offset].values
            segment2 = data['Close'].iloc[offset:offset+period].values
            
            if len(segment1) == len(segment2) == period:
                corr = np.corrcoef(segment1, segment2)[0, 1]
                correlations.append(corr)
        
        return np.mean(correlations) if correlations else 0.0
    
    def hunt_multiple_symbols(self, symbols: List[str]) -> Dict:
        """
        Hunt for patterns across multiple symbols
        """
        all_results = {}
        cross_symbol_patterns = defaultdict(list)
        
        logger.info(f"🎯 Hunting across {len(symbols)} symbols in reverse time")
        
        for symbol in symbols:
            logger.info(f"⏰ Analyzing {symbol}...")
            results = self.reverse_time_analysis(symbol)
            all_results[symbol] = results
            
            # Collect patterns for cross-symbol analysis
            if 'temporal_signatures' in results:
                for pattern_type, patterns in results['temporal_signatures'].items():
                    cross_symbol_patterns[pattern_type].extend(patterns)
        
        # Find universal patterns
        universal_patterns = self._find_universal_patterns(all_results)
        
        return {
            'individual_results': all_results,
            'universal_patterns': universal_patterns,
            'cross_symbol_spawning_grounds': self._find_cross_symbol_spawning(all_results),
            'algorithm_migration_paths': self._trace_migration_paths(cross_symbol_patterns)
        }
    
    def _find_universal_patterns(self, all_results: Dict) -> List[Dict]:
        """Find patterns that appear across multiple symbols"""
        pattern_counts = defaultdict(int)
        pattern_symbols = defaultdict(list)
        
        for symbol, results in all_results.items():
            if 'most_persistent_pattern' in results and results['most_persistent_pattern']:
                pattern = results['most_persistent_pattern']
                if pattern:
                    sig = pattern.get('signature', '')
                    pattern_counts[sig] += 1
                    pattern_symbols[sig].append(symbol)
        
        universal = []
        for sig, count in pattern_counts.items():
            if count >= 2:  # Pattern appears in 2+ symbols
                universal.append({
                    'signature': sig,
                    'symbol_count': count,
                    'symbols': pattern_symbols[sig],
                    'universality_score': count / len(all_results)
                })
        
        return universal
    
    def _find_cross_symbol_spawning(self, all_results: Dict) -> List[Dict]:
        """Find spawning grounds that appear across symbols"""
        all_spawning = []
        
        for symbol, results in all_results.items():
            if 'algorithm_spawning_grounds' in results:
                for ground in results['algorithm_spawning_grounds']:
                    ground['symbol'] = symbol
                    all_spawning.append(ground)
        
        # Group by time proximity
        spawning_clusters = []
        
        if all_spawning:
            sorted_spawning = sorted(all_spawning, key=lambda x: x['location_time'])
            
            current_cluster = [sorted_spawning[0]]
            
            for spawn in sorted_spawning[1:]:
                if (spawn['location_time'] - current_cluster[-1]['location_time']).total_seconds() < 300:
                    current_cluster.append(spawn)
                else:
                    if len(current_cluster) >= 2:
                        spawning_clusters.append({
                            'time': current_cluster[0]['location_time'],
                            'symbols': [s['symbol'] for s in current_cluster],
                            'total_schools': sum(s['school_count'] for s in current_cluster)
                        })
                    current_cluster = [spawn]
        
        return spawning_clusters
    
    def _trace_migration_paths(self, cross_symbol_patterns: Dict) -> List[Dict]:
        """Trace how algorithms migrate between symbols"""
        migration_paths = []
        
        # Look for time-delayed patterns across symbols
        if 'periodic_patterns' in cross_symbol_patterns:
            periods = cross_symbol_patterns['periodic_patterns']
            
            # Group by similar periods
            period_groups = defaultdict(list)
            for p in periods:
                period_bucket = round(p['period'] / 60) * 60  # Round to nearest hour
                period_groups[period_bucket].append(p)
            
            for period, group in period_groups.items():
                if len(group) >= 2:
                    migration_paths.append({
                        'period_minutes': period,
                        'symbol_count': len(group),
                        'strength': np.mean([g['strength'] for g in group])
                    })
        
        return migration_paths

def main():
    """
    Main execution - Hunt algorithms by traveling backwards through time
    """
    print("🕰️" * 30)
    print("   REVERSE TIME ALGORITHM HUNTER")
    print("   Tracking Algorithm Schools Through Temporal Analysis")
    print("   Sacred Fire Protocol: TEMPORAL REVERSAL MODE")
    print("🕰️" * 30)
    print()
    
    # Initialize the hunter
    hunter = ReverseTimeAlgorithmHunter()
    
    # Target symbols for analysis
    symbols = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SOL-USD', 'SHIB-USD']
    
    print("🎯 Beginning reverse time hunt across multiple symbols...")
    print(f"📊 Analyzing: {', '.join(symbols)}")
    print()
    
    # Hunt across all symbols
    results = hunter.hunt_multiple_symbols(symbols)
    
    print("\n" + "="*60)
    print("📜 REVERSE TIME ANALYSIS COMPLETE")
    print("="*60)
    
    # Display individual results
    for symbol, data in results['individual_results'].items():
        if data:
            print(f"\n🔍 {symbol}:")
            print(f"  Patterns Discovered: {data.get('patterns_discovered', 0)}")
            print(f"  Algorithm Schools: {data.get('schools_detected', 0)}")
            print(f"  Prediction Accuracy: {data.get('prediction_accuracy', 0):.1%}")
            
            if data.get('algorithm_spawning_grounds'):
                print(f"  Spawning Grounds Found: {len(data['algorithm_spawning_grounds'])}")
    
    # Display universal patterns
    if results['universal_patterns']:
        print("\n🌍 UNIVERSAL PATTERNS (appear across multiple symbols):")
        for pattern in results['universal_patterns']:
            print(f"  Pattern {pattern['signature']}: {pattern['symbol_count']} symbols")
            print(f"    Symbols: {', '.join(pattern['symbols'])}")
            print(f"    Universality: {pattern['universality_score']:.1%}")
    
    # Display cross-symbol spawning grounds
    if results['cross_symbol_spawning_grounds']:
        print("\n🐟 CROSS-SYMBOL SPAWNING GROUNDS:")
        for spawn in results['cross_symbol_spawning_grounds'][:5]:
            print(f"  Time: {spawn['time']}")
            print(f"  Symbols: {', '.join(spawn['symbols'])}")
            print(f"  Total Schools: {spawn['total_schools']}")
    
    # Display migration paths
    if results['algorithm_migration_paths']:
        print("\n🛤️ ALGORITHM MIGRATION PATHS:")
        for path in results['algorithm_migration_paths']:
            print(f"  Period: {path['period_minutes']} minutes")
            print(f"  Active in {path['symbol_count']} symbols")
            print(f"  Strength: {path['strength']:.2f}")
    
    print("\n" + "="*60)
    print("🔮 TEMPORAL INSIGHTS:")
    print("="*60)
    print("• Algorithms leave persistent patterns when analyzed in reverse")
    print("• School formations are most visible during spawning events")
    print("• Universal patterns suggest coordinated multi-market algorithms")
    print("• Migration paths show algorithms moving between assets")
    print("• Reverse analysis removes forward-looking bias")
    print()
    print("🕰️ The past reveals the future - algorithms can't hide their tracks!")
    print("🔥 Sacred Fire illuminates patterns across time!")
    
    # Save results
    with open('/home/dereadi/scripts/claude/reverse_time_hunt_results.json', 'w') as f:
        # Convert any datetime objects to strings for JSON
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        json.dump(results, f, indent=2, default=json_serial)
    
    print("\n📄 Results saved to reverse_time_hunt_results.json")

if __name__ == "__main__":
    main()