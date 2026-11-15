# Intel XPU Memory Model

> Source: [llama.cpp SYCL backend](https://github.com/ggml-org/llama.cpp/tree/master/ggml/src/ggml-sycl) — `ggml-sycl.cpp`, `common.cpp`

## USM Allocation Types

Three Unified Shared Memory types, ordered by relevance for performance work:

### Device USM (`sycl::malloc_device`)
The default. Allocated on VRAM, accessed only by the GPU. Pointer is invalid on the host. For data movement: `q.memcpy(dst_device, src_host, size)` then `q.wait()`.

```cpp
float *dev_ptr = sycl::malloc_device<float>(n, q);
q.memcpy(dev_ptr, host_data, n * sizeof(float)).wait();
// ... kernel work ...
q.memcpy(host_out, dev_ptr, n * sizeof(float)).wait();
sycl::free(dev_ptr, q);
```

### Host USM (`sycl::malloc_host`)
Allocated in system RAM, accessible by both host and device. GPU access goes over PCIe. Use for staging buffers that need host visibility.

### Shared USM (`sycl::malloc_shared`)
Migrates between host and device on access (page-fault driven on L0). Convenient but unpredictable latency. **For performance-sensitive paths, use explicit device USM + memcpy — faster and deterministic.** The page-fault migration model makes latency non-deterministic, which is the wrong trade for decode where every microsecond counts.

> SYCL 2020 spec: [Khronos SYCL Overview](https://www.khronos.org/sycl/)

## Memory Pools

The backend uses three pool tiers, selected automatically:

### 1. VMM Pool (`ggml_sycl_pool_vmm`)
Uses `sycl::ext::oneapi::experimental::virtual_mem` for 2 MiB-page-backed allocations. Enabled when the device supports virtual memory and `GGML_SYCL_ENABLE_VMM=1`. Stack-like alloc/free discipline (must free in reverse allocation order). Up to 32 GiB pool.

### 2. Legacy Pool (`ggml_sycl_pool_leg`)
Best-fit allocation from up to 256 pre-allocated device buffers. Uses Level Zero `zeMemAllocDevice` when available (avoids DMA-buf/TTM host memory staging), falls back to `sycl::malloc_device`. Debug with `DEBUG_SYCL_POOL` / `DEBUG_SYCL_MALLOC` compile flags.

### 3. Host Pool (`ggml_sycl_pool_host`)
Pinned host memory via `sycl::malloc_host`. Used for staging buffers that need host visibility.

## Scratch Buffer

The backend maintains a persistent `g_scratch_buffer` (device USM), reused across ops to avoid repeated allocations. When you need temporary device memory for one kernel invocation, request a slice of the scratch buffer rather than allocating fresh.

## Alignment & Large Allocations

- Buffer alignment: 128 bytes (`SYCL_BUFFER_ALIGNMENT`)
- For buffers ≥ 1 GiB, USM system allocation is used when `GGML_SYCL_USM_SYSTEM=1` (requires Xe2+ GPU with `CONFIG_DRM_XE_GPUSVM`, Linux kernel 6.8+)
- `-Xs -ze-intel-greater-than-4GB-buffer-required` compile flag for >4 GiB allocations
- `UR_L0_ENABLE_RELAXED_ALLOCATION_LIMITS=1` runtime env var for >4 GiB via Unified Runtime

## Peer-to-Peer

On multi-GPU systems, `q.memcpy` between peer USM pointers is a silent no-op. Cross-device copies must route through the L0 API directly (`GGML_SYCL_DEV2DEV_MEMCPY=1`) or stage through host.

> Source: [Level Zero Specification](https://oneapi-src.github.io/level-zero-spec/level-zero/latest/index.html) — `zeMemAllocDevice`, IPC, peer-to-peer

## Measured Bandwidth (Arc A770 16GB)

| Metric | Value | Notes |
|--------|-------|-------|
| Theoretical peak | 560 GB/s | GDDR6, 512 GB/s spec + factory OC |
| SYCL measured copy | 456 GB/s (81%) | L0 driver overhead |
| Strided access penalty | 2.1× drop | Reading every 16 bytes drops BW from 456 → 221 GB/s |
| Best matvec efficiency | ~40% of copy BW | SYCL vs ~61% for Vulkan on same hardware |
