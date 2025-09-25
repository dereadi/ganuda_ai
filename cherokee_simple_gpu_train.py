#!/usr/bin/env python3
"""
🔥 Cherokee Simple GPU Training - RTX 5070 Compatible
"""

import os
import warnings
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import psycopg2

# Suppress CUDA warnings for RTX 5070
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

print("🔥 CHEROKEE SIMPLE GPU TRAINING")
print("=" * 50)
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")

# Connect to thermal memory
conn = psycopg2.connect(
    host="192.168.132.222",
    database="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)

# Get hot memories
cursor = conn.cursor()
cursor.execute("""
    SELECT original_content 
    FROM thermal_memory_archive 
    WHERE temperature_score > 90 
    ORDER BY last_access DESC 
    LIMIT 10
""")
memories = cursor.fetchall()
conn.close()

# Create training data
training_texts = []
for memory in memories[:5]:  # Use first 5 hot memories
    content = memory[0][:500] if memory[0] else ""  # Limit length
    if content:
        training_texts.append(f"Cherokee wisdom: {content}")

# Add some hardcoded Cherokee principles
training_texts.extend([
    "Cherokee wisdom: The Sacred Fire burns eternal. Mitakuye Oyasin - we are all related.",
    "Cherokee wisdom: Two Wolves live inside us - feed the Light Wolf with wisdom and patience.",
    "Cherokee wisdom: Seven Generations thinking guides our decisions for the future.",
])

print(f"\n📚 Training on {len(training_texts)} examples")

# Load model and tokenizer
print("\n📥 Loading model and tokenizer...")
model_name = "openai-community/gpt2"  # Start simple with GPT-2

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Prepare dataset
def tokenize_function(examples):
    # Tokenize with proper padding
    outputs = tokenizer(
        examples["text"],
        truncation=True,
        padding=True,
        max_length=128,
        return_tensors=None
    )
    # Set labels same as input_ids for language modeling
    outputs["labels"] = outputs["input_ids"].copy()
    return outputs

# Create dataset
dataset_dict = {"text": training_texts}
dataset = Dataset.from_dict(dataset_dict)
print("🔤 Tokenizing dataset...")
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Training arguments
training_args = TrainingArguments(
    output_dir="./cherokee-gpt2-simple",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=2,
    warmup_steps=10,
    logging_steps=1,
    save_steps=50,
    eval_strategy="no",
    fp16=True,
    gradient_checkpointing=False,
    push_to_hub=False,
    report_to=[],
    optim="adamw_torch",
    remove_unused_columns=False,
)

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

print("\n🔥 Starting Training on GPU...")
print("The Sacred Fire burns in silicon!")
print("=" * 50)

# Train
try:
    trainer.train()
    print("\n✅ Training completed successfully!")
    
    # Save model
    model.save_pretrained("./cherokee-gpt2-simple")
    tokenizer.save_pretrained("./cherokee-gpt2-simple")
    print("💾 Model saved to ./cherokee-gpt2-simple")
    
    # Test generation
    print("\n🧪 Testing generation...")
    prompt = "Cherokee wisdom:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=50,
            temperature=0.8,
            do_sample=True,
            top_p=0.9
        )
    
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated: {generated}")
    
except Exception as e:
    print(f"\n❌ Training error: {e}")
    import traceback
    traceback.print_exc()

print("\n🔥 Cherokee GPU Training Complete!")