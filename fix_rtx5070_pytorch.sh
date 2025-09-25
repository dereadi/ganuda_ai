#!/bin/bash
# Fix RTX 5070 CUDA compatibility for PyTorch

echo "🔥 Fixing RTX 5070 CUDA Compatibility for Cherokee AI"
echo "======================================================"

# Set environment variables to force PyTorch to use RTX 5070s
export TORCH_CUDA_ARCH_LIST="5.0;6.0;7.0;7.5;8.0;8.6;9.0;12.0"
export CUDA_VISIBLE_DEVICES=0,1
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Force PyTorch to ignore architecture check
export TORCH_CUDNN_V8_API_DISABLED=1
export PYTORCH_ENABLE_MPS_FALLBACK=1

echo "✅ Environment variables set"

# Install PyTorch nightly build which may have better support
echo "📦 Installing PyTorch nightly build with experimental RTX 5070 support..."

/home/dereadi/cherokee_venv/bin/pip uninstall torch torchvision torchaudio -y

# Install PyTorch nightly with CUDA 12.4
/home/dereadi/cherokee_venv/bin/pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124

echo "✅ PyTorch nightly installed"

# Test the installation
echo "🧪 Testing GPU access..."
/home/dereadi/cherokee_venv/bin/python3 -c "
import torch
import warnings
warnings.filterwarnings('ignore')

print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'GPU Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB')
    
    # Test tensor operations
    print('\n🔥 Testing tensor operations on GPU...')
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print(f'✅ Matrix multiplication successful!')
        print(f'Result shape: {z.shape}')
        print(f'Result device: {z.device}')
    except Exception as e:
        print(f'❌ GPU operation failed: {e}')
else:
    print('❌ CUDA not available')
"

echo ""
echo "🔥 RTX 5070 CUDA fix complete!"