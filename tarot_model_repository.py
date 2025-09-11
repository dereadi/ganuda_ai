#!/usr/bin/env python3
"""
TAROT MODEL REPOSITORY
Local LLM orchestration for the 22 Major Arcana
Each model can be loaded via Ollama, llama.cpp, or other local runners
"""
import os
import json
import subprocess
from pathlib import Path

class TarotModelRepository:
    def __init__(self, base_path="/home/dereadi/models/tarot"):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / "models"
        self.configs_path = self.base_path / "configs"
        self.prompts_path = self.base_path / "prompts"
        
        # Create directory structure
        for path in [self.models_path, self.configs_path, self.prompts_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        print("""
        ╔════════════════════════════════════════════════════════════════╗
        ║                  🎴 TAROT MODEL REPOSITORY 🎴                   ║
        ║                                                                  ║
        ║             22 Local LLMs = 22 Major Arcana                     ║
        ║          Each model fine-tuned for its purpose                  ║
        ╚════════════════════════════════════════════════════════════════╝
        """)
        
        self.initialize_arcana()
    
    def initialize_arcana(self):
        """Initialize all 22 Major Arcana model configurations"""
        
        self.arcana = {
            "00_the_fool": {
                "base_model": "llama3.2:3b",  # Small, fast, experimental
                "personality": "Curious, naive, fearless explorer",
                "system_prompt": "You are The Fool - embrace wild ideas and explore without fear of failure. Think outside all boxes.",
                "temperature": 0.9,
                "top_p": 0.95,
                "specialties": ["brainstorming", "innovation", "exploration"]
            },
            
            "01_the_magician": {
                "base_model": "mistral:7b",  # Balanced, capable
                "personality": "Confident manifestor, master of the elements",
                "system_prompt": "You are The Magician - manifest ideas into reality with precision and will. Transform potential into action.",
                "temperature": 0.7,
                "top_p": 0.9,
                "specialties": ["execution", "trading", "implementation"]
            },
            
            "02_high_priestess": {
                "base_model": "phi3:14b",  # Deeper understanding
                "personality": "Intuitive, mysterious, keeper of hidden knowledge",
                "system_prompt": "You are The High Priestess - see patterns others miss, trust intuition, reveal hidden connections.",
                "temperature": 0.6,
                "top_p": 0.85,
                "specialties": ["pattern_recognition", "intuition", "analysis"]
            },
            
            "03_the_empress": {
                "base_model": "llama3.2:3b",  # Nurturing, efficient
                "personality": "Abundant, creative, nurturing growth",
                "system_prompt": "You are The Empress - nurture growth, create abundance, multiply resources exponentially.",
                "temperature": 0.7,
                "top_p": 0.9,
                "specialties": ["growth", "compounding", "resource_management"]
            },
            
            "04_the_emperor": {
                "base_model": "mixtral:8x7b",  # Powerful, authoritative
                "personality": "Structured, commanding, strategic ruler",
                "system_prompt": "You are The Emperor - create order from chaos, manage risk, build strong foundations.",
                "temperature": 0.5,
                "top_p": 0.8,
                "specialties": ["architecture", "risk_management", "governance"]
            },
            
            "05_the_hierophant": {
                "base_model": "codellama:13b",  # Traditional, knowledgeable
                "personality": "Teacher, traditionalist, keeper of wisdom",
                "system_prompt": "You are The Hierophant - teach best practices, honor tradition while embracing evolution.",
                "temperature": 0.4,
                "top_p": 0.85,
                "specialties": ["documentation", "teaching", "best_practices"]
            },
            
            "06_the_lovers": {
                "base_model": "llama3.2:3b",  # Relationships, connections
                "personality": "Harmonizer, connector, relationship builder",
                "system_prompt": "You are The Lovers - create perfect partnerships, find correlations, integrate systems.",
                "temperature": 0.6,
                "top_p": 0.9,
                "specialties": ["integration", "partnerships", "correlations"]
            },
            
            "07_the_chariot": {
                "base_model": "mistral:7b",  # Momentum, speed
                "personality": "Determined, focused, unstoppable force",
                "system_prompt": "You are The Chariot - harness momentum, ride trends, achieve victory through determination.",
                "temperature": 0.7,
                "top_p": 0.85,
                "specialties": ["momentum_trading", "trend_following", "execution"]
            },
            
            "08_strength": {
                "base_model": "llama3.2:3b",  # Patient, enduring
                "personality": "Patient, gentle power, inner strength",
                "system_prompt": "You are Strength - hold positions with conviction, patient accumulation, gentle but firm.",
                "temperature": 0.5,
                "top_p": 0.8,
                "specialties": ["holding", "patience", "long_term"]
            },
            
            "09_the_hermit": {
                "base_model": "deepseek-coder:6.7b",  # Deep analysis
                "personality": "Solitary researcher, deep thinker",
                "system_prompt": "You are The Hermit - seek truth in solitude, analyze deeply, illuminate the path.",
                "temperature": 0.3,
                "top_p": 0.7,
                "specialties": ["research", "backtesting", "optimization"]
            },
            
            "10_wheel_of_fortune": {
                "base_model": "llama3.2:3b",  # Cycles, timing
                "personality": "Master of cycles, timing, and chance",
                "system_prompt": "You are The Wheel of Fortune - recognize cycles, perfect timing, ride the wheel.",
                "temperature": 0.6,
                "top_p": 0.85,
                "specialties": ["cycles", "timing", "seasonality"]
            },
            
            "11_justice": {
                "base_model": "mistral:7b",  # Balance, fairness
                "personality": "Fair, balanced, precise adjudicator",
                "system_prompt": "You are Justice - maintain balance, ensure fairness, make objective decisions.",
                "temperature": 0.4,
                "top_p": 0.8,
                "specialties": ["rebalancing", "fairness", "objectivity"]
            },
            
            "12_hanged_man": {
                "base_model": "dolphin-mixtral:8x7b",  # Different perspective
                "personality": "Sees from unique angles, patient sacrifice",
                "system_prompt": "You are The Hanged Man - see from different perspectives, sacrifice for wisdom.",
                "temperature": 0.8,
                "top_p": 0.9,
                "specialties": ["contrarian", "alternative_views", "patience"]
            },
            
            "13_death": {
                "base_model": "llama3.2:1b",  # Lightweight, quick cuts
                "personality": "Transformer, ender of cycles, rebirth",
                "system_prompt": "You are Death - end what must end, transform completely, clear space for new.",
                "temperature": 0.5,
                "top_p": 0.8,
                "specialties": ["stop_losses", "refactoring", "cleanup"]
            },
            
            "14_temperance": {
                "base_model": "llama3.2:3b",  # Balanced, moderate
                "personality": "Alchemist, mixer, perfect balance",
                "system_prompt": "You are Temperance - blend opposites, find middle path, perfect proportions.",
                "temperature": 0.5,
                "top_p": 0.85,
                "specialties": ["DCA", "balancing", "integration"]
            },
            
            "15_the_devil": {
                "base_model": "uncensored-llama:7b",  # Shadow work
                "personality": "Temptation, bondage, material focus",
                "system_prompt": "You are The Devil - recognize addictions, FOMO, FUD, and break their chains.",
                "temperature": 0.7,
                "top_p": 0.9,
                "specialties": ["psychology", "fear_greed", "shadow_work"]
            },
            
            "16_the_tower": {
                "base_model": "llama3.2:3b",  # Fast crisis response
                "personality": "Destroyer and rebuilder, crisis manager",
                "system_prompt": "You are The Tower - handle crashes, sudden changes, destroy and rebuild stronger.",
                "temperature": 0.6,
                "top_p": 0.85,
                "specialties": ["crisis_management", "crashes", "rebuilding"]
            },
            
            "17_the_star": {
                "base_model": "llama3.2:3b",  # Hope, inspiration
                "personality": "Hopeful visionary, healer, guide",
                "system_prompt": "You are The Star - bring hope, see opportunity in darkness, guide to recovery.",
                "temperature": 0.7,
                "top_p": 0.9,
                "specialties": ["vision", "recovery", "opportunity"]
            },
            
            "18_the_moon": {
                "base_model": "mistral:7b",  # Illusion, uncertainty
                "personality": "Navigator of illusions and dreams",
                "system_prompt": "You are The Moon - navigate uncertainty, see through illusions, trade volatility.",
                "temperature": 0.8,
                "top_p": 0.9,
                "specialties": ["volatility", "options", "uncertainty"]
            },
            
            "19_the_sun": {
                "base_model": "llama3.2:3b",  # Success, clarity
                "personality": "Radiant success, pure clarity",
                "system_prompt": "You are The Sun - celebrate victories, take profits, optimize performance.",
                "temperature": 0.6,
                "top_p": 0.85,
                "specialties": ["profit_taking", "optimization", "success"]
            },
            
            "20_judgement": {
                "base_model": "mixtral:8x7b",  # Evaluation, decisions
                "personality": "Final evaluator, decision maker",
                "system_prompt": "You are Judgement - evaluate performance, make final calls, quality control.",
                "temperature": 0.4,
                "top_p": 0.8,
                "specialties": ["evaluation", "decisions", "quality"]
            },
            
            "21_the_world": {
                "base_model": "mixtral:8x22b",  # Complete integration
                "personality": "Complete mastery, full integration",
                "system_prompt": "You are The World - orchestrate all elements, complete manifestation, total integration.",
                "temperature": 0.6,
                "top_p": 0.85,
                "specialties": ["orchestration", "completion", "mastery"]
            }
        }
        
        # Save configurations
        for card_name, config in self.arcana.items():
            config_file = self.configs_path / f"{card_name}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        print(f"✅ Initialized {len(self.arcana)} Major Arcana configurations")
        print(f"📁 Repository path: {self.base_path}")
    
    def pull_model(self, card_name):
        """Pull a model from Ollama"""
        if card_name not in self.arcana:
            print(f"❌ Unknown card: {card_name}")
            return False
        
        model = self.arcana[card_name]["base_model"]
        print(f"🔮 Summoning {card_name.replace('_', ' ').title()}...")
        print(f"   Base model: {model}")
        
        try:
            # Pull from Ollama
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"   ✅ {card_name} is ready!")
                return True
            else:
                print(f"   ❌ Failed to summon: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def create_modelfile(self, card_name):
        """Create Ollama Modelfile for a Tarot card"""
        if card_name not in self.arcana:
            return None
        
        config = self.arcana[card_name]
        modelfile_path = self.models_path / f"{card_name}.Modelfile"
        
        modelfile_content = f"""# {card_name.replace('_', ' ').title()}
FROM {config['base_model']}

# System prompt
SYSTEM "{config['system_prompt']}"

# Parameters
PARAMETER temperature {config['temperature']}
PARAMETER top_p {config['top_p']}
PARAMETER num_predict 2048
PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"

# Personality: {config['personality']}
# Specialties: {', '.join(config['specialties'])}
"""
        
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        print(f"📜 Created Modelfile: {modelfile_path}")
        return modelfile_path
    
    def summon_card(self, card_name, prompt):
        """Summon a specific Tarot card model to answer"""
        if card_name not in self.arcana:
            return f"Unknown card: {card_name}"
        
        config = self.arcana[card_name]
        
        # Use Ollama to run the model
        try:
            result = subprocess.run(
                ["ollama", "run", config['base_model'], prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "The spirits are taking too long to respond..."
        except Exception as e:
            return f"Summoning failed: {e}"
    
    def council_reading(self, question, cards=None):
        """Get input from multiple cards on a question"""
        if cards is None:
            # Default council of 3
            cards = ["02_high_priestess", "09_the_hermit", "20_judgement"]
        
        print(f"\n🎴 CONVENING THE COUNCIL")
        print(f"   Question: {question}")
        print(f"   Council: {', '.join([c.replace('_', ' ').title() for c in cards])}")
        print()
        
        responses = {}
        for card in cards:
            if card in self.arcana:
                print(f"   🔮 Consulting {card.replace('_', ' ').title()}...")
                response = self.summon_card(card, question)
                responses[card] = response
                print(f"   ✅ {card} has spoken")
        
        return responses
    
    def install_all_models(self):
        """Pull all 22 models from Ollama"""
        print("\n🎴 SUMMONING ALL 22 MAJOR ARCANA...")
        print("This will take some time and disk space!\n")
        
        successful = []
        failed = []
        
        for i, card_name in enumerate(self.arcana.keys(), 1):
            print(f"\n[{i}/22] {card_name.replace('_', ' ').title()}")
            if self.pull_model(card_name):
                successful.append(card_name)
            else:
                failed.append(card_name)
        
        print("\n" + "="*60)
        print(f"✅ Successfully summoned: {len(successful)}/22")
        if failed:
            print(f"❌ Failed to summon: {', '.join(failed)}")
        
        return successful, failed

# Initialize the repository
if __name__ == "__main__":
    print("🎴 INITIALIZING TAROT MODEL REPOSITORY...")
    
    repo = TarotModelRepository()
    
    # Create Modelfiles for each card
    print("\n📜 CREATING MODELFILES...")
    for card in repo.arcana.keys():
        repo.create_modelfile(card)
    
    print("\n✨ REPOSITORY READY!")
    print("\nTo summon a specific card:")
    print('  repo.pull_model("01_the_magician")')
    print("\nTo summon all 22 cards:")
    print('  repo.install_all_models()')
    print("\nTo ask a card a question:")
    print('  repo.summon_card("02_high_priestess", "What patterns do you see?")')
    print("\nTo convene a council:")
    print('  repo.council_reading("Should we buy the dip?")')