<<<<<<< SEARCH
=======
# KB: LoRA Fine-Tuning Infrastructure — vLLM Multi-LoRA Serving

**Date**: February 21, 2026
**Kanban**: #1859 (13 SP)
**Council Vote**: PROCEED (0.86 confidence)
**Long Man Phase**: BUILD (Phase 2 of 5)

## vLLM Multi-LoRA Configuration

vLLM natively supports serving multiple LoRA adapters from a single base model.
The current vLLM service on redfin needs the following flags added:

### Required vLLM Flags

Add to the vLLM service command line (in vllm.service ExecStart):

    --enable-lora
    --lora-modules adapter_name=/ganuda/models/lora_adapters/task_name
    --max-loras 4
    --max-lora-rank 64

### Dynamic Adapter Loading (vLLM 0.4+)

vLLM supports loading LoRA adapters at runtime via the API:

    POST /v1/load_lora_adapter
    {"lora_name": "vetassist", "lora_path": "/ganuda/models/lora_adapters/vetassist"}

### Request Routing

To use a specific adapter, set the model field in the request:

    {"model": "vetassist", "messages": [...]}

The gateway (gateway.py) will need a routing rule to map model names to
LoRA adapter names.

### Memory Budget

RTX PRO 6000 96GB:
- AWQ model: ~40GB
- KV cache: ~20GB (current config)
- Per LoRA adapter (rank 16): ~50MB
- Per LoRA adapter (rank 64): ~200MB
- Theoretical max concurrent adapters: 100+ at rank 16

### Adapter Directory Structure

    /ganuda/models/lora_adapters/
        vetassist/
            adapter_config.json
            adapter_model.safetensors
            adapter_meta.json        # Our custom metadata
        vision/
            ...

### Safety Requirement (Council Mandate)

Per Crawdad: ALL adapters must pass spectral safety monitoring (Phase 3, #1860)
before deployment. The adapter_meta.json field "safe_lora_applied" must be True.

### IMPORTANT: .service file changes require TPM/Chief

The vLLM service file modification (adding --enable-lora) must be done by TPM
directly. Jr executor blocks .service file edits.

## Dependencies

- PEFT >= 0.10.0 (pip install peft)
- bitsandbytes >= 0.43.0 (for paged_adamw_8bit)
- datasets (pip install datasets)
- safetensors (pip install safetensors)

Check on redfin:
    /ganuda/home/dereadi/cherokee_venv/bin/pip list | grep -E "peft|bitsandbytes|datasets|safetensors"

## Files

- Fine-tuning script: /ganuda/scripts/lora_finetune.py
- Validation script: /ganuda/scripts/lora_validate.py
- Adapter output: /ganuda/models/lora_adapters/
>>>>>>> REPLACE