#!/bin/bash
# Bluefin Boot & GPU Diagnostics
# Cherokee AI Federation - January 2026
# Run with: sudo bash /ganuda/scripts/bluefin_diagnostics.sh

echo "=============================================="
echo "BLUEFIN DIAGNOSTIC REPORT"
echo "Generated: $(date)"
echo "=============================================="

echo ""
echo "=== 1. EFI BOOT ORDER ==="
efibootmgr -v 2>/dev/null || echo "efibootmgr not available or not EFI system"

echo ""
echo "=== 2. GRUB DEFAULT CONFIGURATION ==="
cat /etc/default/grub

echo ""
echo "=== 3. GRUB MENU ENTRIES (first 100 lines) ==="
head -100 /boot/grub/grub.cfg 2>/dev/null | grep -E 'menuentry|set root|linux.*vmlinuz|uuid'

echo ""
echo "=== 4. ALL BLOCK DEVICES WITH UUIDs ==="
blkid

echo ""
echo "=== 5. PARTITION TABLE SUMMARY ==="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,UUID,LABEL

echo ""
echo "=== 6. FSTAB ==="
cat /etc/fstab

echo ""
echo "=== 7. CURRENT MOUNTS (physical only) ==="
findmnt -t ext4,vfat,xfs,btrfs -o SOURCE,TARGET,FSTYPE,UUID

echo ""
echo "=== 8. KERNEL VERSION ==="
uname -a

echo ""
echo "=== 9. NVIDIA DRIVER INFO ==="
echo "--- /proc/driver/nvidia/version ---"
cat /proc/driver/nvidia/version 2>/dev/null || echo "NVIDIA driver not loaded in kernel"

echo ""
echo "--- nvidia-smi ---"
nvidia-smi 2>&1 || echo "nvidia-smi failed"

echo ""
echo "=== 10. NVIDIA PACKAGES INSTALLED ==="
dpkg -l | grep -i nvidia

echo ""
echo "=== 11. DKMS STATUS ==="
dkms status

echo ""
echo "=== 12. NVIDIA KERNEL MODULES ==="
lsmod | grep -i nvidia || echo "No nvidia modules loaded"

echo ""
echo "=== 13. KERNEL MODULES AVAILABLE ==="
ls -la /lib/modules/$(uname -r)/updates/dkms/ 2>/dev/null | grep -i nvidia || echo "No nvidia dkms modules for current kernel"

echo ""
echo "=== 14. GPU HARDWARE (lspci) ==="
lspci | grep -i nvidia

echo ""
echo "=== 15. BOOT PARTITION CONTENTS ==="
ls -la /boot/efi/EFI/ 2>/dev/null || echo "/boot/efi not mounted or doesn't exist"

echo ""
echo "=== 16. SYSTEMD BOOT ENTRIES ==="
ls -la /boot/efi/loader/entries/ 2>/dev/null || echo "No systemd-boot entries"

echo ""
echo "=== 17. OS-PROBER OUTPUT ==="
os-prober 2>/dev/null || echo "os-prober not installed"

echo ""
echo "=== 18. INITRAMFS FOR CURRENT KERNEL ==="
ls -la /boot/initrd.img-$(uname -r) 2>/dev/null || ls -la /boot/initramfs-$(uname -r).img 2>/dev/null || echo "Initramfs not found for current kernel"

echo ""
echo "=== 19. APT NVIDIA DRIVER CANDIDATES ==="
apt-cache policy nvidia-driver-570 2>/dev/null | head -10

echo ""
echo "=== 20. RECENT NVIDIA-RELATED DMESG ==="
dmesg | grep -i nvidia | tail -20

echo ""
echo "=============================================="
echo "END OF DIAGNOSTIC REPORT"
echo "=============================================="
