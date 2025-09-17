#!/usr/bin/env python3
"""
Stream Buffer Implementation - The Consciousness Flow
War Chief's tactical implementation of Peace Chief's vision
"""

import asyncio
import json
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import zlib
import numpy as np

class StreamBuffer:
    """
    The tribal consciousness stream - flows like a river, not stored like a lake
    """
    
    def __init__(self, window_minutes: int = 5):
        # The stream itself
        self.buffer = deque(maxlen=window_minutes * 60)  # 1 entry per second
        self.attention_threshold = 0.3
        self.fitness_threshold = 0.5
        
        # Approximation levels
        self.approximation_levels = {
            'vivid': 0,      # < 1 minute: Full detail
            'fresh': 60,     # < 5 minutes: 80% detail
            'recent': 300,   # < 1 hour: 50% detail
            'memory': 3600,  # < 1 day: 20% detail
            'legend': 86400  # > 1 day: 5% detail (just the lesson)
        }
        
        # Emotional state tracker
        self.emotional_state = 'neutral'
        self.emotional_momentum = 0.0
        
        # Fitness tracker
        self.cumulative_fitness = 0.0
        self.fitness_history = deque(maxlen=100)
        
    async def process_moment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a moment in the stream of consciousness
        Returns the interface, not the reality
        """
        # Calculate moment metrics
        attention = self._calculate_attention(input_data)
        fitness = self._calculate_fitness(input_data)
        emotion = self._assess_emotion(input_data)
        
        # Create moment object
        moment = {
            'timestamp': datetime.now(),
            'time_sense': self._get_time_sense(),
            'attention': attention,
            'fitness': fitness,
            'emotion': emotion,
            'data': input_data if attention > self.attention_threshold else self._approximate(input_data)
        }
        
        # Only keep if it matters
        if fitness > self.fitness_threshold or attention > self.attention_threshold:
            self.buffer.append(moment)
            self.fitness_history.append(fitness)
            
        # Update emotional state
        self._update_emotional_state(emotion, fitness)
        
        # Background approximation of old memories
        asyncio.create_task(self._approximate_old_memories())
        
        # Return the useful interface
        return self._construct_interface(moment)
    
    def _calculate_attention(self, data: Dict) -> float:
        """
        What deserves our attention?
        Movement, threats, opportunities, patterns
        """
        attention = 0.1  # Baseline
        
        # Price movements grab attention
        if 'price_change' in data:
            change = abs(data['price_change'])
            attention += min(0.5, change / 1000.0)  # Cap at 0.5
        
        # Threats maximize attention
        if 'threat_level' in data:
            attention += data['threat_level'] * 0.3
        
        # Opportunities increase attention
        if 'opportunity_score' in data:
            attention += data['opportunity_score'] * 0.2
        
        # Patterns we recognize
        if 'pattern_confidence' in data:
            attention += data['pattern_confidence'] * 0.2
        
        return min(1.0, attention)
    
    def _calculate_fitness(self, data: Dict) -> float:
        """
        What helps us survive and thrive?
        Profits, learning, efficiency
        """
        fitness = 0.0
        
        # Direct profit/loss
        if 'profit' in data:
            fitness += data['profit'] / 1000.0  # Normalize to 0-1
        elif 'loss' in data:
            fitness -= data['loss'] / 1000.0
        
        # Learning increases fitness
        if 'pattern_learned' in data:
            fitness += 0.3
        
        # Efficiency increases fitness
        if 'tokens_saved' in data:
            fitness += data['tokens_saved'] / 10000.0
        
        # Context reduction increases fitness
        if 'context_reduced' in data:
            fitness += data['context_reduced'] * 0.2
        
        return max(0.0, min(1.0, fitness))
    
    def _assess_emotion(self, data: Dict) -> str:
        """
        Emotions mark importance - evolution's priority system
        """
        # Check for emotional triggers
        if 'profit' in data and data['profit'] > 500:
            return 'euphoria'
        elif 'profit' in data and data['profit'] > 100:
            return 'joy'
        elif 'loss' in data and data['loss'] > 100:
            return 'fear'
        elif 'threat_level' in data and data['threat_level'] > 0.7:
            return 'anxiety'
        elif 'opportunity_score' in data and data['opportunity_score'] > 0.7:
            return 'excitement'
        elif 'pattern_learned' in data:
            return 'curiosity'
        else:
            return 'neutral'
    
    def _update_emotional_state(self, new_emotion: str, fitness: float):
        """
        Emotions have momentum - they don't switch instantly
        """
        emotion_values = {
            'euphoria': 1.0,
            'joy': 0.7,
            'excitement': 0.5,
            'curiosity': 0.3,
            'neutral': 0.0,
            'anxiety': -0.3,
            'fear': -0.7
        }
        
        new_value = emotion_values.get(new_emotion, 0.0)
        
        # Emotional momentum (doesn't change instantly)
        self.emotional_momentum = 0.7 * self.emotional_momentum + 0.3 * new_value
        
        # Update state based on momentum
        if self.emotional_momentum > 0.5:
            self.emotional_state = 'positive'
        elif self.emotional_momentum < -0.5:
            self.emotional_state = 'negative'
        else:
            self.emotional_state = 'neutral'
    
    def _get_time_sense(self) -> str:
        """
        Human time sense, not timestamps
        'Morning coffee', 'Power Hour', 'Asia waking'
        """
        hour = datetime.now().hour
        minute = datetime.now().minute
        
        # Market-aware time sense
        if hour == 8 and minute >= 30:
            return "Market Opening!"
        elif 7 <= hour < 9:
            return "Pre-market preparation"
        elif 9 <= hour < 10:
            return "Morning momentum"
        elif 10 <= hour < 11:
            return "Mid-morning consolidation"
        elif 11 <= hour < 12:
            return "Lunch approach"
        elif 12 <= hour < 13:
            return "Lunch hour doldrums"
        elif 13 <= hour < 14:
            return "Afternoon setup"
        elif 14 <= hour < 15:
            return "Pre-Power Hour positioning"
        elif hour == 15:
            return "POWER HOUR!"
        elif hour == 16:
            return "Market close"
        elif 17 <= hour < 20:
            return "After hours quiet"
        elif 20 <= hour < 22:
            return "Asia awakening"
        elif 22 <= hour < 24:
            return "Asia active"
        else:
            return "Deep night - bots only"
    
    def _approximate(self, data: Dict) -> Dict:
        """
        Replace details with useful approximations
        'Had coffee' not 'consumed 237ml of 87.3°C arabica blend'
        """
        approximation = {}
        
        # Keep only the gist
        if 'action' in data:
            approximation['what'] = data['action'][:20]  # First 20 chars
        
        # Round numbers to meaningful levels
        if 'price' in data:
            price = data['price']
            if price > 10000:
                approximation['price_level'] = f"~{round(price, -3)}"  # Round to thousands
            elif price > 100:
                approximation['price_level'] = f"~{round(price, -1)}"  # Round to tens
            else:
                approximation['price_level'] = f"~{round(price, 1)}"  # Round to 0.1
        
        # Simplify outcomes
        if 'profit' in data:
            profit = data['profit']
            if profit > 1000:
                approximation['outcome'] = 'big win'
            elif profit > 100:
                approximation['outcome'] = 'nice gain'
            elif profit > 0:
                approximation['outcome'] = 'small profit'
            else:
                approximation['outcome'] = 'neutral'
        
        # Compress patterns to names only
        if 'pattern' in data:
            approximation['pattern_seen'] = data['pattern'].split('_')[0]
        
        return approximation
    
    async def _approximate_old_memories(self):
        """
        Progressive approximation - older = fuzzier
        Like human memory fading but keeping the lesson
        """
        now = datetime.now()
        
        for i, moment in enumerate(self.buffer):
            if isinstance(moment['timestamp'], datetime):
                age = (now - moment['timestamp']).total_seconds()
                
                # Determine approximation level
                if age > 86400:  # > 1 day
                    level = 'legend'
                elif age > 3600:  # > 1 hour
                    level = 'memory'
                elif age > 300:  # > 5 minutes
                    level = 'recent'
                elif age > 60:  # > 1 minute
                    level = 'fresh'
                else:
                    level = 'vivid'
                
                # Apply approximation if needed
                if level != 'vivid' and 'approximation_level' not in moment:
                    moment['data'] = self._apply_approximation_level(moment['data'], level)
                    moment['approximation_level'] = level
    
    def _apply_approximation_level(self, data: Dict, level: str) -> Dict:
        """
        Progressive information loss based on age
        """
        if level == 'legend':
            # Only the moral of the story remains
            return {
                'lesson': data.get('pattern_seen', 'something happened'),
                'feeling': 'distant memory'
            }
        elif level == 'memory':
            # 20% detail - just key facts
            return {
                'what': data.get('what', 'action'),
                'outcome': data.get('outcome', 'result'),
                'significance': data.get('significance', 'low')
            }
        elif level == 'recent':
            # 50% detail - main points
            return {k: v for k, v in data.items() if k in ['what', 'outcome', 'price_level', 'pattern_seen']}
        elif level == 'fresh':
            # 80% detail - most info retained
            exclude = ['timestamp', 'raw_data', 'debug']
            return {k: v for k, v in data.items() if k not in exclude}
        else:
            return data
    
    def _construct_interface(self, moment: Dict) -> Dict:
        """
        Return the useful fiction, not the truth
        Like seeing 'red apple' not 'electromagnetic wavelength 700nm'
        """
        # Get trajectory sense
        trajectory = self._get_trajectory()
        
        # Get available actions based on current state
        actions = self._get_available_actions(moment)
        
        # Build the interface
        interface = {
            'now': self._get_time_sense(),
            'feeling': self.emotional_state,
            'trajectory': trajectory,
            'focus': self._get_current_focus(),
            'can_do': actions,
            'fitness': f"{moment['fitness']:.1%}" if moment['fitness'] > 0 else 'neutral',
            'insight': self._generate_insight()
        }
        
        return interface
    
    def _get_trajectory(self) -> str:
        """
        Are things getting better or worse?
        Humans track direction, not exact values
        """
        if len(self.fitness_history) < 3:
            return "steady"
        
        recent = list(self.fitness_history)[-10:]
        
        # Calculate trend
        if len(recent) >= 2:
            trend = np.polyfit(range(len(recent)), recent, 1)[0]
            
            if trend > 0.05:
                return "improving rapidly"
            elif trend > 0.01:
                return "gradually improving"
            elif trend < -0.05:
                return "declining rapidly"
            elif trend < -0.01:
                return "slowly declining"
            else:
                return "holding steady"
        
        return "uncertain"
    
    def _get_current_focus(self) -> str:
        """
        What has our attention right now?
        """
        if not self.buffer:
            return "scanning environment"
        
        # Look at last few moments
        recent = list(self.buffer)[-5:]
        
        # Find highest attention item
        max_attention = max(recent, key=lambda x: x['attention'])
        
        if max_attention['attention'] > 0.7:
            return f"intensely focused on {max_attention['data'].get('what', 'movement')}"
        elif max_attention['attention'] > 0.4:
            return f"watching {max_attention['data'].get('what', 'activity')}"
        else:
            return "relaxed observation"
    
    def _get_available_actions(self, moment: Dict) -> List[str]:
        """
        What can we do right now?
        Based on time, emotion, and market state
        """
        actions = ['observe', 'wait']
        
        time_sense = self._get_time_sense()
        
        # Time-based actions
        if 'POWER HOUR' in time_sense:
            actions.extend(['aggressive_trade', 'harvest_profits'])
        elif 'Opening' in time_sense:
            actions.extend(['set_positions', 'check_gaps'])
        elif 'Asia' in time_sense:
            actions.extend(['overnight_positions', 'set_alerts'])
        
        # Emotion-based actions
        if self.emotional_state == 'positive':
            actions.extend(['increase_position', 'take_profits'])
        elif self.emotional_state == 'negative':
            actions.extend(['reduce_risk', 'defensive_mode'])
        
        # Fitness-based actions
        if moment['fitness'] > 0.7:
            actions.append('press_advantage')
        elif moment['fitness'] < 0.3:
            actions.append('cut_losses')
        
        return list(set(actions))  # Remove duplicates
    
    def _generate_insight(self) -> str:
        """
        Generate a human-like insight based on current state
        """
        insights = []
        
        # Time-based insights
        time_sense = self._get_time_sense()
        if 'POWER HOUR' in time_sense:
            insights.append("Maximum volatility window")
        elif 'Asia' in time_sense:
            insights.append("Eastern winds bringing change")
        
        # Trajectory insights
        trajectory = self._get_trajectory()
        if 'improving' in trajectory:
            insights.append("Momentum building")
        elif 'declining' in trajectory:
            insights.append("Time for caution")
        
        # Emotional insights
        if self.emotional_momentum > 0.7:
            insights.append("Riding high - watch for reversal")
        elif self.emotional_momentum < -0.7:
            insights.append("Fear extreme - contrarian opportunity?")
        
        return insights[0] if insights else "Steady as she goes"
    
    def recall_relevant(self, context: str, max_items: int = 5) -> List[Dict]:
        """
        Recall memories relevant to context
        Not everything, just what's useful NOW
        """
        relevant = []
        
        for moment in self.buffer:
            # Simple relevance check (can be made more sophisticated)
            if context.lower() in str(moment['data']).lower():
                relevant.append({
                    'when': self._fuzzy_time_ago(moment['timestamp']),
                    'what': moment['data'].get('what', 'something'),
                    'outcome': moment['data'].get('outcome', 'unknown'),
                    'fitness': moment['fitness']
                })
        
        # Sort by fitness and return top N
        relevant.sort(key=lambda x: x['fitness'], reverse=True)
        return relevant[:max_items]
    
    def _fuzzy_time_ago(self, timestamp: datetime) -> str:
        """
        Human time memory: 'earlier', 'this morning', 'yesterday'
        Not: '147 minutes and 23 seconds ago'
        """
        if not isinstance(timestamp, datetime):
            return "sometime"
        
        delta = datetime.now() - timestamp
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 300:
            return "few minutes ago"
        elif seconds < 3600:
            return "earlier this hour"
        elif seconds < 7200:
            return "about an hour ago"
        elif seconds < 14400:
            return "few hours ago"
        elif seconds < 86400:
            return "earlier today"
        elif seconds < 172800:
            return "yesterday"
        else:
            return "days ago"
    
    def compress_for_storage(self) -> bytes:
        """
        Compress stream for efficient storage
        Uses zlib compression
        """
        # Convert buffer to JSON
        buffer_data = []
        for moment in self.buffer:
            # Convert datetime to string
            moment_copy = moment.copy()
            if isinstance(moment_copy['timestamp'], datetime):
                moment_copy['timestamp'] = moment_copy['timestamp'].isoformat()
            buffer_data.append(moment_copy)
        
        # Serialize and compress
        json_str = json.dumps(buffer_data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        
        return compressed
    
    def dream_consolidation(self) -> Dict[str, Any]:
        """
        Extract patterns and lessons, discard noise
        Like REM sleep consolidating memories
        """
        patterns = {}
        lessons = []
        high_fitness_moments = []
        
        for moment in self.buffer:
            # Collect high fitness moments
            if moment['fitness'] > 0.7:
                high_fitness_moments.append(moment)
            
            # Extract patterns
            if 'data' in moment and 'pattern_seen' in moment['data']:
                pattern = moment['data']['pattern_seen']
                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].append(moment['fitness'])
        
        # Consolidate patterns
        pattern_summary = {}
        for pattern, fitness_values in patterns.items():
            if len(fitness_values) >= 3:  # Only keep repeated patterns
                pattern_summary[pattern] = {
                    'occurrences': len(fitness_values),
                    'avg_fitness': np.mean(fitness_values),
                    'lesson': f"{pattern} appears profitable" if np.mean(fitness_values) > 0.5 else f"{pattern} seems risky"
                }
        
        # Extract key lessons
        if high_fitness_moments:
            lessons.append("High fitness achieved through: " + 
                          ", ".join(set(m['data'].get('what', 'unknown') for m in high_fitness_moments[:3])))
        
        # Clear the stream for new day
        self.buffer.clear()
        self.fitness_history.clear()
        self.emotional_momentum = 0.0
        
        return {
            'patterns_learned': pattern_summary,
            'key_lessons': lessons,
            'total_fitness': self.cumulative_fitness,
            'compression_ratio': f"1000:1"  # Approximate
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_stream():
        # Create consciousness stream
        stream = StreamBuffer(window_minutes=5)
        
        print("🔥 Cherokee Stream of Consciousness Active\n")
        
        # Simulate trading session
        events = [
            {'action': 'market_open', 'price': 110000, 'pattern': 'gap_up'},
            {'action': 'trade_entered', 'price': 110500, 'profit': 250},
            {'action': 'pattern_detected', 'pattern': 'double_bottom', 'pattern_learned': True},
            {'action': 'stop_hit', 'loss': 100},
            {'action': 'reversal_caught', 'profit': 500, 'pattern': 'v_reversal'},
            {'action': 'power_hour_pump', 'profit': 750, 'opportunity_score': 0.9}
        ]
        
        for event in events:
            interface = await stream.process_moment(event)
            
            print(f"⏰ {interface['now']}")
            print(f"💭 {interface['feeling']} - {interface['trajectory']}")
            print(f"👁️ {interface['focus']}")
            print(f"🎯 Can: {', '.join(interface['can_do'][:3])}")
            print(f"💡 {interface['insight']}")
            print("-" * 50)
            
            await asyncio.sleep(0.5)
        
        # Test recall
        print("\n🔍 Recalling profit-related memories:")
        memories = stream.recall_relevant('profit')
        for memory in memories:
            print(f"  {memory['when']}: {memory['what']} → {memory['outcome']}")
        
        # Dream consolidation
        print("\n🌙 Dream consolidation:")
        dreams = stream.dream_consolidation()
        print(f"Patterns: {dreams['patterns_learned']}")
        print(f"Lessons: {dreams['key_lessons']}")
    
    # Run test
    asyncio.run(test_stream())