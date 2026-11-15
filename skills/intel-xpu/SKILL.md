---
name: intel-xpu
description: Intel XPU GPU programming reference — SYCL/DPC++, torch-xpu, IPEX-LLM.
disable-model-invocation: true
---

# Intel XPU — SYCL, torch-xpu, IPEX-LLM

Reference for programming Intel discrete GPUs (Arc A770/A750/B580, Flex 170, Data Center GPU Max 1550). Three toolchains, one hardware target.

When using this skill, apply every section relevant to the current task: build config, memory model, kernel patterns, and performance constraints. Skip only the toolchain or GPU family not in use.

Sources: [llama.cpp SYCL backend](https://github.com/ggml-org/llama.cpp/tree/master/ggml/src/ggml-sycl) · [SYCL backend docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md) · [Intel oneAPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html) · [PyTorch XPU](https://pytorch.org/docs/stable/notes/xpu.html) · [Level Zero spec](https://oneapi-src.github.io/level-zero-spec/level-zero/latest/index.html) · [IPEX-LLM (archived)](https://github.com/intel/ipex-llm) · [Khronos SYCL](https://www.khronos.org/sycl/)

## Guiding constraints

Three invariants for Intel GPU programming. They anchor every decision below:

- **Memory-bound** — decode on Arc is gated by VRAM bandwidth, not compute. Optimize data movement first; ALU efficiency is secondary. Kernel throughput gains that don't reduce bytes-read-per-token are invisible end-to-end.
- **Coalesced** — the single highest-impact kernel optimization. Contiguous memory access patterns (loading neighboring bytes in neighboring lanes) determine whether you hit the measured 456 GB/s or the strided 221 GB/s.
- **Deterministic** — explicit device USM + `memcpy` beats shared USM page-fault migration for performance paths. Predictable latency wins over convenience.

## SYCL / DPC++

Intel's native GPU programming model. Compiler: `icpx` (oneAPI) or `clang++ -fsycl` (open-source).

### Build setup

```bash
source /opt/intel/oneapi/setvars.sh --force
cmake -B build -DGGML_SYCL=ON -DCMAKE_CXX_COMPILER=icpx
```

Key CMake flags (from `ggml/src/ggml-sycl/CMakeLists.txt`):

| Option | Effect |
|--------|--------|
| `GGML_SYCL=ON` | Enable SYCL backend |
| `GGML_SYCL_F16=ON` | Use `sycl::half` for dequant math (faster on Arc) |
| `GGML_SYCL_GRAPH=ON` | SYCL graph recording (experimental; defaults OFF upstream) |
| `GGML_SYCL_DNN=ON` | Link oneDNN for matrix multiplication |
| `GGML_SYCL_DEVICE_ARCH` | AOT compile for specific target (e.g. `acm-g12`, `pvc`) |
| `GGML_SYCL_TARGET=INTEL` | Target Intel GPUs (sets warp_size=16) |
| `GGML_SYCL_HOST_MEM_FALLBACK=ON` | Host memory fallback on device OOM (kernel 6.8+) |
| `GGML_SYCL_SUPPORT_LEVEL_ZERO_API=ON` | Level Zero API for direct device allocation |

Compile flags:
- `-fsycl` — bare minimum SYCL enable
- `-fsycl-targets=spir64_gen -Xsycl-target-backend=spir64_gen "-device acm-g12"` — AOT for Arc A-series
- `-Xs -ze-intel-greater-than-4GB-buffer-required` — enable >4 GB allocations

### Environment variables

Full reference: [`references/env-vars.md`](references/env-vars.md).

**The single highest-impact setting** for Arc A-series is `SYCL_UR_USE_LEVEL_ZERO_V2=1`. On A770 it halves the kernel launch floor (~9 µs → ~4.5 µs), which matters for decode where kernels are tiny.

Quick-set for best runtime:
```bash
export SYCL_UR_USE_LEVEL_ZERO_V2=1
export SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
export SYCL_CACHE_PERSISTENT=1
export GGML_SYCL_DEBUG=1  # when debugging kernel launches
```

### Memory management

Full reference: [`references/memory-model.md`](references/memory-model.md).

Three USM allocation types, in order of relevance:

- **Device USM** (`sycl::malloc_device`) — VRAM, GPU-only. The default. Data movement via `q.memcpy` + `q.wait()`. **Deterministic** latency.
- **Host USM** (`sycl::malloc_host`) — system RAM, both sides. GPU access over PCIe. For staging buffers needing host visibility.
- **Shared USM** (`sycl::malloc_shared`) — migrates on access via page faults. For performance paths, use explicit device USM + memcpy instead — **deterministic** latency beats page-fault unpredictability.

**Scratch buffer** — persistent `g_scratch_buffer` (device USM), reused across ops. Request a slice for temporary device memory rather than allocating fresh.

**Memory pools** — three tiers, auto-selected: VMM (2 MiB-page-backed, stack discipline, ≤32 GiB), legacy (best-fit from 256 pre-allocated buffers, L0 `zeMemAllocDevice` when available), host (pinned, for staging).

**Peer-to-peer** — `q.memcpy` between peer USM pointers is a silent no-op. Cross-device copies route through L0 directly (`GGML_SYCL_DEV2DEV_MEMCPY=1`) or stage through host.

### Kernel patterns

Three patterns that appear in every performance-sensitive kernel.

**nd_range and workgroup sizing.** Intel GPU requires global size to be a multiple of local size. Non-uniform workgroups fail with a cryptic L0 error:

```cpp
static int round_up_wg(int n, int wg_size) {
    return ((n + wg_size - 1) / wg_size) * wg_size;
}
int wg_size = 256;  // sweet spot for matvec
sycl::range<3> global(round_up_wg(nrows, wg_size), 1, 1);
sycl::range<3> local(wg_size, 1, 1);
q.parallel_for(sycl::nd_range<3>(global, local), [=](sycl::nd_item<3> item) {
    // ...
});
```

**Sub-group (warp) operations.** Arc uses SIMD16 sub-groups (`WARP_SIZE=16` via `GGML_SYCL_WARP_SIZE`). This is a hardware constant:

```cpp
auto sg = item.get_sub_group();
const int sg_size = sg.get_group_linear_range();  // 16 on Arc, 32 on PVC
const int sg_id   = sg.get_group_linear_id();
const int row     = workgroup_id * sg_size + sg_id;

float sum = sycl::reduce_over_group(sg, partial_sum, std::plus<>());
if (sg.leader()) {
    dst[row] = sum;  // one write per sub-group
}
```

Key sub-group API: `get_group_linear_range()` (SIMD width), `get_group_linear_id()` (sub-group index in workgroup), `get_local_linear_id()` (lane index), `leader()` (lane 0), `reduce_over_group()`, `shift_group_left/right()`.

**Coalesced quantized matvec** — the inner loop of `mmvq.cpp`. The single most impactful kernel optimization on Arc:

```cpp
// Thread N handles row N. Each row: load weights once, accumulate dot products.
for (int i = sg_start; i < blocks_per_row; i += sg_stride) {
    const auto bx_offset = block_type::get_block_offset(ibx, nblocks);
    const auto d_offset  = block_type::get_d_offset(nrows, ncols, ibx);
    partial_sum += vec_dot(vx, bx_offset, d_offset, q8_1_ptr, q8_1_ds_ptr, iqs);
}
auto sum = sycl::reduce_over_group(sg, partial_sum, std::plus<>());
```

**Coalesced** weight loads (contiguous bytes in neighboring lanes) improved Q4_K kernel throughput by 21% and end-to-end decode by 11%. The pattern: load neighboring bytes in neighboring SIMD lanes; avoid strided access which drops bandwidth 2.1×.

**Element-wise fusion** — fuse adjacent element-wise ops into one kernel to avoid VRAM round-trips. Each saves ~3 memory round-trips per token:

| Fusion | Saves | Used in |
|--------|-------|---------|
| SiLU+MUL | 1 read + 1 write | SwiGLU FFN |
| ADD+MUL | 1 read + 1 write | Residual scaling |
| RMS_NORM+MUL | 1 read + 1 write | Attention norm |

### Performance constraints (Arc A770)

> Full GPU specs: [`references/hardware.md`](references/hardware.md)

| Constraint | Value | Implication |
|-----------|-------|-------------|
| Measured copy BW | 456 GB/s (81% of peak) | **Memory-bound** — bytes-per-token is the ceiling |
| Strided access | 2.1× BW drop | **Coalesced** loads are mandatory |
| Kernel launch floor | ~9 µs (L0 v1), ~4.5 µs (L0 v2) | `SYCL_UR_USE_LEVEL_ZERO_V2=1` is essential |
| Sub-group width | SIMD16 | Half Vulkan's SIMD32 — the primary Vulkan gap |
| Matvec efficiency | ~40% of copy BW | SYCL vs ~61% Vulkan on same hardware |
| Workgroup sweet spot | 256 | Max is 1024, but 256 is typical for matvec |

**The Vulkan gap** — on identical A770 hardware, Vulkan decode is ~1.2× faster than SYCL. Root causes, in order of impact:

1. **SIMD32 vs SIMD16** — Vulkan's 32-lane subgroups double cache line coverage for the same workgroup count
2. **Compiler codegen** — Mesa GLSL→SPIR-V generates tighter instruction schedules than Intel's SYCL compiler for quantized dot-product loops
3. **Driver dispatch** — Vulkan command buffers have lower per-dispatch overhead than SYCL in-order queues

These are compiler/driver/architecture differences — not fixable in SYCL source.

### L0 interop

When bypassing SYCL for direct Level Zero API access (device-to-device copies, VMM):

```cpp
#include <level_zero/ze_api.h>
ze_device_handle_t ze_dev = sycl::get_native<sycl::backend::ext_oneapi_level_zero>(sycl_dev);
ze_context_handle_t ze_ctx = sycl::get_native<sycl::backend::ext_oneapi_level_zero>(sycl_ctx);
```

Build with `-DGGML_SYCL_SUPPORT_LEVEL_ZERO_API=ON`, link `ze_loader`.

## torch-xpu

PyTorch with Intel GPU backend. Same API surface as CUDA; substitutes `.cuda()` → `.xpu()`.

> Source: [PyTorch XPU docs](https://pytorch.org/docs/stable/notes/xpu.html) · [Intel Extension for PyTorch](https://intel.github.io/intel-extension-for-pytorch/)

### Installation

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu
```

Minimum: PyTorch 2.4+ (XPU backend moved from `intel_extension_for_pytorch` into upstream). For 2.3 and earlier, use IPEX directly.

### Usage

```python
import torch
assert torch.xpu.is_available()
model = model.to('xpu')
tensor = tensor.to('xpu')
# Same API as CUDA: .xpu(), loss.backward(), optimizer.step()
```

### Porting from CUDA

Mechanical substitution — `cuda` → `xpu`:

| CUDA | XPU |
|------|-----|
| `torch.cuda.is_available()` | `torch.xpu.is_available()` |
| `tensor.cuda()` | `tensor.xpu()` |
| `torch.cuda.synchronize()` | `torch.xpu.synchronize()` |
| `torch.cuda.amp.autocast()` | `torch.xpu.amp.autocast()` |
| `torch.cuda.empty_cache()` | `torch.xpu.empty_cache()` |
| `torch.cuda.Stream()` | `torch.xpu.Stream()` |
| `torch.cuda.max_memory_allocated()` | `torch.xpu.max_memory_allocated()` |

Custom CUDA kernels need rewriting: `__global__` / `__device__` → SYCL `parallel_for` / device functions. Use `torch.xpu.optimize_for_inference()` for graph-capture (analogous to `torch.cuda.graph()`).

### Known limits

- **No explicit XMX exposure** — Arc GPUs have 512 XMX systolic arrays (16 per Xe-core × 32 cores) but PyTorch XPU routes matmul through oneDNN, which auto-selects XMX based on shapes and quant types.
- **BF16 matmul** — Arc A770 achieves ~269 GB/s effective BW with BF16 on Vulkan; XPU path is slower (~182 GB/s). The gap is kernel codegen, not hardware.
- **Multi-GPU** — `torch.xpu.device_count()` + `torch.nn.DataParallel`, similar to CUDA. Peer-to-peer uses L0 IPC.

## IPEX-LLM (ARCHIVED)

> Full reference: [`references/ipex-llm.md`](references/ipex-llm.md)

Intel Extension for PyTorch — LLMs. **Archived January 28, 2026.** Its functionality has been absorbed into upstream `torch.xpu` (PyTorch 2.4+) and other Intel projects.

Key takeaway for current work: **FP8 KV cache** is the most actionable remaining optimization from IPEX-LLM — portable to the SYCL backend if FP8 quant types are added to llama.cpp's type system, reducing KV cache memory traffic 2× vs BF16.

For new projects, use `torch.xpu` directly. Reference IPEX-LLM source only for studying ESIMD kernel patterns and quantization schemes.

## Quick-start cheatsheet

```bash
# Build llama.cpp with SYCL
source /opt/intel/oneapi/setvars.sh --force
cmake -B build-sycl \
  -DGGML_SYCL=ON -DGGML_SYCL_F16=ON \
  -DGGML_SYCL_GRAPH=ON -DGGML_SYCL_DNN=ON \
  -DCMAKE_CXX_COMPILER=icpx
cmake --build build-sycl -j$(nproc)

# Best runtime config (Arc A-series)
export SYCL_UR_USE_LEVEL_ZERO_V2=1
export GGML_SYCL_DISABLE_GRAPH=0
./build-sycl/bin/llama-cli -m model.gguf -ngl 99

# List SYCL devices
./build-sycl/bin/llama-ls-sycl-device

# torch-xpu quick test
python3 -c "import torch; print(torch.xpu.is_available()); print(torch.xpu.get_device_name(0))"
```
