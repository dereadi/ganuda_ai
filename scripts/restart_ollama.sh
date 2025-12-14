#!/bin/bash
sudo systemctl start ollama.service
sleep 3
systemctl status ollama.service --no-pager | head -10
nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv
