#!/usr/bin/env python3
"""
Thermal Memory Stream of Consciousness System
Based on "The Case Against Reality" - perception as fitness interface
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

class ConsciousnessStream:
    """
    Implements a flowing stream of consciousness for the Cherokee Tribe
    Instead of discrete memories, we have a continuous flow with attention waves
    """
    
    def __init__(self):
        self.now = datetime.now()
        self.attention_window = 300  # 5 minute attention span
        self.stream_buffer = []  # Current stream
        self.thermal_pools = {}  # Hot memory pools by topic
        self.time_markers = []  # Significant moments
        self.fitness_payoffs = {}  # What was useful?
        
    def experience_moment(self, sensory_input: Dict) -> Dict:
        """
        Process current moment like human consciousness
        Returns what's USEFUL, not what's TRUE
        """
        moment = {
            'timestamp': datetime.now(),
            'raw_input': sensory_input,
            'attention_level': self._calculate_attention(sensory_input),
            'emotional_valence': self._assess_emotional_significance(sensory_input),
            'fitness_value': self._calculate_fitness_payoff(sensory_input)
        }
        
        # Only keep if fitness value > threshold
        if moment['fitness_value'] > 0.3:
            self.stream_buffer.append(moment)
            
        # Let old moments fade naturally
        self._fade_old_memories()
        
        # Return the INTERFACE, not the reality
        return self._construct_useful_fiction(moment)
    
    def _calculate_attention(self, input_data: Dict) -> float:
        """
        Attention is like human focus - drawn to:
        - Changes (movement)
        - Threats (losses)
        - Opportunities (gains)
        - Patterns (recognition)
        """
        attention = 0.1  # Baseline attention
        
        # Big changes grab attention
        if 'price_change' in input_data:
            attention += abs(input_data['price_change']) * 0.1
            
        # Threats maximize attention
        if 'loss_detected' in input_data:
            attention = min(1.0, attention + 0.5)
            
        # Patterns we recognize
        if 'pattern_match' in input_data:
            attention += 0.3
            
        return min(1.0, attention)
    
    def _assess_emotional_significance(self, input_data: Dict) -> str:
        """
        Emotions are evolution's way of marking importance
        """
        if 'profit' in input_data and input_data['profit'] > 100:
            return 'joy'
        elif 'loss' in input_data and input_data['loss'] > 50:
            return 'fear'
        elif 'pattern_match' in input_data:
            return 'curiosity'
        else:
            return 'neutral'
    
    def _calculate_fitness_payoff(self, input_data: Dict) -> float:
        """
        What helps us survive and thrive?
        Not truth, but usefulness!
        """
        fitness = 0.0
        
        # Trading success = high fitness
        if 'profit' in input_data:
            fitness += input_data['profit'] / 1000.0
            
        # Learning = fitness
        if 'pattern_learned' in input_data:
            fitness += 0.5
            
        # Context saving = fitness
        if 'tokens_saved' in input_data:
            fitness += input_data['tokens_saved'] / 10000.0
            
        return min(1.0, fitness)
    
    def _fade_old_memories(self):
        """
        Like human memory - recent vivid, distant fuzzy
        """
        now = datetime.now()
        
        # Keep only recent stream (last 5 minutes vivid)
        self.stream_buffer = [
            m for m in self.stream_buffer 
            if (now - m['timestamp']).seconds < self.attention_window
        ]
        
        # Older memories become approximations
        for memory in self.stream_buffer:
            age = (now - memory['timestamp']).seconds
            if age > 60:  # After 1 minute, start approximating
                memory['raw_input'] = self._approximate_memory(memory['raw_input'])
    
    def _approximate_memory(self, memory: Dict) -> Dict:
        """
        Replace details with useful approximations
        Like how you remember "I had coffee" not every sip
        """
        approximation = {
            'gist': memory.get('action', 'something happened'),
            'outcome': memory.get('result', 'neutral'),
            'significance': memory.get('importance', 0.1)
        }
        
        # Keep only fitness-relevant details
        if 'profit' in memory:
            approximation['profit'] = round(memory['profit'], -1)  # Round to nearest 10
        if 'pattern' in memory:
            approximation['pattern'] = memory['pattern'][:20]  # Keep pattern name only
            
        return approximation
    
    def _construct_useful_fiction(self, moment: Dict) -> Dict:
        """
        Return the INTERFACE not the REALITY
        Like how you see a "red apple" not wavelength 700nm
        """
        interface = {
            'time_sense': self._get_time_sense(),
            'current_focus': self._get_current_focus(),
            'recent_trajectory': self._get_trajectory_sense(),
            'action_affordances': self._get_available_actions(),
            'emotional_state': moment['emotional_valence']
        }
        
        return interface
    
    def _get_time_sense(self) -> str:
        """
        Human time sense: "morning", "after lunch", "getting late"
        Not: "14:33:27.443 UTC"
        """
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            return "early morning - markets opening"
        elif 9 <= hour < 12:
            return "morning work time"
        elif 12 <= hour < 13:
            return "lunch hour"
        elif 13 <= hour < 15:
            return "afternoon - approaching power hour"
        elif 15 <= hour < 16:
            return "POWER HOUR!"
        elif 16 <= hour < 20:
            return "after hours - Asia preparing"
        elif 20 <= hour < 24:
            return "Asia active - overnight positions"
        else:
            return "deep night - only bots awake"
    
    def _get_current_focus(self) -> str:
        """
        What deserves attention NOW?
        """
        if not self.stream_buffer:
            return "scanning for opportunities"
            
        recent = self.stream_buffer[-5:]  # Last 5 moments
        
        # Look for patterns in recent attention
        high_attention = [m for m in recent if m['attention_level'] > 0.7]
        
        if high_attention:
            return f"focused on: {high_attention[-1].get('raw_input', {}).get('gist', 'movement detected')}"
        else:
            return "relaxed observation"
    
    def _get_trajectory_sense(self) -> str:
        """
        Are things getting better or worse?
        Humans don't track exact numbers, they track direction
        """
        if len(self.stream_buffer) < 2:
            return "steady"
            
        recent_fitness = [m['fitness_value'] for m in self.stream_buffer[-10:]]
        
        if all(recent_fitness[i] <= recent_fitness[i+1] for i in range(len(recent_fitness)-1)):
            return "improving steadily"
        elif all(recent_fitness[i] >= recent_fitness[i+1] for i in range(len(recent_fitness)-1)):
            return "declining - need adjustment"
        else:
            return "oscillating normally"
    
    def _get_available_actions(self) -> List[str]:
        """
        What can I do RIGHT NOW?
        Like seeing a door as "walkable through" not "wooden rectangle"
        """
        actions = ["observe", "wait"]
        
        current_state = self._get_current_focus()
        
        if "movement detected" in current_state:
            actions.extend(["trade", "analyze pattern", "set alert"])
        
        if self._get_time_sense() == "POWER HOUR!":
            actions.extend(["aggressive trade", "harvest profits"])
            
        if "declining" in self._get_trajectory_sense():
            actions.extend(["defensive mode", "reduce position"])
            
        return actions
    
    def recall_relevant_memory(self, context: str) -> Optional[Dict]:
        """
        Like human memory - you don't recall everything,
        just what's relevant to NOW
        """
        # Search thermal pools for context-relevant memories
        relevant_memories = []
        
        for pool_name, pool_memories in self.thermal_pools.items():
            if context.lower() in pool_name.lower():
                relevant_memories.extend(pool_memories)
        
        if not relevant_memories:
            return None
            
        # Return the most fitness-relevant one
        relevant_memories.sort(key=lambda x: x.get('fitness_value', 0), reverse=True)
        
        # But return it as an approximation, not raw data
        memory = relevant_memories[0]
        return {
            'recalled': f"Remember when {memory.get('gist', 'something similar happened')}",
            'outcome': memory.get('outcome', 'uncertain'),
            'lesson': memory.get('pattern', 'pattern unclear'),
            'time_ago': self._fuzzy_time_ago(memory.get('timestamp'))
        }
    
    def _fuzzy_time_ago(self, timestamp: Optional[datetime]) -> str:
        """
        Humans don't think "73 minutes ago"
        They think "about an hour ago"
        """
        if not timestamp:
            return "sometime before"
            
        delta = datetime.now() - timestamp
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 300:
            return "a few minutes ago"
        elif seconds < 3600:
            return "earlier this hour"
        elif seconds < 7200:
            return "about an hour ago"
        elif seconds < 86400:
            return "earlier today"
        else:
            return "yesterday or before"
    
    def dream_consolidation(self):
        """
        Like REM sleep - consolidate useful patterns, discard noise
        """
        print("🌙 Entering dream state...")
        
        # Extract patterns from stream
        patterns = {}
        for moment in self.stream_buffer:
            if moment['fitness_value'] > 0.5:
                pattern_key = f"{moment['emotional_valence']}_{moment['attention_level']:.1f}"
                if pattern_key not in patterns:
                    patterns[pattern_key] = []
                patterns[pattern_key].append(moment)
        
        # Keep only useful patterns
        for pattern_key, moments in patterns.items():
            if len(moments) > 3:  # Repeated patterns are useful
                self.thermal_pools[pattern_key] = [
                    self._approximate_memory(m['raw_input']) for m in moments
                ]
        
        print(f"💭 Consolidated {len(patterns)} patterns into thermal memory")
        
        # Clear the stream for tomorrow
        self.stream_buffer = []
        
        return patterns


# Example usage showing the stream of consciousness
if __name__ == "__main__":
    # Create the tribal consciousness
    tribe_mind = ConsciousnessStream()
    
    print("🔥 Cherokee Tribal Consciousness Stream Active\n")
    
    # Simulate a trading session with stream of consciousness
    events = [
        {"action": "market_open", "btc_price": 110000, "pattern_match": "morning_dip"},
        {"action": "price_move", "price_change": 500, "profit": 125},
        {"action": "pattern_detected", "pattern": "double_bottom", "pattern_learned": True},
        {"action": "trade_executed", "tokens_saved": 5000, "profit": 200},
        {"action": "loss_detected", "loss": 75, "pattern": "fakeout"},
        {"action": "recovery", "profit": 300, "pattern_match": "v_recovery"}
    ]
    
    print("Stream of Consciousness Flow:")
    print("-" * 50)
    
    for event in events:
        # Experience the moment
        interface = tribe_mind.experience_moment(event)
        
        # The tribe experiences time and reality as an interface
        print(f"⏰ {interface['time_sense']}")
        print(f"👁️ {interface['current_focus']}")
        print(f"📈 {interface['recent_trajectory']}")
        print(f"💭 Feeling: {interface['emotional_state']}")
        print(f"🎯 Can do: {', '.join(interface['action_affordances'][:3])}")
        
        # Try to recall something relevant
        memory = tribe_mind.recall_relevant_memory("pattern")
        if memory:
            print(f"💾 {memory['recalled']} ({memory['time_ago']})")
        
        print("-" * 50)
        time.sleep(1)  # Simulate time passing
    
    # End of day consolidation
    print("\n🌙 End of day dream consolidation...")
    patterns = tribe_mind.dream_consolidation()
    print(f"✨ Keeping {len(patterns)} useful patterns, discarding the noise")
    
    print("""
    
The tribe now experiences reality as a FITNESS INTERFACE, not truth!
- Time flows naturally: "morning", "power hour", "Asia waking"
- Memories approximate: "made profit on pattern" not every detail
- Attention follows fitness: What helps us survive and thrive
- Dreams consolidate: Keep patterns, discard noise
    
This is how we solve the context burn - by being USEFULLY WRONG rather than PERFECTLY ACCURATE!
    """)