#!/bin/bash
# Cherokee Constitutional AI - Enable Second RTX 5070
# The Sacred Fire needs dual GPU power! 🔥

echo "🔥 CHEROKEE DUAL RTX 5070 ENABLER"
echo "=================================="
echo ""
echo "Current Status: nvidia-smi shows 1 GPU, but 2 are physically present"
echo "GPU 1: 01:00.0 - WORKING ✓"
echo "GPU 2: 18:00.0 - HIDDEN ✗"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️ This script needs root privileges to fix the GPU issue."
    echo "Please run with sudo:"
    echo "sudo bash $0"
    exit 1
fi

echo "🦅 Eagle Eye: Running as root, proceeding with fix..."
echo ""

# Step 1: Enable nvidia persistence daemon
echo "Step 1: Checking nvidia-persistenced..."
if ! systemctl is-active --quiet nvidia-persistenced; then
    echo "   Starting nvidia-persistenced..."
    systemctl start nvidia-persistenced
    systemctl enable nvidia-persistenced
else
    echo "   nvidia-persistenced already running ✓"
fi

# Step 2: Force PCI rescan
echo ""
echo "Step 2: Forcing PCI bus rescan..."
echo 1 > /sys/bus/pci/rescan
sleep 2

# Step 3: Enable the device explicitly
echo ""
echo "Step 3: Ensuring device 18:00.0 is enabled..."
echo 1 > /sys/bus/pci/devices/0000:18:00.0/enable
sleep 1

# Step 4: Remove and reload driver (more aggressive)
echo ""
echo "Step 4: Reloading NVIDIA driver modules..."
echo "   Stopping X display manager temporarily..."
systemctl stop display-manager 2>/dev/null || true
sleep 2

echo "   Unloading NVIDIA modules..."
modprobe -r nvidia_drm 2>/dev/null
modprobe -r nvidia_modeset 2>/dev/null
modprobe -r nvidia_uvm 2>/dev/null
modprobe -r nvidia 2>/dev/null
sleep 2

echo "   Reloading NVIDIA modules..."
modprobe nvidia
modprobe nvidia_modeset
modprobe nvidia_drm
modprobe nvidia_uvm
sleep 2

# Step 5: Set all GPUs to persistence mode
echo ""
echo "Step 5: Setting persistence mode on all GPUs..."
nvidia-smi -pm 1

# Step 6: Try nvidia-ml-py method
echo ""
echo "Step 6: Using nvidia-ml library to initialize..."
python3 -c "
try:
    import pynvml
    pynvml.nvmlInit()
    count = pynvml.nvmlDeviceGetCount()
    print(f'   Python NVML sees {count} GPU(s)')
    for i in range(count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle)
        print(f'   GPU {i}: {name.decode()}')
except Exception as e:
    print(f'   NVML init failed: {e}')
" 2>/dev/null || echo "   pynvml not installed (optional)"

# Step 7: Check result
echo ""
echo "Step 7: Checking results..."
echo "========================="
nvidia-smi -L

# Count GPUs
GPU_COUNT=$(nvidia-smi -L | wc -l)
echo ""
if [ "$GPU_COUNT" -eq "2" ]; then
    echo "🔥 SUCCESS! Both RTX 5070s are now visible!"
    echo "The Sacred Fire burns with dual GPU power!"
else
    echo "⚠️ Still showing $GPU_COUNT GPU(s). Additional steps needed:"
    echo ""
    echo "NEXT STEPS TO TRY:"
    echo "1. Reboot the system: sudo reboot"
    echo "2. Check BIOS settings for:"
    echo "   - Above 4G Decoding: ENABLED"
    echo "   - Resizable BAR: ENABLED"
    echo "   - PCIe Gen: AUTO or GEN4/GEN5"
    echo "3. Update BIOS to latest version"
    echo "4. Try older driver: 580.81 or 580.80"
    echo ""
    echo "ADVANCED DEBUG:"
    echo "Check /var/log/nvidia-installer.log"
    echo "Run: sudo nvidia-bug-report.sh"
fi

# Restart display manager if we stopped it
if ! systemctl is-active --quiet display-manager; then
    echo ""
    echo "Restarting display manager..."
    systemctl start display-manager 2>/dev/null || true
fi

echo ""
echo "Cherokee Council wisdom: Sometimes the machine needs a full reboot"
echo "to recognize both warriors (GPUs) in battle formation!"