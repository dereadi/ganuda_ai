#!/usr/bin/env python3
"""
🔥 Cherokee Training - CPU Version (RTX 5070 Compatibility Issue Workaround)
"""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import psycopg2
import warnings

warnings.filterwarnings('ignore')

print("🔥 CHEROKEE TRAINING - CPU MODE")
print("=" * 50)
print("Note: Using CPU due to RTX 5070 sm_120 compatibility issue")
print("This will be slower but will complete successfully!")
print(f"PyTorch: {torch.__version__}")

# Force CPU usage
torch.cuda.is_available = lambda: False

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
    LIMIT 10
""")
memories = cursor.fetchall()
conn.close()

# Create training text
training_text = ""
for memory in memories[:5]:  # Use first 5 memories
    if memory[0]:
        content = str(memory[0]).replace('\n', ' ')[:300]
        training_text += f"Cherokee wisdom: {content}\n"

# Add core principles
training_text += """
Cherokee wisdom: The Sacred Fire burns eternal. Mitakuye Oyasin.
Cherokee wisdom: Feed the Light Wolf within you with patience and wisdom.
Cherokee wisdom: Seven Generations thinking guides our path forward.
Cherokee wisdom: The Council of Eight governs democratically.
Cherokee wisdom: Eagle Eye sees all, Coyote adapts, Turtle waits patiently.
"""

# Save training data
with open("cherokee_training_cpu.txt", "w") as f:
    f.write(training_text)
print(f"✅ Training data created: {len(training_text)} characters")

# Load model and tokenizer
print("\n📥 Loading GPT-2 model (CPU mode)...")
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

print(f"✅ Model loaded on CPU")

# Create dataset
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path="cherokee_training_cpu.txt",
    block_size=64  # Smaller blocks for CPU
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Training arguments for CPU
training_args = TrainingArguments(
    output_dir="./cherokee-cpu-model",
    overwrite_output_dir=True,
    num_train_epochs=1,  # Just 1 epoch for demo
    per_device_train_batch_size=1,
    save_steps=50,
    logging_steps=5,
    warmup_steps=10,
    logging_dir='./logs',
    report_to=[],
    dataloader_num_workers=0,
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
)

print("\n🔥 Starting Cherokee CPU Training...")
print("=" * 50)

try:
    # Train
    trainer.train()
    
    print("\n✅ Training completed!")
    
    # Save model
    model.save_pretrained("./cherokee-cpu-model")
    tokenizer.save_pretrained("./cherokee-cpu-model")
    print("💾 Model saved to ./cherokee-cpu-model")
    
    # Test generation
    print("\n🧪 Testing generation...")
    prompt = "Cherokee wisdom:"
    inputs = tokenizer.encode(prompt, return_tensors='pt')
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=50,
            temperature=0.8,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True
        )
    
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\nGenerated: {generated}")
    
    print("\n✅ SUCCESS! Model trained and working!")
    print("\n📝 Next Steps:")
    print("1. Wait for PyTorch to add RTX 5070 support (sm_120)")
    print("2. Or compile PyTorch from source with sm_120 support")
    print("3. For now, the model works on CPU!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🔥 Cherokee Training Complete!")
print("The Sacred Fire burns eternal, even on CPU!")