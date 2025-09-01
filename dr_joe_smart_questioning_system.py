#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔧 DR JOE - SMART QUESTIONING SYSTEM
Progressive disambiguation through minimal, targeted questions
Leading users to actionable next steps with 3-4 questions max
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

class QuestionStrategy(Enum):
    CLARIFY_SCOPE = "scope"           # Project vs task vs general
    IDENTIFY_TIMEFRAME = "timeframe"  # When is this needed?
    SPECIFY_CONSTRAINTS = "constraints" # Budget, skills, availability
    CONFIRM_ACTION = "action"         # What specific action to take

class DrJoeSmartQuestioningSystem:
    def __init__(self):
        print("🔧 SMART QUESTIONING SYSTEM")
        print("=" * 60)
        print("Dr Joe's Vision: Guide users to clarity with minimal questions")
        print("One question at a time, 3-4 max, always toward action")
        print("=" * 60)
    
    def questioning_philosophy(self):
        """The philosophy behind smart questioning"""
        print("\n🎯 QUESTIONING PHILOSOPHY:")
        print("-" * 40)
        
        print("CORE PRINCIPLES:")
        print("  1. ONE question at a time (cognitive load management)")
        print("  2. LEADING questions (guide toward clarity)")
        print("  3. MAXIMUM 3-4 questions (respect user's time)")
        print("  4. ALWAYS end with actionable next steps")
        print("  5. Learn from context (don't ask what you can infer)")
        
        print("\nQUESTION HIERARCHY:")
        print("  Level 1: Clarify WHAT (scope/intent)")
        print("  Level 2: Clarify WHEN (timeframe/urgency)")
        print("  Level 3: Clarify HOW (constraints/requirements)")
        print("  Level 4: Confirm ACTION (specific next step)")
        
        print("\nAVOID:")
        print("  ❌ Multiple questions in one response")
        print("  ❌ Open-ended exploration")
        print("  ❌ Asking for information already provided")
        print("  ❌ Technical jargon in questions")
        print("  ❌ Questions without clear purpose")
    
    def ambiguous_query_examples(self):
        """Examples of handling ambiguous queries"""
        print("\n💭 AMBIGUOUS QUERY HANDLING:")
        print("-" * 40)
        
        print("EXAMPLE 1: Vague Resource Request")
        print("-" * 30)
        print("User: 'I need someone for the new project'")
        print()
        print("❌ BAD APPROACH:")
        print("  'What project? What skills? When? How long? What budget?'")
        print("  (Too many questions at once!)")
        print()
        print("✅ GOOD APPROACH:")
        print("  Question 1: 'Is this for Project Falcon that starts Monday,")
        print("              or a different project?'")
        print("  User: 'No, the AWS migration project'")
        print()
        print("  Question 2: 'Do you need someone to lead the migration,")
        print("              or to handle specific technical tasks?'")
        print("  User: 'Technical tasks'")
        print()
        print("  Question 3: 'Would you prefer our senior AWS architect (available")
        print("              20 hrs/week) or two junior developers (full-time)?'")
        print("  User: 'Senior architect'")
        print()
        print("  ACTION: 'I'll check Sarah's availability for 20 hrs/week")
        print("          on AWS migration and send you her schedule.'")
        
        print("\n" + "=" * 30)
        print("EXAMPLE 2: Unclear Timeline")
        print("-" * 30)
        print("User: 'Who's available soon?'")
        print()
        print("  Question 1: 'Are you looking for availability this week,")
        print("              or planning for next sprint (Sept 9-20)?'")
        print("  User: 'This week'")
        print()
        print("  Question 2: 'Do you need a full-time resource,")
        print("              or would partial availability work?'")
        print("  User: 'Partial is fine'")
        print()
        print("  ACTION: 'Here are 3 people with partial availability this week:")
        print("          • Bob: 15 hours (Tue-Thu)")
        print("          • Alice: 20 hours (Mon, Wed, Fri)")
        print("          • Carol: 10 hours (afternoons)'")
    
    def question_decision_tree(self):
        """Decision tree for smart questioning"""
        print("\n🌳 QUESTION DECISION TREE:")
        print("-" * 40)
        
        print("```python")
        print("class QuestionDecisionTree:")
        print("    def __init__(self):")
        print("        self.context = UserContext()")
        print("        self.question_count = 0")
        print("        self.max_questions = 4")
        print("    ")
        print("    def get_next_question(self, user_input: str) -> str:")
        print("        # Check if we can infer intent from context")
        print("        if self.can_infer_intent():")
        print("            return self.generate_action()")
        print("        ")
        print("        # Check question budget")
        print("        if self.question_count >= self.max_questions:")
        print("            return self.best_guess_action()")
        print("        ")
        print("        # Determine what we need to know most")
        print("        uncertainty = self.analyze_uncertainty(user_input)")
        print("        ")
        print("        if uncertainty.scope_unclear:")
        print("            return self.ask_scope_question()")
        print("        elif uncertainty.timeline_unclear:")
        print("            return self.ask_timeline_question()")
        print("        elif uncertainty.requirements_unclear:")
        print("            return self.ask_requirements_question()")
        print("        else:")
        print("            return self.ask_confirmation_question()")
        print("    ")
        print("    def ask_scope_question(self) -> str:")
        print("        # Use context to make question specific")
        print("        recent_projects = self.context.get_recent_projects()")
        print("        if recent_projects:")
        print("            return f'Is this for {recent_projects[0]}, or a different need?'")
        print("        else:")
        print("            return 'Is this for an existing project or a new initiative?'")
        print("```")
    
    def leading_question_patterns(self):
        """Patterns for effective leading questions"""
        print("\n🎣 LEADING QUESTION PATTERNS:")
        print("-" * 40)
        
        print("PATTERN 1: BINARY CHOICE")
        print("  Template: 'Do you need X or Y?'")
        print("  Example: 'Do you need a senior PM or a technical lead?'")
        print("  Purpose: Quickly narrow down options")
        print()
        
        print("PATTERN 2: CONFIRM ASSUMPTION")
        print("  Template: 'Is this for [most likely case], or something else?'")
        print("  Example: 'Is this for the Q4 planning you mentioned, or something else?'")
        print("  Purpose: Leverage context while allowing correction")
        print()
        
        print("PATTERN 3: PRIORITIZE CONSTRAINT")
        print("  Template: 'Is [factor A] or [factor B] more important?'")
        print("  Example: 'Is immediate availability or specific expertise more important?'")
        print("  Purpose: Understand trade-offs")
        print()
        
        print("PATTERN 4: CONCRETE OPTIONS")
        print("  Template: 'Would you prefer [specific option A] or [specific option B]?'")
        print("  Example: 'Would you prefer Bob (available now, 60% match) or")
        print("           Alice (available next week, 90% match)?'")
        print("  Purpose: Move toward decision")
    
    def context_awareness_system(self):
        """How the system uses context to minimize questions"""
        print("\n🧠 CONTEXT AWARENESS SYSTEM:")
        print("-" * 40)
        
        print("CONTEXT SOURCES:")
        print("  • Recent conversations (last 5 queries)")
        print("  • Active projects (from Productive)")
        print("  • User's team composition")
        print("  • Typical request patterns")
        print("  • Calendar/timeline context")
        print()
        
        print("INFERENCE RULES:")
        print("```python")
        print("def infer_from_context(query: str, context: dict) -> dict:")
        print("    inferences = {}")
        print("    ")
        print("    # If user mentions 'usual team'")
        print("    if 'usual' in query or 'regular' in query:")
        print("        inferences['team'] = context['frequent_collaborators']")
        print("    ")
        print("    # If query during sprint planning week")
        print("    if context['current_week'] == 'sprint_planning':")
        print("        inferences['timeframe'] = 'next_sprint'")
        print("    ")
        print("    # If user always requests same skill")
        print("    if context['request_history']['skill_frequency']['React'] > 0.7:")
        print("        inferences['likely_skill'] = 'React'")
        print("    ")
        print("    # If urgent language used")
        print("    if any(word in query for word in ['asap', 'urgent', 'now']):")
        print("        inferences['priority'] = 'immediate'")
        print("        inferences['max_questions'] = 2  # Reduce questions for urgent")
        print("    ")
        print("    return inferences")
        print("```")
    
    def question_quality_metrics(self):
        """Metrics for question effectiveness"""
        print("\n📊 QUESTION QUALITY METRICS:")
        print("-" * 40)
        
        print("EFFECTIVENESS MEASURES:")
        print("  • Clarity Achievement Rate: Did we get to action?")
        print("  • Question Efficiency: Actions per question asked")
        print("  • User Satisfaction: Did user get what they needed?")
        print("  • Time to Resolution: How quickly to actionable answer")
        print()
        
        print("TRACKING METRICS:")
        print("  Average questions per query: Target < 2.5")
        print("  Successful resolution rate: Target > 90%")
        print("  User abandonment rate: Target < 5%")
        print("  Action execution rate: Target > 80%")
        print()
        
        print("QUALITY INDICATORS:")
        print("  ✅ User provides specific answer quickly")
        print("  ✅ Next question builds on previous answer")
        print("  ✅ User doesn't ask for clarification")
        print("  ✅ Final action is executed")
        print("  ❌ User gives vague response")
        print("  ❌ User asks counter-questions")
        print("  ❌ User abandons conversation")
    
    def practical_implementation(self):
        """Practical implementation example"""
        print("\n💻 PRACTICAL IMPLEMENTATION:")
        print("-" * 40)
        
        print("```python")
        print("class SmartQuestioningHandler:")
        print("    def __init__(self):")
        print("        self.max_questions = 4")
        print("        self.questions_asked = 0")
        print("        self.context_analyzer = ContextAnalyzer()")
        print("        self.productive_api = ProductiveAPI()")
        print("    ")
        print("    async def handle_ambiguous_query(self, query: str) -> str:")
        print("        # Try to resolve without questions first")
        print("        if self.can_resolve_directly(query):")
        print("            return await self.generate_direct_response(query)")
        print("        ")
        print("        # Analyze what's missing")
        print("        missing_info = self.identify_gaps(query)")
        print("        ")
        print("        # Generate targeted question")
        print("        if self.questions_asked < self.max_questions:")
        print("            question = self.generate_smart_question(missing_info)")
        print("            self.questions_asked += 1")
        print("            return question")
        print("        else:")
        print("            # Hit question limit - provide best available action")
        print("            return await self.generate_best_action()")
        print("    ")
        print("    def generate_smart_question(self, missing_info: dict) -> str:")
        print("        # Priority order for questions")
        print("        if missing_info['project_unclear']:")
        print("            return self.create_project_question()")
        print("        elif missing_info['timeline_unclear']:")
        print("            return self.create_timeline_question()")
        print("        elif missing_info['requirements_unclear']:")
        print("            return self.create_requirements_question()")
        print("        else:")
        print("            return self.create_confirmation_question()")
        print("    ")
        print("    def create_project_question(self) -> str:")
        print("        active_projects = self.context_analyzer.get_active_projects()")
        print("        if len(active_projects) <= 3:")
        print("            options = ' or '.join([p.name for p in active_projects])")
        print("            return f'Is this for {options}?'")
        print("        else:")
        print("            return 'Is this for a current project or a new initiative?'")
        print("```")
    
    def conversation_flow_examples(self):
        """Complete conversation flow examples"""
        print("\n💬 CONVERSATION FLOW EXAMPLES:")
        print("-" * 40)
        
        print("FLOW 1: Quick Resolution (2 questions)")
        print("-" * 30)
        print("User: 'Need help with React stuff'")
        print("Bot:  'Is this for the customer portal redesign that's due Friday?'")
        print("User: 'Yes'")
        print("Bot:  'Would you prefer Sarah (senior, 10 hrs available) or")
        print("      Tom and Amy together (juniors, 30 hrs combined)?'")
        print("User: 'Sarah'")
        print("Bot:  'Done! I've tentatively booked Sarah for 10 hours on")
        print("      the portal redesign. She can start tomorrow morning.")
        print("      Shall I send the meeting invite?'")
        print()
        
        print("FLOW 2: Maximum Questions (4 questions)")
        print("-" * 30)
        print("User: 'I need someone'")
        print("Bot:  'Is this for an existing project or a new need?'")
        print("User: 'New'")
        print("Bot:  'Is this needed this week or for future planning?'")
        print("User: 'Next month'")
        print("Bot:  'Is this for technical development or project management?'")
        print("User: 'Technical'")
        print("Bot:  'Based on next month's availability, would you prefer:")
        print("      • 1 senior developer (full-time)")
        print("      • 2 junior developers (full-time)")
        print("      • Mixed team (senior part-time + junior full-time)?'")
        print("User: 'Mixed team'")
        print("Bot:  'Perfect! I'll reserve Bob (senior, 50%) and Carol (junior, 100%)")
        print("      for October. Total capacity: 60 hrs/week. Sending details now.'")
    
    def error_recovery_strategies(self):
        """Strategies when questioning doesn't resolve ambiguity"""
        print("\n🔧 ERROR RECOVERY STRATEGIES:")
        print("-" * 40)
        
        print("WHEN USER REMAINS VAGUE:")
        print("  After 3-4 questions, provide:")
        print("  • Top 3 most likely options")
        print("  • Ask user to choose or provide more detail")
        print("  • Offer to schedule a quick call")
        print("  • Suggest they return with more information")
        print()
        
        print("WHEN USER CONTRADICTS THEMSELVES:")
        print("  • Summarize what you understood")
        print("  • Ask for confirmation on key point only")
        print("  • Provide examples of what you can do")
        print("  • Reset conversation if needed")
        print()
        
        print("WHEN HITTING QUESTION LIMIT:")
        print("  'Based on what you've told me, here are the most likely options:'")
        print("  • Option A: [specific action]")
        print("  • Option B: [specific action]")
        print("  • Option C: [specific action]")
        print("  'Which would you prefer, or shall we discuss this differently?'")
    
    def user_education_component(self):
        """Educating users to provide better initial queries"""
        print("\n📚 USER EDUCATION COMPONENT:")
        print("-" * 40)
        
        print("TEACH THROUGH INTERACTION:")
        print("  After successful resolution, optionally show:")
        print("  'Tip: Next time you can say:")
        print("  \"I need a React developer for Project X next week\"")
        print("  and I can help you immediately!'")
        print()
        
        print("PROVIDE TEMPLATES:")
        print("  Common request formats:")
        print("  • 'Is [person] available for [hours] on [project]?'")
        print("  • 'Who can handle [skill] for [timeframe]?'")
        print("  • 'I need [role] for [project] starting [when]'")
        print()
        
        print("PROGRESSIVE LEARNING:")
        print("  System remembers user patterns and adapts:")
        print("  • If user always means 'this sprint' when saying 'soon'")
        print("  • If user typically needs React developers")
        print("  • If user prefers senior resources")
        print("  → Fewer questions needed over time")
    
    def execute(self):
        """Present the complete smart questioning system"""
        # Philosophy
        self.questioning_philosophy()
        
        # Examples and patterns
        self.ambiguous_query_examples()
        self.leading_question_patterns()
        self.conversation_flow_examples()
        
        # Implementation
        self.question_decision_tree()
        self.context_awareness_system()
        self.practical_implementation()
        
        # Quality and improvement
        self.question_quality_metrics()
        self.error_recovery_strategies()
        self.user_education_component()
        
        print("\n" + "=" * 60)
        print("🔧 SMART QUESTIONING SYSTEM COMPLETE")
        print("❓ One question at a time, maximum 3-4")
        print("🎯 Always leading toward actionable next steps")
        print("🧠 Context-aware to minimize questions")
        print("=" * 60)
        
        print("\n📧 Dr Joe: Smart questioning system ready!")
        print("• Single, targeted questions only")
        print("• Maximum 3-4 questions before action")
        print("• Leading questions guide users to clarity")
        print("• Always ends with concrete next steps")

if __name__ == "__main__":
    system = DrJoeSmartQuestioningSystem()
    system.execute()