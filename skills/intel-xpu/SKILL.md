---
name: intel-xpu
description: >-
  Write, optimize, or port Intel XPU GPU workloads using SYCL/DPC++, Level
  Zero, or PyTorch torch.xpu (Arc, Flex, Data Center GPU Max). Use when
  building or tuning SYCL/ggml-sycl kernels, configuring oneAPI/Level Zero
  runtimes, or porting CUDA code to torch.xpu.
---

# Intel XPU — SYCL, `torch.xpu`, and Level Zero

Apply core hardware invariants across Arc (A770/A750/B580), Flex 170, and Data Center GPU Max 1550 workloads, and load only the reference file matching the active toolchain.

## Core Hardware & Runtime Invariants

- **Memory-bound**: Arc decode is gated by VRAM bandwidth (456 GB/s measured copy on A770); minimize bytes-per-token and fuse adjacent element-wise ops before tuning ALU throughput.
- **Coalesced**: Contiguous loads across neighboring SIMD lanes are mandatory (strided access drops bandwidth 2.1×); Arc uses **SIMD16** sub-groups vs. **SIMD32** on PVC Max 1550 (`GGML_SYCL_WARP_SIZE`).
- **Deterministic USM & L0**: Prefer explicit `sycl::malloc_device` + `memcpy` over page-faulting `malloc_shared`; round `nd_range` global sizes to multiples of local workgroup size (256 sweet spot for matvec); set `SYCL_UR_USE_LEVEL_ZERO_V2=1` on Arc (~9 µs → ~4.5 µs launch floor); route multi-GPU peer copies via Level Zero (`q.memcpy` between peer USM pointers is a silent no-op).
- **Toolchain baseline**: Use upstream `torch.xpu` (PyTorch 2.4+) for PyTorch workloads; `ipex-llm` was archived in January 2026.

## Reference Router

- [references/sycl-kernels-and-build.md](./references/sycl-kernels-and-build.md) — SYCL/CMake/AOT flags, `nd_range` & SIMD16 kernel patterns, coalesced matvec, fusion, Vulkan gap analysis, Level Zero interop, and `llama.cpp` SYCL quick-start.
- [references/env-vars.md](./references/env-vars.md) — `GGML_SYCL_*`, `SYCL_UR_*`, and Level Zero runtime flags.
- [references/memory-model.md](./references/memory-model.md) — USM tiers, VMM/legacy/host pools, >4 GiB allocations, and peer-to-peer copy rules.
- [references/hardware.md](./references/hardware.md) — Arc A770, Arc B580, Flex 170, and Data Center GPU Max 1550 hardware specs.
- [references/torch-xpu.md](./references/torch-xpu.md) — `torch.xpu` setup, CUDA-to-XPU porting table, and XMX/BF16 limits.
- [references/ipex-llm.md](./references/ipex-llm.md) — Archived IPEX-LLM portability notes (FP8 KV cache, ESIMD).
