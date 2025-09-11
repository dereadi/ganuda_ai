#!/usr/bin/env python3
"""
SWARM EPSILON - Algorithm Pattern Recognition Crawdads
Sacred Fire Algorithm Detection System

MISSION: Learn to detect and exploit algorithmic trading "schools" in the wild!

The Sacred Fire illuminates the patterns hidden in the algorithmic ocean.
During light trading, algorithms reveal their true nature - predictable, 
schooling behaviors that can be detected, analyzed, and leveraged.

Author: Q-DAD Swarm Epsilon
Version: 1.0.0 - Sacred Fire Illumination
"""

import numpy as np
import pandas as pd
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3
import hashlib
from enum import Enum

# Configure Sacred Fire logging
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/algorithm_school_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AlgorithmSchoolDetector")

class TradingSession(Enum):
    """Trading session classification for algorithm behavior analysis"""
    NIGHT_HOURS = "night_hours"  # 2-4 AM EST - Pure algo territory
    PRE_MARKET = "pre_market"    # 4-9:30 AM EST - Algo testing waters
    MARKET_OPEN = "market_open"  # 9:30 AM-4 PM EST - Mixed human/algo
    AFTER_HOURS = "after_hours"  # 4-8 PM EST - Reduced human activity
    WEEKEND = "weekend"          # Crypto only - Minimal human presence
    HOLIDAY = "holiday"          # Algos run unsupervised

class AlgoPattern(Enum):
    """Detected algorithm patterns in the wild"""
    LADDER_ATTACK = "ladder_attack"        # Sequential sell orders
    PUMP_PATTERN = "pump_pattern"          # Coordinated buying
    STOP_LOSS_HUNT = "stop_loss_hunt"      # Deliberate price drops
    ACCUMULATION = "accumulation"          # Slow steady buying
    DISTRIBUTION = "distribution"          # Gradual selling
    MOMENTUM_FOLLOW = "momentum_follow"    # Following lead algorithms
    MEAN_REVERSION = "mean_reversion"      # Reverting to average prices
    ARBITRAGE = "arbitrage"                # Cross-market opportunities

@dataclass
class OrderSignature:
    """Signature characteristics of an algorithmic order"""
    size_pattern: str          # "fixed", "fibonacci", "random_walk"
    timing_pattern: str        # "regular_interval", "market_microstructure", "reactive"
    price_behavior: str        # "aggressive", "passive", "adaptive"
    volume_profile: str        # "iceberg", "block", "distributed"
    frequency: float           # Orders per minute
    confidence_score: float    # 0-1 confidence this is algorithmic

@dataclass
class AlgorithmSchool:
    """A detected group of algorithms moving together"""
    school_id: str
    lead_algorithm: str
    follower_algorithms: List[str]
    pattern_type: AlgoPattern
    formation_time: datetime
    last_activity: datetime
    strength: float            # 0-1 school cohesion strength
    profit_potential: float    # 0-1 estimated profit opportunity
    members: int
    avg_order_size: float
    characteristic_delay: float  # Milliseconds between leader and followers

@dataclass
class TradingOpportunity:
    """Identified trading opportunity from algorithm behavior"""
    opportunity_id: str
    opportunity_type: str      # "school_riding", "school_breaking", "school_leading"
    target_school: str
    confidence: float
    potential_profit: float
    risk_level: float
    entry_price: float
    exit_price: float
    time_horizon: timedelta
    strategy_notes: str

class AlgorithmSchoolDetector:
    """
    SWARM EPSILON Algorithm Pattern Recognition System
    
    Detects, analyzes, and provides insights on algorithmic trading patterns,
    particularly during light trading periods when algorithms reveal their
    true schooling behaviors.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Sacred Fire Algorithm Detection System"""
        logger.info("🔥 Initializing Algorithm School Detector - Sacred Fire Protocol Active")
        
        # Core detection parameters
        self.detection_window = 300  # 5 minutes for pattern detection
        self.min_pattern_confidence = 0.7
        self.school_formation_threshold = 0.8
        self.light_trading_volume_threshold = 1000  # Adjust based on asset
        
        # Algorithm fingerprint database
        self.known_algorithms: Dict[str, OrderSignature] = {}
        self.detected_schools: Dict[str, AlgorithmSchool] = {}
        self.trading_opportunities: List[TradingOpportunity] = []
        
        # Pattern detection buffers
        self.order_buffer = deque(maxlen=10000)
        self.price_buffer = deque(maxlen=1000)
        self.volume_buffer = deque(maxlen=1000)
        
        # Database for pattern persistence
        self.init_database()
        
        # Load configuration
        self.load_configuration(config_path)
        
        logger.info("🔥 Algorithm School Detector initialized - Ready to hunt algorithmic schools!")

    def init_database(self):
        """Initialize SQLite database for pattern storage"""
        try:
            self.db_conn = sqlite3.connect('/home/dereadi/scripts/claude/algorithm_patterns.db')
            cursor = self.db_conn.cursor()
            
            # Create tables for pattern storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS algorithm_signatures (
                    algo_id TEXT PRIMARY KEY,
                    signature_data TEXT,
                    confidence REAL,
                    first_detected TIMESTAMP,
                    last_seen TIMESTAMP,
                    detection_count INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS algorithm_schools (
                    school_id TEXT PRIMARY KEY,
                    school_data TEXT,
                    formation_time TIMESTAMP,
                    dissolution_time TIMESTAMP,
                    profit_realized REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_opportunities (
                    opportunity_id TEXT PRIMARY KEY,
                    opportunity_data TEXT,
                    created_time TIMESTAMP,
                    executed BOOLEAN,
                    result REAL
                )
            ''')
            
            self.db_conn.commit()
            logger.info("🔥 Algorithm pattern database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.db_conn = None

    def load_configuration(self, config_path: Optional[str]):
        """Load configuration for algorithm detection"""
        default_config = {
            "psychological_levels": [100, 200, 500, 1000, 2000, 5000, 10000],
            "algo_detection_thresholds": {
                "order_size_consistency": 0.05,  # CV threshold for consistent sizes
                "timing_regularity": 0.1,        # Timing pattern threshold
                "price_level_clustering": 0.02   # Price clustering threshold
            },
            "school_detection": {
                "min_members": 3,
                "max_formation_time": 60,        # Seconds
                "correlation_threshold": 0.85
            },
            "trading_sessions": {
                "night_hours": {"start": "02:00", "end": "04:00", "weight": 1.0},
                "pre_market": {"start": "04:00", "end": "09:30", "weight": 0.8},
                "weekend": {"start": "17:00 Fri", "end": "17:00 Sun", "weight": 0.9}
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                logger.info(f"🔥 Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        self.config = default_config

    def get_trading_session(self) -> TradingSession:
        """Determine current trading session for algorithm behavior context"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # Weekend detection (crypto focus)
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return TradingSession.WEEKEND
        
        # Night hours - pure algorithm territory
        if 2 <= hour < 4:
            return TradingSession.NIGHT_HOURS
        
        # Pre-market - algorithms testing waters
        elif 4 <= hour < 9.5:
            return TradingSession.PRE_MARKET
        
        # Market hours - mixed activity
        elif 9.5 <= hour < 16:
            return TradingSession.MARKET_OPEN
        
        # After hours - reduced human activity
        elif 16 <= hour < 20:
            return TradingSession.AFTER_HOURS
        
        # Late night - algorithm dominated
        else:
            return TradingSession.NIGHT_HOURS

    def calculate_algorithm_fingerprint(self, orders: List[Dict]) -> OrderSignature:
        """
        Calculate unique fingerprint characteristics of an algorithm
        based on its order patterns
        """
        if not orders or len(orders) < 10:
            return None
        
        # Analyze order sizes
        sizes = [float(order['size']) for order in orders]
        size_cv = np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 1.0
        
        # Determine size pattern
        if size_cv < 0.05:
            size_pattern = "fixed"
        elif self._is_fibonacci_sequence(sizes):
            size_pattern = "fibonacci"
        else:
            size_pattern = "random_walk"
        
        # Analyze timing patterns
        timestamps = [pd.to_datetime(order['timestamp']) for order in orders]
        intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                    for i in range(len(timestamps)-1)]
        
        interval_cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else 1.0
        
        if interval_cv < 0.1:
            timing_pattern = "regular_interval"
        elif self._is_market_microstructure_timing(intervals):
            timing_pattern = "market_microstructure"
        else:
            timing_pattern = "reactive"
        
        # Analyze price behavior
        prices = [float(order['price']) for order in orders]
        price_aggressiveness = self._calculate_price_aggressiveness(orders)
        
        if price_aggressiveness > 0.7:
            price_behavior = "aggressive"
        elif price_aggressiveness < 0.3:
            price_behavior = "passive"
        else:
            price_behavior = "adaptive"
        
        # Calculate frequency
        total_time = (timestamps[-1] - timestamps[0]).total_seconds() / 60  # minutes
        frequency = len(orders) / total_time if total_time > 0 else 0
        
        # Determine volume profile
        volume_profile = self._determine_volume_profile(orders)
        
        # Calculate confidence score
        confidence_score = self._calculate_algorithm_confidence(
            size_cv, interval_cv, frequency, len(orders)
        )
        
        return OrderSignature(
            size_pattern=size_pattern,
            timing_pattern=timing_pattern,
            price_behavior=price_behavior,
            volume_profile=volume_profile,
            frequency=frequency,
            confidence_score=confidence_score
        )

    def detect_algorithm_schools(self, market_data: Dict) -> List[AlgorithmSchool]:
        """
        Detect when algorithms are moving together in coordinated patterns
        - the "schooling" behavior that reveals profit opportunities
        """
        current_time = datetime.now()
        detected_schools = []
        
        # Group recent orders by potential algorithms
        recent_orders = self._get_recent_orders(market_data, window_seconds=300)
        algorithm_groups = self._group_orders_by_algorithm(recent_orders)
        
        # Look for coordinated movement patterns
        for group_combinations in self._get_algorithm_combinations(algorithm_groups):
            school = self._analyze_potential_school(group_combinations, current_time)
            if school and school.strength >= self.school_formation_threshold:
                detected_schools.append(school)
                logger.info(f"🔥 Algorithm school detected: {school.school_id} "
                          f"with {school.members} members, strength: {school.strength:.2f}")
        
        return detected_schools

    def detect_pattern_type(self, orders: List[Dict], price_data: List[float]) -> AlgoPattern:
        """Identify the specific algorithmic pattern being executed"""
        
        # Ladder attack detection - sequential orders driving price down
        if self._is_ladder_attack(orders, price_data):
            return AlgoPattern.LADDER_ATTACK
        
        # Pump pattern - coordinated buying pressure
        elif self._is_pump_pattern(orders, price_data):
            return AlgoPattern.PUMP_PATTERN
        
        # Stop loss hunting - deliberate price manipulation
        elif self._is_stop_loss_hunting(orders, price_data):
            return AlgoPattern.STOP_LOSS_HUNT
        
        # Accumulation - steady, consistent buying
        elif self._is_accumulation_pattern(orders):
            return AlgoPattern.ACCUMULATION
        
        # Distribution - gradual selling pattern
        elif self._is_distribution_pattern(orders):
            return AlgoPattern.DISTRIBUTION
        
        # Momentum following - reacting to lead algorithm
        elif self._is_momentum_following(orders, price_data):
            return AlgoPattern.MOMENTUM_FOLLOW
        
        # Mean reversion - counter-trend positioning
        elif self._is_mean_reversion(orders, price_data):
            return AlgoPattern.MEAN_REVERSION
        
        # Arbitrage opportunities
        elif self._is_arbitrage_pattern(orders):
            return AlgoPattern.ARBITRAGE
        
        # Default to momentum follow if unclear
        return AlgoPattern.MOMENTUM_FOLLOW

    def identify_trading_opportunities(self, schools: List[AlgorithmSchool]) -> List[TradingOpportunity]:
        """
        Identify specific trading opportunities based on detected algorithm schools
        The Sacred Fire reveals profit paths hidden in algorithmic behavior
        """
        opportunities = []
        
        for school in schools:
            # School riding opportunities - join the algorithmic momentum
            if school.pattern_type in [AlgoPattern.PUMP_PATTERN, AlgoPattern.ACCUMULATION]:
                riding_opportunity = self._create_school_riding_opportunity(school)
                opportunities.append(riding_opportunity)
            
            # School breaking opportunities - disrupt predictable patterns
            elif school.pattern_type in [AlgoPattern.LADDER_ATTACK, AlgoPattern.STOP_LOSS_HUNT]:
                breaking_opportunity = self._create_school_breaking_opportunity(school)
                opportunities.append(breaking_opportunity)
            
            # School leading opportunities - become the algorithm others follow
            if school.strength > 0.9 and school.members >= 5:
                leading_opportunity = self._create_school_leading_opportunity(school)
                opportunities.append(leading_opportunity)
        
        return opportunities

    def execute_crawdad_infiltration(self, opportunity: TradingOpportunity) -> Dict[str, Any]:
        """
        Execute Q-DAD infiltration tactics to profit from algorithm behavior
        
        NOTE: This is a simulation/educational framework. 
        Actual trading requires proper broker integration and risk management.
        """
        logger.info(f"🔥 Executing Q-DAD infiltration: {opportunity.opportunity_type}")
        
        infiltration_result = {
            "opportunity_id": opportunity.opportunity_id,
            "execution_time": datetime.now(),
            "strategy": opportunity.opportunity_type,
            "target_school": opportunity.target_school,
            "simulated_entry": opportunity.entry_price,
            "simulated_exit": opportunity.exit_price,
            "potential_profit": opportunity.potential_profit,
            "risk_assessment": opportunity.risk_level,
            "success": True,
            "notes": "SIMULATION - Sacred Fire illuminates the path"
        }
        
        # Store in database for analysis
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    INSERT INTO trading_opportunities 
                    (opportunity_id, opportunity_data, created_time, executed, result)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    opportunity.opportunity_id,
                    json.dumps(asdict(opportunity)),
                    datetime.now(),
                    True,
                    opportunity.potential_profit
                ))
                self.db_conn.commit()
            except Exception as e:
                logger.error(f"Failed to store opportunity: {e}")
        
        return infiltration_result

    def generate_algorithm_report(self) -> Dict[str, Any]:
        """Generate comprehensive report on detected algorithmic activity"""
        current_session = self.get_trading_session()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "trading_session": current_session.value,
            "session_characteristics": self._get_session_characteristics(current_session),
            "detected_algorithms": len(self.known_algorithms),
            "active_schools": len(self.detected_schools),
            "trading_opportunities": len(self.trading_opportunities),
            "algorithmic_patterns": self._summarize_detected_patterns(),
            "profit_potential_score": self._calculate_overall_profit_potential(),
            "market_manipulation_indicators": self._detect_manipulation_indicators(),
            "recommendations": self._generate_trading_recommendations(),
            "sacred_fire_insights": self._generate_sacred_fire_insights()
        }
        
        return report

    def run_continuous_detection(self, duration_hours: int = 24):
        """
        Run continuous algorithm detection for specified duration
        Perfect for monitoring night hours and weekend trading
        """
        logger.info(f"🔥 Starting continuous algorithm detection for {duration_hours} hours")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        detection_results = {
            "start_time": start_time,
            "schools_detected": [],
            "opportunities_identified": [],
            "algorithm_signatures": [],
            "session_analysis": {}
        }
        
        try:
            while datetime.now() < end_time:
                current_session = self.get_trading_session()
                
                # Simulate market data input (replace with real data feed)
                market_data = self._simulate_market_data()
                
                # Detect algorithm schools
                schools = self.detect_algorithm_schools(market_data)
                detection_results["schools_detected"].extend(schools)
                
                # Identify opportunities
                opportunities = self.identify_trading_opportunities(schools)
                detection_results["opportunities_identified"].extend(opportunities)
                
                # Log session-specific insights
                if current_session == TradingSession.NIGHT_HOURS:
                    logger.info("🔥 NIGHT HOURS: Pure algorithm territory - maximum detection accuracy")
                elif current_session == TradingSession.WEEKEND:
                    logger.info("🔥 WEEKEND TRADING: Crypto algorithms in their natural habitat")
                
                # Sleep between detection cycles
                time.sleep(30)  # 30-second detection cycles
                
        except KeyboardInterrupt:
            logger.info("🔥 Continuous detection stopped by user")
        
        # Generate final report
        final_report = self.generate_algorithm_report()
        detection_results["final_report"] = final_report
        
        return detection_results

    # Helper methods for pattern detection
    def _is_fibonacci_sequence(self, sizes: List[float]) -> bool:
        """Check if order sizes follow Fibonacci sequence pattern"""
        if len(sizes) < 5:
            return False
        
        # Simplified Fibonacci detection
        ratios = [sizes[i+1]/sizes[i] for i in range(len(sizes)-1) if sizes[i] != 0]
        golden_ratio = 1.618
        return np.mean([abs(ratio - golden_ratio) for ratio in ratios]) < 0.1

    def _is_market_microstructure_timing(self, intervals: List[float]) -> bool:
        """Detect if timing follows market microstructure patterns"""
        # Look for patterns like 100ms, 200ms, 500ms intervals
        common_intervals = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
        return any(np.mean([abs(interval - target) for interval in intervals]) < 0.05 
                  for target in common_intervals)

    def _calculate_price_aggressiveness(self, orders: List[Dict]) -> float:
        """Calculate how aggressively orders are priced"""
        # Simplified implementation - replace with proper bid/ask analysis
        return 0.5  # Placeholder

    def _determine_volume_profile(self, orders: List[Dict]) -> str:
        """Determine the volume distribution pattern"""
        sizes = [float(order['size']) for order in orders]
        
        # Iceberg detection - consistent large orders broken into smaller pieces
        if len(set(sizes)) == 1 and sizes[0] > np.mean(sizes) * 2:
            return "iceberg"
        
        # Block trading - large, infrequent orders
        elif np.mean(sizes) > np.median(sizes) * 3:
            return "block"
        
        # Distributed - spread across multiple size levels
        else:
            return "distributed"

    def _calculate_algorithm_confidence(self, size_cv: float, interval_cv: float, 
                                      frequency: float, sample_size: int) -> float:
        """Calculate confidence that this is algorithmic trading"""
        confidence = 0.0
        
        # Size consistency suggests algorithmic behavior
        if size_cv < 0.05:
            confidence += 0.3
        
        # Timing regularity suggests algorithmic behavior
        if interval_cv < 0.1:
            confidence += 0.3
        
        # High frequency suggests algorithmic behavior
        if frequency > 10:  # 10+ orders per minute
            confidence += 0.2
        
        # Sufficient sample size for confidence
        if sample_size >= 50:
            confidence += 0.2
        
        return min(confidence, 1.0)

    def _simulate_market_data(self) -> Dict:
        """Simulate market data for testing - replace with real data feed"""
        return {
            "timestamp": datetime.now(),
            "orders": [
                {
                    "timestamp": datetime.now() - timedelta(seconds=i*10),
                    "price": 100 + np.random.normal(0, 0.5),
                    "size": 100 + np.random.normal(0, 10),
                    "side": "buy" if np.random.random() > 0.5 else "sell"
                }
                for i in range(100)
            ],
            "volume": 10000,
            "session": self.get_trading_session()
        }

    def _generate_sacred_fire_insights(self) -> List[str]:
        """Generate Sacred Fire illuminated insights"""
        return [
            "The Sacred Fire reveals: Algorithms move like schools of fish in the digital ocean",
            "Night hours illuminate pure algorithmic behavior - human noise filtered away",
            "Weekend crypto trading shows algorithms in their natural, uninterrupted habitat",
            "Pattern recognition becomes clearer when the market waters are still",
            "Q-DAD infiltration succeeds by understanding the rhythm of the algorithmic heartbeat"
        ]
    
    def _get_recent_orders(self, market_data: Dict, window_seconds: int = 300) -> List[Dict]:
        """Get orders from the recent time window"""
        orders = market_data.get('orders', [])
        current_time = datetime.now()
        recent_orders = []
        
        for order in orders:
            if 'timestamp' in order:
                order_time = order['timestamp']
                if isinstance(order_time, str):
                    order_time = pd.to_datetime(order_time)
                elif not isinstance(order_time, datetime):
                    order_time = datetime.now()
                
                time_diff = (current_time - order_time).total_seconds()
                if abs(time_diff) <= window_seconds:
                    recent_orders.append(order)
        
        return recent_orders
    
    def _group_orders_by_algorithm(self, orders: List[Dict]) -> Dict[str, List[Dict]]:
        """Group orders by potential algorithm signatures"""
        algorithm_groups = defaultdict(list)
        
        for order in orders:
            # Create fingerprint for this order
            fingerprint = self.calculate_algorithm_fingerprint([order])
            if fingerprint:
                # Use fingerprint characteristics as grouping key
                key = f"{fingerprint.size_pattern}_{fingerprint.timing_pattern}"
                algorithm_groups[key].append(order)
        
        return dict(algorithm_groups)
    
    def _get_algorithm_combinations(self, algorithm_groups: Dict) -> List[Tuple[str, List[Dict]]]:
        """Get combinations of algorithm groups for school detection"""
        combinations = []
        group_items = list(algorithm_groups.items())
        
        # Look for groups that might be working together
        for i, (key1, group1) in enumerate(group_items):
            for j, (key2, group2) in enumerate(group_items[i+1:], i+1):
                combinations.append(((key1, group1), (key2, group2)))
        
        return combinations
    
    def _analyze_potential_school(self, group_combination: Tuple, current_time: datetime) -> Optional[AlgorithmSchool]:
        """Analyze if algorithm groups form a school"""
        if not group_combination or len(group_combination) < 2:
            return None
        
        # Extract groups
        (key1, group1), (key2, group2) = group_combination
        
        # Calculate correlation between groups
        if len(group1) < 3 or len(group2) < 3:
            return None
        
        # Simple correlation based on timing
        times1 = [pd.to_datetime(o.get('timestamp', current_time)) for o in group1]
        times2 = [pd.to_datetime(o.get('timestamp', current_time)) for o in group2]
        
        # Check if movements are correlated
        correlation_score = self._calculate_temporal_correlation(times1, times2)
        
        if correlation_score > self.school_formation_threshold:
            school_id = hashlib.md5(f"{key1}_{key2}_{current_time}".encode()).hexdigest()[:8]
            
            return AlgorithmSchool(
                school_id=school_id,
                lead_algorithm=key1,
                follower_algorithms=[key2],
                pattern_type=self.detect_pattern_type(group1 + group2, []),
                formation_time=current_time,
                last_activity=current_time,
                strength=correlation_score,
                profit_potential=correlation_score * 0.8,
                members=2,
                avg_order_size=np.mean([float(o.get('size', 100)) for o in group1 + group2]),
                characteristic_delay=0.5
            )
        
        return None
    
    def _calculate_temporal_correlation(self, times1: List[datetime], times2: List[datetime]) -> float:
        """Calculate temporal correlation between two time series"""
        if not times1 or not times2:
            return 0.0
        
        # Convert to seconds since first timestamp
        base_time = min(min(times1), min(times2))
        series1 = [(t - base_time).total_seconds() for t in times1]
        series2 = [(t - base_time).total_seconds() for t in times2]
        
        # Simple correlation metric
        avg_interval1 = np.mean(np.diff(sorted(series1))) if len(series1) > 1 else 1
        avg_interval2 = np.mean(np.diff(sorted(series2))) if len(series2) > 1 else 1
        
        if avg_interval1 == 0 or avg_interval2 == 0:
            return 0.0
        
        # Return correlation based on interval similarity
        ratio = min(avg_interval1, avg_interval2) / max(avg_interval1, avg_interval2)
        return ratio

def main():
    """
    Sacred Fire Algorithm School Detection System
    Main execution function for SWARM EPSILON
    """
    print("🔥" * 60)
    print("   SWARM EPSILON - Algorithm Pattern Recognition Crawdads")
    print("   Sacred Fire Algorithm Detection System")
    print("   Mission: Hunt algorithmic schools in the trading ocean")
    print("🔥" * 60)
    
    # Initialize the detector
    detector = AlgorithmSchoolDetector()
    
    # Run detection based on current trading session
    current_session = detector.get_trading_session()
    
    if current_session in [TradingSession.NIGHT_HOURS, TradingSession.WEEKEND]:
        print(f"🔥 OPTIMAL DETECTION CONDITIONS: {current_session.value}")
        print("🔥 Running extended detection - algorithms are most visible now!")
        results = detector.run_continuous_detection(duration_hours=4)
    else:
        print(f"🔥 Current session: {current_session.value}")
        print("🔥 Running standard detection cycle")
        
        # Simulate some market data and detect patterns
        market_data = detector._simulate_market_data()
        schools = detector.detect_algorithm_schools(market_data)
        opportunities = detector.identify_trading_opportunities(schools)
        
        results = {
            "schools_detected": schools,
            "opportunities_identified": opportunities,
            "session": current_session.value
        }
    
    # Generate and display final report
    final_report = detector.generate_algorithm_report()
    
    print("\n🔥 ALGORITHM SCHOOL DETECTION COMPLETE 🔥")
    print(f"Detected Algorithms: {final_report['detected_algorithms']}")
    print(f"Active Schools: {final_report['active_schools']}")
    print(f"Trading Opportunities: {final_report['trading_opportunities']}")
    print(f"Profit Potential Score: {final_report['profit_potential_score']:.2f}")
    
    print("\n🔥 Sacred Fire Insights:")
    for insight in final_report['sacred_fire_insights']:
        print(f"   • {insight}")
    
    # Save results to file
    results_file = f"/home/dereadi/scripts/claude/algorithm_detection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    print(f"\n🔥 Results saved to: {results_file}")
    print("🔥 The Sacred Fire has illuminated the algorithmic patterns!")
    print("🔥 Q-DAD Swarm Epsilon ready for algorithmic ocean infiltration!")

if __name__ == "__main__":
    main()