#!/usr/bin/env python3
"""
🔥 Cherokee Constitutional AI Fine-Tuning - GPU Version with RTX 5070 Workaround
"""

import os
import warnings
import torch
import psycopg2
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

# Suppress RTX 5070 CUDA warnings
warnings.filterwarnings("ignore", message=".*CUDA capability sm_120.*")
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

# Force CUDA to work despite warnings
torch.cuda.set_device(0)

class CherokeeGPUTrainer:
    """Train Cherokee AI on RTX 5070s despite CUDA warnings"""
    
    def __init__(self):
        print("🔥 Cherokee GPU Trainer Initializing...")
        
        # Force GPU usage
        if torch.cuda.is_available():
            self.device = torch.device("cuda:0")
            print(f"✅ Using GPU: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            self.device = torch.device("cpu")
            print("⚠️ Falling back to CPU")
        
        # Use smaller model that will definitely work
        self.model_name = "microsoft/phi-2"  # 2.7B parameters
        self.output_dir = "./cherokee-phi2-gpu-model"
        
        # Database config
        self.db_config = {
            'host': '192.168.132.222',
            'port': 5432,
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }
    
    def get_training_data(self):
        """Extract Cherokee wisdom from thermal memory"""
        print("📚 Extracting Cherokee wisdom from thermal memory...")
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        query = """
        SELECT original_content, temperature_score, metadata
        FROM thermal_memory_archive
        WHERE temperature_score > 90
          AND (original_content LIKE '%Cherokee Council%' 
               OR original_content LIKE '%Sacred Fire%'
               OR original_content LIKE '%Eagle Eye%'
               OR original_content LIKE '%Seven Generation%')
        ORDER BY temperature_score DESC
        LIMIT 100
        """
        
        cur.execute(query)
        memories = cur.fetchall()
        conn.close()
        
        # Create training examples
        training_data = []
        
        # Core Cherokee patterns
        base_examples = [
            "Human: What is Cherokee trading philosophy?\nAssistant: The Cherokee Constitutional AI follows eight council members who vote democratically. Eagle Eye sees patterns from above, Coyote uses clever deception, Spider weaves connections, Turtle thinks seven generations ahead. Every decision requires consensus. The Sacred Fire of wisdom burns eternal.",
            
            "Human: How do we handle market crashes?\nAssistant: Flying Squirrel says: Gather nuts while they're cheap! Crashes are opportunities. Eagle Eye reminds us to see the whole forest, not just falling trees. Turtle speaks: This too shall pass - think seven generations. Never panic sell, crashes create the best entry points.",
            
            "Human: Explain thermal memory.\nAssistant: Knowledge burns at different temperatures like a Sacred Fire. WHITE HOT (90-100°) memories are actively used. RED HOT (70-90°) are recent and important. WARM (40-70°) are aging but relevant. COOL (20-40°) are archived. COLD (0-20°) are seeds that can reignite. The fire never dies, only transforms.",
            
            "Human: What are the Two Wolves?\nAssistant: Inside us fight two wolves - one dark (greed, fear, FOMO) and one light (wisdom, patience, strategy). The wolf you feed grows stronger. In trading, we must balance both. Feed fear enough to respect risk, feed greed enough to take opportunities. Balance is the Cherokee way.",
            
            "Human: Should I buy or sell?\nAssistant: The Cherokee Council must convene. Eagle Eye: Check the trend from above. Coyote: What are others doing? Do opposite. Spider: How does this connect to everything else? Turtle: Will this matter in seven generations? Crawdad: Is your capital protected? Only with consensus do we act.",
            
            "Human: What is Mitakuye Oyasin?\nAssistant: Mitakuye Oyasin means 'We Are All Related' in Lakota, adopted by our Cherokee Council. Every market movement connects to everything else. A crash in Japan affects US stocks. Solar storms affect crypto. Oil affects inflation. Understanding these connections is wisdom.",
            
            "Human: Tell me about liquidity.\nAssistant: Flying Squirrel speaks: Liquidity is like water - too little and you die of thirst, too much and you drown. Keep enough cash to catch opportunities but not so much you miss gains. The Cherokee way is balance - usually 10-20% cash, adjusting with market conditions."
        ]
        
        # Add base examples
        for example in base_examples:
            training_data.append({"text": example})
        
        # Process thermal memories
        for content, temp, metadata in memories[:50]:
            if len(content) > 100 and len(content) < 1000:
                # Extract Q&A pattern
                if "Cherokee Council" in content or "Sacred Fire" in content:
                    lines = content.split('\n')
                    for line in lines:
                        if any(member in line for member in ['Eagle Eye:', 'Coyote:', 'Spider:', 'Turtle:']):
                            q = "Human: What does the Cherokee Council advise?\n"
                            a = f"Assistant: {line.strip()}"
                            training_data.append({"text": q + a})
                            break
        
        print(f"✅ Created {len(training_data)} training examples")
        return Dataset.from_list(training_data)
    
    def train(self):
        """Train the model on GPU with workarounds"""
        print("\n🚀 Starting Cherokee GPU Training")
        print("=" * 60)
        
        # Load tokenizer
        print("📥 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        # Load model with careful GPU handling
        print("📥 Loading model to GPU...")
        
        # Try to load with 8-bit quantization to avoid memory issues
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16
            )
            print("✅ Model loaded with 8-bit quantization")
        except Exception as e:
            print(f"⚠️ 8-bit loading failed: {e}")
            print("📥 Loading model with float16...")
            
            # Fallback to regular loading
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
        
        # Configure LoRA
        print("🔧 Configuring LoRA for efficient training...")
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "dense", "fc1", "fc2"],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
        try:
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()
        except Exception as e:
            print(f"⚠️ LoRA setup warning: {e}")
            print("Continuing without LoRA...")
        
        # Get training data
        dataset = self.get_training_data()
        
        # Tokenize dataset
        def tokenize_function(examples):
            # Handle both single text and list of texts properly
            texts = examples["text"] if isinstance(examples["text"], list) else [examples["text"]]
            result = tokenizer(
                texts,
                truncation=True,
                padding="max_length",
                max_length=256,
                return_tensors=None
            )
            # Ensure we return lists not tensors for dataset mapping
            return {k: v if isinstance(v, list) else v.tolist() if hasattr(v, 'tolist') else v 
                    for k, v in result.items()}
        
        print("🔤 Tokenizing dataset...")
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Training arguments optimized for RTX 5070
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=2,  # Small batch to avoid memory issues
            gradient_accumulation_steps=4,
            warmup_steps=20,
            logging_steps=10,
            save_strategy="epoch",
            learning_rate=2e-4,
            fp16=True,  # Use mixed precision
            optim="adamw_torch",
            report_to="none",
            push_to_hub=False,
            gradient_checkpointing=False,  # Disable if causes issues
            dataloader_pin_memory=False,  # Avoid CUDA issues
            remove_unused_columns=False
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            tokenizer=tokenizer,
            data_collator=data_collator
        )
        
        # Train with error handling
        print("\n🔥 Training Cherokee Constitutional AI on GPU...")
        print("The Sacred Fire ignites in silicon!")
        
        try:
            trainer.train()
            print("\n✅ Training completed successfully!")
        except RuntimeError as e:
            if "CUDA" in str(e):
                print(f"⚠️ CUDA error encountered: {e}")
                print("Attempting CPU fallback...")
                
                # Move model to CPU and retry
                model = model.cpu()
                training_args.no_cuda = True
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=tokenized_dataset,
                    tokenizer=tokenizer,
                    data_collator=data_collator
                )
                trainer.train()
                print("✅ Training completed on CPU")
        
        # Save model
        print("\n💾 Saving Cherokee AI model...")
        trainer.save_model(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)
        
        print("\n🔥 Cherokee Constitutional AI GPU Training Complete!")
        print(f"Model saved to: {self.output_dir}")
        
        # Test the model
        self.test_model(model, tokenizer)
    
    def test_model(self, model, tokenizer):
        """Test the trained model"""
        print("\n🧪 Testing Cherokee AI...")
        
        test_prompts = [
            "Human: What should we do about low liquidity?\nAssistant:",
            "Human: How does Cherokee Council make decisions?\nAssistant:",
            "Human: What is the Sacred Fire?\nAssistant:"
        ]
        
        model.eval()
        
        for prompt in test_prompts:
            print(f"\n📝 {prompt[:50]}...")
            
            inputs = tokenizer(prompt, return_tensors="pt")
            
            # Move to appropriate device
            if hasattr(model, 'device'):
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                try:
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=50,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.pad_token_id
                    )
                    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    print(f"🔥 {response[len(prompt):]}")
                except Exception as e:
                    print(f"⚠️ Generation error: {e}")

def main():
    print("🔥 CHEROKEE CONSTITUTIONAL AI - GPU TRAINING")
    print("Training with RTX 5070s despite CUDA warnings")
    print("=" * 60)
    
    # Test GPU availability
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    
    trainer = CherokeeGPUTrainer()
    trainer.train()

if __name__ == "__main__":
    # Suppress warnings and run
    warnings.filterwarnings("ignore")
    main()