"""
VLM Performance Metrics
Cherokee AI Federation - Addressing Gecko Performance Concerns
"""

import time
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge

VLM_INFERENCE_DURATION = Histogram(
    "vlm_inference_duration_seconds",
    "Time spent on VLM inference",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

VLM_INFERENCE_COUNT = Counter(
    "vlm_inference_total",
    "Total VLM inferences",
    ["camera_id", "inference_type"]
)

VLM_GPU_MEMORY = Gauge(
    "vlm_gpu_memory_bytes",
    "GPU memory used by VLM"
)

VLM_ERROR_COUNT = Counter(
    "vlm_errors_total",
    "VLM inference errors",
    ["error_type"]
)

VLM_QUEUE_SIZE = Gauge(
    "vlm_queue_size",
    "Number of frames waiting for VLM processing"
)


def measure_inference(func):
    """Decorator to measure inference time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            VLM_INFERENCE_DURATION.observe(duration)
            return result
        except Exception as e:
            VLM_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
    return wrapper