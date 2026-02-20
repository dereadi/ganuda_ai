# VLM Integration Architecture
Cherokee AI Federation - Spider Integration Documentation

## System Overview

```
+-----------------------------------------------------------+
|                SAG Unified Interface                       |
|              (192.168.132.223:4000)                        |
+-----------------------------+-----------------------------+
                              | HTTP/REST
                              v
+-----------------------------------------------------------+
|                    LLM Gateway v1.2                        |
|              (192.168.132.223:8080)                        |
|  +-------------+  +-------------+  +-------------------+   |
|  | Council API |  |  VLM API    |  | Metrics/Logging   |   |
|  +-------------+  +------+------+  +-------------------+   |
+-----------------------------------------------------------+
                           |
                           v
+-----------------------------------------------------------+
|                  VLM Service Layer                         |
|  +----------------+  +----------------+  +-------------+   |
|  | Frame Process  |  | LLaVA-7B Model |  | Security    |   |
|  | (Encryption)   |  | (GPU Inference)|  | Manager     |   |
|  +----------------+  +----------------+  +-------------+   |
+-----------------------------------------------------------+
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
+-------------------+            +----------------------+
| Tribal Vision     |            |    redfin GPU        |
| Frame Storage     |            |   RTX 4090 24GB      |
| /ganuda/data/     |            | (192.168.132.223)    |
+-------------------+            +----------------------+
          |
          v
+-----------------------------------------------------------+
|                  bluefin Database                          |
|               (192.168.132.222)                            |
|  +---------------+  +---------------+  +---------------+   |
|  | vlm_inferences|  | vlm_audit_log |  |thermal_memory |   |
|  +---------------+  +---------------+  +---------------+   |
+-----------------------------------------------------------+
```

## Data Flow

1. **Camera Capture**: Amcrest cameras capture frame on detection
2. **Frame Storage**: Encrypted storage at `/ganuda/data/vision/frames/`
3. **VLM Processing**: Frame sent to VLM service for description
4. **Council Integration**: VLM output feeds specialist analysis
5. **Audit Logging**: All operations logged to bluefin
6. **Alert Generation**: Anomalies trigger alerts via configured channels

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/vlm/describe` | POST | Get scene description |
| `/v1/vlm/analyze` | POST | Anomaly analysis |
| `/v1/vlm/ask` | POST | Question answering |
| `/v1/vlm/health` | GET | Service health |
| `/v1/vlm/metrics` | GET | Prometheus metrics |

## Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| transformers | 4.36+ | Model loading |
| torch | 2.1+ | GPU inference |
| Pillow | 10.0+ | Image processing |
| cryptography | 41.0+ | Frame encryption |
| prometheus_client | 0.19+ | Observability |

## Security Layers

1. **Transport**: TLS 1.3 for all frame transfers
2. **Storage**: AES-256 encryption at rest
3. **Access**: API key + role-based access control
4. **Audit**: Full logging to JSONL

---
*Cherokee AI Federation*
