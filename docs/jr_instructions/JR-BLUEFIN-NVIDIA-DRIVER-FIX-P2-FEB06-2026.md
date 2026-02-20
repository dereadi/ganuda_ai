# JR-BLUEFIN-NVIDIA-DRIVER-FIX-P2-FEB06-2026

## Priority: P2 (Infrastructure)
## Assigned Specialist: Infrastructure Jr.
## Date: February 6, 2026

---

## 1. Context

Task 597 (Bluefin Hardware Probe) failed with:
```
Failed to initialize NVML: Driver/library version mismatch
NVML library version: 570.211
```

This indicates the NVIDIA driver and NVML library are out of sync on bluefin.

## 2. Objective

Fix the NVIDIA driver/library mismatch on bluefin (192.168.132.222) to enable GPU monitoring and future RTX 6000 upgrade feasibility testing.

## 3. Diagnostic Steps

### Step 1: Check current driver version
```bash
cat /proc/driver/nvidia/version
```

### Step 2: Check installed NVIDIA packages
```bash
dpkg -l | grep nvidia
# or
rpm -qa | grep nvidia
```

### Step 3: Check NVML library version
```bash
ls -la /usr/lib/x86_64-linux-gnu/libnvidia-ml.so*
# or
ldconfig -p | grep libnvidia-ml
```

### Step 4: Check if nvidia-smi works
```bash
nvidia-smi
```

## 4. Common Fixes

### Option A: Reboot (if driver was recently updated)
```bash
sudo reboot
```

### Option B: Reinstall matching driver
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install --reinstall nvidia-driver-570

# Or use the NVIDIA installer
sudo /usr/bin/nvidia-uninstall
sudo sh NVIDIA-Linux-x86_64-570.xxx.run
```

### Option C: Update to latest driver
```bash
# Check available versions
apt-cache search nvidia-driver

# Install latest
sudo apt install nvidia-driver-535  # or current stable
```

### Option D: Fix library path
```bash
# Ensure correct library is in path
sudo ldconfig
```

## 5. Post-Fix Verification

```bash
# All should work without errors
nvidia-smi
python3 -c "import pynvml; pynvml.nvmlInit(); print('NVML OK')"
```

## 6. GPU Inventory (for reference)

Once fixed, document the GPU configuration:
```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

## 7. If No GPU Present

If bluefin doesn't have an NVIDIA GPU, Task 597 should be reassigned to a GPU-equipped node (redfin has RTX 5090).

Check GPU presence:
```bash
lspci | grep -i nvidia
```

## 8. Blockers

This task requires:
- SSH access to bluefin as root/sudo user
- Potential reboot window
- Knowledge of current GPU hardware

## For Seven Generations

Reliable infrastructure enables reliable AI. Fixing driver mismatches ensures our compute resources serve future generations.
