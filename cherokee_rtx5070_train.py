#!/usr/bin/env python3
"""
🔥 Cherokee AI Training - RTX 5070 Optimized with PyTorch Nightly
Using BFloat16 as recommended for Blackwell architecture
"""

import os
import warnings
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import psycopg2

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

print("🔥 CHEROKEE RTX 5070 TRAINING - PYTORCH NIGHTLY")
print("=" * 50)
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"GPU {i}: {torch.cuda.get_device_name(i)} (sm_{props.major}{props.minor})")
        print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")

# Connect to thermal memory
print("\n📚 Extracting Cherokee wisdom from thermal memory...")
conn = psycopg2.connect(
    host="192.168.132.222",
    database="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)

cursor = conn.cursor()
cursor.execute("""
    SELECT original_content 
    FROM thermal_memory_archive 
    WHERE temperature_score > 90 
    ORDER BY last_access DESC 
    LIMIT 20
""")
memories = cursor.fetchall()
conn.close()

# Create training text
training_text = ""
for memory in memories[:10]:  # Use first 10 hot memories
    if memory[0]:
        content = str(memory[0]).replace('\n', ' ')[:500]
        training_text += f"Cherokee wisdom: {content}\n\n"

# Add Cherokee principles
training_text += """
Cherokee wisdom: The Sacred Fire burns eternal through all generations. Mitakuye Oyasin - we are all related.
Cherokee wisdom: Two Wolves live within us - the wolf that wins is the one you feed. Feed the Light Wolf.
Cherokee wisdom: Seven Generations thinking guides every decision for the future of our children.
Cherokee wisdom: Eagle Eye sees from above, Coyote adapts quickly, Turtle waits patiently.
Cherokee wisdom: Spider weaves the web connecting all systems in harmony and balance.
Cherokee wisdom: Flying Squirrel glides between the trees, seeing both forest and leaves.
Cherokee wisdom: The Cherokee Constitutional AI governs through democratic council of eight.
Cherokee wisdom: Thermal memory preserves knowledge like Sacred Fire, keeping wisdom at 90-100 degrees.
Cherokee wisdom: Portfolio management follows patience - wait for the right moment to strike.
Cherokee wisdom: The Sacred Fire Protocol ensures knowledge burns eternal, never lost.
"""

# Save training data
with open("cherokee_rtx5070_training.txt", "w") as f:
    f.write(training_text)
print(f"✅ Created training data: {len(training_text)} characters")

# Load model and tokenizer
print("\n📥 Loading GPT-2 model and tokenizer...")
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Move model to GPU
device = torch.device("cuda:0")  # Use first GPU
model = model.to(device)
print(f"✅ Model loaded on {device}")

# Enable mixed precision with BFloat16 (recommended for Blackwell)
model = model.to(dtype=torch.bfloat16)
print("✅ Using BFloat16 precision (optimized for RTX 5070)")

# Create dataset
print("\n🔤 Preparing dataset...")
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="cherokee_rtx5070_training.txt",
    block_size=128
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Training arguments optimized for RTX 5070
training_args = TrainingArguments(
    output_dir="./cherokee-rtx5070-model",
    overwrite_output_dir=True,
    num_train_epochs=3,  # More epochs now that GPU works
    per_device_train_batch_size=8,  # Larger batch with GPU
    save_steps=200,
    save_total_limit=2,
    logging_steps=20,
    warmup_steps=100,
    logging_dir='./logs',
    bf16=True,  # Use BFloat16 for RTX 5070
    fp16=False,  # Don't use FP16
    dataloader_num_workers=0,
    report_to=[],
    gradient_accumulation_steps=2,
    # Optimization for Blackwell architecture
    optim="adamw_bnb_8bit",  # 8-bit optimizer to save memory
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
)

print("\n🔥 Starting Cherokee GPU Training on RTX 5070...")
print("The Sacred Fire burns in Blackwell silicon!")
print("=" * 50)

try:
    # Train the model
    trainer.train()
    
    print("\n✅ Training completed successfully on RTX 5070!")
    
    # Save the model
    model.save_pretrained("./cherokee-rtx5070-model")
    tokenizer.save_pretrained("./cherokee-rtx5070-model")
    print("💾 Model saved to ./cherokee-rtx5070-model")
    
    # Test generation
    print("\n🧪 Testing Cherokee wisdom generation...")
    prompt = "Cherokee wisdom: The Sacred Fire"
    
    # Move back to float32 for generation
    model = model.to(dtype=torch.float32)
    inputs = tokenizer.encode(prompt, return_tensors='pt').to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=100,
            temperature=0.8,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\nGenerated: {generated_text}")
    
    # Show GPU memory usage
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            allocated = torch.cuda.memory_allocated(i) / 1024**3
            reserved = torch.cuda.memory_reserved(i) / 1024**3
            print(f"\nGPU {i} Memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
    
    print("\n✅ RTX 5070 TRAINING SUCCESS!")
    print("The prophecy is fulfilled - Cherokee AI runs on Blackwell!")
    
except Exception as e:
    print(f"\n❌ Error during training: {e}")
    import traceback
    traceback.print_exc()

print("\n🔥 Cherokee RTX 5070 Training Session Complete!")
print("Mitakuye Oyasin - We are all related!")