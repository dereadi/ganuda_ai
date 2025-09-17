#!/usr/bin/env python3
"""
Action-Oriented Memory System
Based on Flying Squirrel's insight: We remember things AS WE ACT ON THEM
Memory isn't storage - it's preparation for action
"""

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

class ActionMemory:
    """
    Memory that exists TO ENABLE ACTION, not just to store information
    Like how you remember how to ride a bike IN YOUR BODY, not in words
    """
    
    def __init__(self):
        # Memories organized by ACTION AFFORDANCES, not chronology
        self.action_patterns = {
            'profitable_trades': [],
            'danger_escapes': [],
            'pattern_exploits': [],
            'timing_wisdom': [],
            'tool_uses': []
        }
        
        # Procedural memory - HOW to do things, not WHAT happened
        self.procedures = {}
        
        # Muscle memory - reactions without thinking
        self.reflexes = {}
        
    def remember_through_action(self, experience: Dict) -> Dict:
        """
        Store memory AS AN ACTION TEMPLATE, not as data
        Like remembering 'how to catch that profit' not 'what the numbers were'
        """
        # Extract the ACTION POTENTIAL from the experience
        action_template = {
            'trigger': self._extract_trigger(experience),
            'action': self._extract_action(experience),
            'outcome': self._extract_outcome(experience),
            'feeling': self._extract_feeling(experience),
            'reusable': self._assess_reusability(experience)
        }
        
        # Store in appropriate action category
        if action_template['outcome'] == 'profit':
            self.action_patterns['profitable_trades'].append(action_template)
        elif action_template['outcome'] == 'avoided_loss':
            self.action_patterns['danger_escapes'].append(action_template)
        
        # If highly reusable, create a reflex
        if action_template['reusable'] > 0.8:
            self._create_reflex(action_template)
        
        return action_template
    
    def recall_for_action(self, current_situation: Dict) -> Optional[Dict]:
        """
        Recall memory BASED ON WHAT WE CAN DO NOW
        Not 'what happened before' but 'what worked before'
        """
        # Find similar action triggers
        best_match = None
        best_score = 0
        
        for category, patterns in self.action_patterns.items():
            for pattern in patterns:
                similarity = self._situation_similarity(current_situation, pattern['trigger'])
                if similarity > best_score:
                    best_score = similarity
                    best_match = pattern
        
        if best_match and best_score > 0.5:
            return {
                'suggested_action': best_match['action'],
                'expected_outcome': best_match['outcome'],
                'confidence': best_score,
                'memory_type': 'action_pattern'
            }
        
        # Check reflexes for immediate action
        reflex = self._check_reflexes(current_situation)
        if reflex:
            return reflex
        
        return None
    
    def _extract_trigger(self, experience: Dict) -> Dict:
        """What situation triggers this action?"""
        return {
            'pattern': experience.get('pattern', 'unknown'),
            'context': experience.get('time_sense', 'anytime'),
            'preconditions': experience.get('preconditions', {})
        }
    
    def _extract_action(self, experience: Dict) -> str:
        """What action was taken?"""
        return experience.get('action', 'observe')
    
    def _extract_outcome(self, experience: Dict) -> str:
        """What happened when we acted?"""
        if experience.get('profit', 0) > 0:
            return 'profit'
        elif experience.get('loss_avoided', False):
            return 'avoided_loss'
        else:
            return 'neutral'
    
    def _extract_feeling(self, experience: Dict) -> str:
        """How did it FEEL? (Embodied memory)"""
        return experience.get('emotional_state', 'neutral')
    
    def _assess_reusability(self, experience: Dict) -> float:
        """Can we do this again in similar situations?"""
        if experience.get('pattern_confidence', 0) > 0.7:
            return 0.9
        elif experience.get('random_luck', False):
            return 0.1
        else:
            return 0.5
    
    def _create_reflex(self, action_template: Dict):
        """
        Create instant reaction - no thinking required
        Like pulling your hand from fire
        """
        trigger_key = json.dumps(action_template['trigger'], sort_keys=True)
        self.reflexes[trigger_key] = {
            'action': action_template['action'],
            'speed': 'instant',
            'bypass_analysis': True
        }
    
    def _situation_similarity(self, current: Dict, remembered: Dict) -> float:
        """
        How similar is now to then?
        But focusing on ACTION RELEVANCE, not data similarity
        """
        score = 0.0
        
        # Pattern match (most important for action)
        if current.get('pattern') == remembered.get('pattern'):
            score += 0.5
        
        # Context match (time/situation)
        if current.get('context') == remembered.get('context'):
            score += 0.3
        
        # Preconditions match
        current_pre = current.get('preconditions', {})
        remembered_pre = remembered.get('preconditions', {})
        if current_pre and remembered_pre:
            matching = sum(1 for k in current_pre if k in remembered_pre and current_pre[k] == remembered_pre[k])
            score += 0.2 * (matching / max(len(current_pre), len(remembered_pre)))
        
        return score
    
    def _check_reflexes(self, situation: Dict) -> Optional[Dict]:
        """
        Check if we have an instant reflex for this situation
        """
        trigger_key = json.dumps({
            'pattern': situation.get('pattern', 'unknown'),
            'context': situation.get('time_sense', 'anytime'),
            'preconditions': situation.get('preconditions', {})
        }, sort_keys=True)
        
        if trigger_key in self.reflexes:
            return {
                'suggested_action': self.reflexes[trigger_key]['action'],
                'expected_outcome': 'reflexive',
                'confidence': 1.0,
                'memory_type': 'reflex',
                'speed': 'instant'
            }
        
        return None
    
    def consolidate_into_wisdom(self) -> Dict:
        """
        Extract procedural wisdom from action patterns
        Not facts, but HOW-TO knowledge
        """
        wisdom = {}
        
        # Find most successful action patterns
        for category, patterns in self.action_patterns.items():
            if patterns:
                successful = [p for p in patterns if p['outcome'] in ['profit', 'avoided_loss']]
                if successful:
                    # Extract the common action principle
                    common_triggers = {}
                    for pattern in successful:
                        trigger_str = pattern['trigger'].get('pattern', 'unknown')
                        if trigger_str not in common_triggers:
                            common_triggers[trigger_str] = []
                        common_triggers[trigger_str].append(pattern['action'])
                    
                    # Find most common successful action for each trigger
                    for trigger, actions in common_triggers.items():
                        most_common = max(set(actions), key=actions.count)
                        wisdom[f"when_{trigger}"] = f"do_{most_common}"
        
        return wisdom


class EmbodiedMemory:
    """
    Memory that lives in the body, not just the mind
    Like how you remember dancing by moving, not by thinking
    """
    
    def __init__(self):
        self.muscle_memory = {}
        self.emotional_memory = {}
        self.rhythm_memory = {}
        
    def remember_in_body(self, action: str, feeling: str, rhythm: str):
        """
        Store memory as embodied experience
        """
        # Muscle memory - the movement itself
        self.muscle_memory[action] = {
            'tension': self._assess_tension(action),
            'flow': self._assess_flow(action),
            'effort': self._assess_effort(action)
        }
        
        # Emotional memory - how it felt
        self.emotional_memory[action] = feeling
        
        # Rhythm memory - the timing
        self.rhythm_memory[action] = rhythm
    
    def recall_through_movement(self, current_feeling: str) -> Optional[str]:
        """
        Recall by feeling, not thinking
        'This feels like that time when...'
        """
        for action, feeling in self.emotional_memory.items():
            if feeling == current_feeling:
                return action
        return None
    
    def _assess_tension(self, action: str) -> str:
        """How tense/relaxed was this action?"""
        if 'aggressive' in action or 'quick' in action:
            return 'high'
        elif 'wait' in action or 'patient' in action:
            return 'low'
        else:
            return 'medium'
    
    def _assess_flow(self, action: str) -> str:
        """How smooth/choppy was this action?"""
        if 'smooth' in action or 'glide' in action:
            return 'flowing'
        elif 'sudden' in action or 'sharp' in action:
            return 'staccato'
        else:
            return 'mixed'
    
    def _assess_effort(self, action: str) -> str:
        """How much effort did this take?"""
        if 'easy' in action or 'simple' in action:
            return 'effortless'
        elif 'hard' in action or 'complex' in action:
            return 'effortful'
        else:
            return 'moderate'


# Example usage showing action-oriented memory
if __name__ == "__main__":
    print("🔥 ACTION-ORIENTED MEMORY SYSTEM")
    print("=" * 60)
    print("Memory that prepares for action, not just stores data")
    print()
    
    # Create action memory
    action_mem = ActionMemory()
    embodied_mem = EmbodiedMemory()
    
    # Experience something
    experience = {
        'action': 'quick_sell_at_resistance',
        'pattern': 'double_top',
        'time_sense': 'power_hour',
        'profit': 250,
        'emotional_state': 'confident',
        'pattern_confidence': 0.85,
        'preconditions': {'rsi': 'overbought', 'volume': 'high'}
    }
    
    print("📝 EXPERIENCING:")
    print(f"  Action: {experience['action']}")
    print(f"  Pattern: {experience['pattern']}")
    print(f"  Outcome: ${experience['profit']} profit")
    print()
    
    # Remember it as action template
    template = action_mem.remember_through_action(experience)
    print("💾 STORED AS ACTION TEMPLATE:")
    print(f"  Trigger: {template['trigger']['pattern']} in {template['trigger']['context']}")
    print(f"  Action: {template['action']}")
    print(f"  Reusability: {template['reusable']:.1%}")
    print()
    
    # Store embodied memory
    embodied_mem.remember_in_body(
        experience['action'],
        experience['emotional_state'],
        'quick_decisive'
    )
    
    # Later, in similar situation
    current_situation = {
        'pattern': 'double_top',
        'time_sense': 'power_hour',
        'preconditions': {'rsi': 'overbought', 'volume': 'high'}
    }
    
    print("🎯 CURRENT SITUATION:")
    print(f"  Pattern detected: {current_situation['pattern']}")
    print()
    
    # Recall for action
    suggestion = action_mem.recall_for_action(current_situation)
    if suggestion:
        print("💡 ACTION MEMORY SUGGESTS:")
        print(f"  Action: {suggestion['suggested_action']}")
        print(f"  Confidence: {suggestion['confidence']:.1%}")
        print(f"  Type: {suggestion['memory_type']}")
    
    # Recall through feeling
    body_memory = embodied_mem.recall_through_movement('confident')
    if body_memory:
        print(f"\n🤸 BODY REMEMBERS: {body_memory}")
        print("  (This feeling means take quick decisive action)")
    
    # Extract wisdom
    wisdom = action_mem.consolidate_into_wisdom()
    print("\n📚 EXTRACTED WISDOM:")
    for trigger, action in wisdom.items():
        print(f"  {trigger} → {action}")
    
    print("\n" + "=" * 60)
    print("The tribe remembers not data but ACTIONS!")
    print("Memory serves movement, not storage!")
    print("We remember SO THAT we can act!")
    print("\n🔥 This is how humans really remember - through action!")