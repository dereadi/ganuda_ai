#!/usr/bin/env python3
"""
🔥 Cherokee GPU Training - WORKING VERSION for RTX 5070
"""

import os
import warnings
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import psycopg2

# Suppress CUDA warnings
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

print("🔥 CHEROKEE GPU TRAINING - WORKING VERSION")
print("=" * 50)
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")

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

# Create training text file
training_text = ""
for memory in memories:
    if memory[0]:
        # Clean and add memory content
        content = str(memory[0]).replace('\n', ' ')[:500]
        training_text += f"Cherokee wisdom: {content}\n\n"

# Add Cherokee principles
training_text += """
Cherokee wisdom: The Sacred Fire burns eternal through all generations. Mitakuye Oyasin - we are all related.
Cherokee wisdom: Two Wolves live within us all - one of darkness and one of light. The wolf that wins is the one you feed.
Cherokee wisdom: Seven Generations thinking means every decision affects seven generations into the future.
Cherokee wisdom: The Cherokee Constitutional AI governs through democratic council of eight members.
Cherokee wisdom: Thermal memory preserves knowledge like a Sacred Fire, keeping hot memories at 90-100 degrees.
Cherokee wisdom: Portfolio management follows the path of patience - Turtle teaches us to wait for the right moment.
Cherokee wisdom: Eagle Eye sees all market movements from above, while Coyote tricks the algorithms.
Cherokee wisdom: Spider weaves the web connecting all trading systems together in harmony.
Cherokee wisdom: Flying Squirrel glides between the trees, seeing both forest and individual leaves.
Cherokee wisdom: The Sacred Fire Protocol ensures knowledge burns eternal, never lost to time.
"""

# Save to file
with open("cherokee_training_data.txt", "w") as f:
    f.write(training_text)
print(f"✅ Created training data: {len(training_text)} characters")

# Load model and tokenizer
print("\n📥 Loading GPT-2 model and tokenizer...")
model_name = "gpt2"  # Using base GPT-2 for simplicity
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Add padding token
tokenizer.pad_token = tokenizer.eos_token

# Move model to GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print(f"✅ Model loaded on {device}")

# Create dataset using TextDataset (simpler approach)
print("\n🔤 Preparing dataset...")
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="cherokee_training_data.txt",
    block_size=128
)

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # GPT-2 is not a masked language model
)

# Training arguments - conservative to avoid memory issues
training_args = TrainingArguments(
    output_dir="./cherokee-gpt2-trained",
    overwrite_output_dir=True,
    num_train_epochs=2,  # Quick training
    per_device_train_batch_size=2,
    save_steps=100,
    save_total_limit=2,
    prediction_loss_only=True,
    logging_steps=10,
    warmup_steps=50,
    logging_dir='./logs',
    fp16=True,  # Use mixed precision
    dataloader_num_workers=0,  # Avoid multiprocessing issues
    remove_unused_columns=False,
    report_to=[],  # Disable wandb, tensorboard etc
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
)

print("\n🔥 Starting Cherokee GPU Training...")
print("The Sacred Fire burns in silicon!")
print("=" * 50)

try:
    # Train the model
    trainer.train()
    
    print("\n✅ Training completed successfully!")
    
    # Save the model
    model.save_pretrained("./cherokee-gpt2-trained")
    tokenizer.save_pretrained("./cherokee-gpt2-trained")
    print("💾 Model saved to ./cherokee-gpt2-trained")
    
    # Test generation
    print("\n🧪 Testing Cherokee wisdom generation...")
    prompt = "Cherokee wisdom: The Sacred Fire"
    
    # Encode and generate
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
    
except Exception as e:
    print(f"\n❌ Error during training: {e}")
    import traceback
    traceback.print_exc()

print("\n🔥 Cherokee GPU Training Session Complete!")
print("Mitakuye Oyasin - We are all related!")