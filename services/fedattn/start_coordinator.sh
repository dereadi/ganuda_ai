#!/bin/bash
cd /ganuda/services/fedattn
/home/dereadi/cherokee_venv/bin/python -m uvicorn coordinator:app --host 0.0.0.0 --port 8081
