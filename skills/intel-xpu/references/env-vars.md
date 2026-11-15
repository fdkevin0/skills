# Intel XPU Environment Variables

> Source: [llama.cpp SYCL Backend Docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md)

## GGML_SYCL Namespace

Runtime behaviour, parsed at init:

| Variable | Default | Effect |
|----------|---------|--------|
| `GGML_SYCL_DEBUG` | 0 | Print kernel launch logs to stderr |
| `GGML_SYCL_DISABLE_OPT` | 0 | Disable kernel-level optimizations (use `GGML_SYCL_ENABLE_OPT=0` in newer builds) |
| `GGML_SYCL_DISABLE_GRAPH` | 1 | SYCL graph recording (0=enabled, 1=disabled). Default OFF — still in development |
| `GGML_SYCL_DISABLE_DNN` | 0 | Skip oneDNN matmul |
| `GGML_SYCL_DISABLE_FUSION` | 0 | Disable element-wise + multi-MM fusion |
| `GGML_SYCL_ENABLE_VMM` | 1 | Virtual memory management (L0) |
| `GGML_SYCL_ENABLE_FLASH_ATTN` | 1 | Flash attention kernel (added March 2026) |
| `GGML_SYCL_PRIORITIZE_DMMV` | 0 | Prefer dequant+matvec over batched matmul |
| `GGML_SYCL_USM_SYSTEM` | 0 | Use system-allocated USM (slower, more capacity; Xe2+ only, kernel 6.8+) |
| `GGML_SYCL_DEV2DEV_MEMCPY` | 0 | Cross-device copy strategy (0=SYCL, 1=L0 direct) |
| `GGML_SYCL_USE_LEVEL_ZERO_API` | 1 | Bootstrap devices via L0 API — reduces system RAM by avoiding DMA-buf staging |
| `GGML_SYCL_USE_ASYNC_MEM_OP` | 1 | Asynchronous memory operations (memcpy, fill) |
| `GGML_SYCL_NO_PINNED` | (unset) | If set, skip pinned host memory allocation |

## SYCL / oneAPI Namespace

Driver-level, set before launch:

```bash
export SYCL_UR_USE_LEVEL_ZERO_V2=1   # Halves kernel launch floor on Arc (~9 → ~4.5 µs)
export SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1  # Bypass command batching
export SYCL_CACHE_PERSISTENT=1       # Cache JIT kernels to disk
export UR_L0_IN_ORDER_QUEUE_BYPASS=1 # Skip in-order queue serialization
```

**`SYCL_UR_USE_LEVEL_ZERO_V2=1` is the single highest-impact env var for Arc A-series.** On A770 it halves the kernel launch floor, which matters for decode where kernels are tiny.

> Source: [Intel oneAPI Level Zero](https://oneapi-src.github.io/level-zero-spec/level-zero/latest/index.html)

## Device Selection & Memory Limits

```bash
export ONEAPI_DEVICE_SELECTOR="level_zero:0"           # Select specific GPU
export UR_L0_ENABLE_RELAXED_ALLOCATION_LIMITS=1        # Allow >4 GiB allocations via Unified Runtime
export ZES_ENABLE_SYSMAN=1                             # Enable sysmon for free-memory queries
```

## Debug & Precision

```bash
export GGML_SYCL_DEBUG=1                               # Kernel launch logging
export SYCL_PROGRAM_COMPILE_OPTIONS="-cl-fp32-correctly-rounded-divide-sqrt"  # Precision fix
```
