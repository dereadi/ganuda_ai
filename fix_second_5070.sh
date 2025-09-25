#!/bin/bash
# Cherokee Constitutional AI - Fix Second RTX 5070 Detection
# Sacred Fire burns eternal through dual GPU power! 🔥

echo "🔥 Cherokee Council GPU Fix - Detecting Second RTX 5070"
echo "=================================================="
echo ""

# Check current status
echo "Current GPU Detection Status:"
echo "-----------------------------"
nvidia-smi -L
echo ""

echo "PCI Devices Found:"
echo "------------------"
lspci | grep -E 'NVIDIA.*2f04'
echo ""

# The second GPU is at 18:00.0 but not being recognized
echo "🦅 Eagle Eye sees: Two RTX 5070s detected at hardware level"
echo "🐺 Coyote says: Driver only loading first one"
echo "🐢 Turtle advises: Patient systematic approach"
echo ""

echo "Attempting Fix Solutions:"
echo "========================"

# Solution 1: Try to manually bind the device
echo ""
echo "1. Checking if nvidia driver is bound to second GPU..."
ls -la /sys/bus/pci/devices/0000:18:00.0/ 2>/dev/null | grep driver

# Solution 2: Force rescan of PCI bus
echo ""
echo "2. Requesting PCI bus rescan (requires root)..."
echo "   Run: sudo sh -c 'echo 1 > /sys/bus/pci/rescan'"

# Solution 3: Check if device is disabled
echo ""
echo "3. Checking device enable status..."
if [ -f /sys/bus/pci/devices/0000:18:00.0/enable ]; then
    cat /sys/bus/pci/devices/0000:18:00.0/enable
    echo "   If 0, run: sudo sh -c 'echo 1 > /sys/bus/pci/devices/0000:18:00.0/enable'"
fi

# Solution 4: Remove and reprobe
echo ""
echo "4. To force driver reprobe (requires root):"
echo "   sudo modprobe -r nvidia_drm nvidia_modeset nvidia"
echo "   sudo modprobe nvidia"
echo "   sudo modprobe nvidia_modeset"
echo "   sudo modprobe nvidia_drm"

# Solution 5: Check IOMMU/VFIO conflicts
echo ""
echo "5. Checking for IOMMU/VFIO conflicts..."
lspci -nnk -d 10de:2f04 | grep -A 3 "18:00.0"

# Solution 6: nvidia-xconfig
echo ""
echo "6. Generate new xorg config with both GPUs:"
echo "   sudo nvidia-xconfig --enable-all-gpus"

echo ""
echo "🔥 RECOMMENDED IMMEDIATE ACTION:"
echo "================================"
echo "1. First try: sudo sh -c 'echo 1 > /sys/bus/pci/rescan'"
echo "2. If that doesn't work, reload the driver modules"
echo "3. Check 'nvidia-smi' after each step"
echo ""
echo "The Sacred Fire needs both GPUs burning!"