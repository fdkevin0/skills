# Intel GPU Hardware Reference

> Sources: [Intel Arc Specifications](https://www.intel.com/content/www/us/en/products/details/discrete-gpus/arc.html), [Wikipedia](https://en.wikipedia.org/wiki/Intel_Arc)

## Arc A770 (ACM-G12, Alchemist)

The most common Intel discrete GPU for LLM inference. AOT compilation target: `-device acm-g12`.

| Spec | Value |
|------|-------|
| Xe-cores | 32 |
| XMX engines | 512 (16 per Xe-core) |
| FP32 ALUs | 4096 |
| Execution units | 512 (8 per Xe-core) |
| Memory | 8 GB or 16 GB GDDR6, 256-bit |
| Theoretical BW | 560 GB/s (16 GB model, factory OC; 512 GB/s spec) |
| Measured SYCL copy BW | 456 GB/s (81% of theoretical) |
| Sub-group width | SIMD16 |
| Max workgroup size | 1024 |
| L1 cache | 192 KB per Xe-core |
| L2 cache | 16 MB |
| PCIe | Gen4 ×16 |
| TDP | 225 W |
| Boost clock | 2,400 MHz |
| Process node | TSMC N6 |
| L0 driver | `libze_intel_gpu.so` |
| API support | Vulkan 1.3, OpenCL 3.0, SYCL/DPC++ |

## Arc B580 (BMG-G21, Battlemage)

Second-generation Arc. AOT target: `-device bmg-g21`.

| Spec | Value |
|------|-------|
| Xe-cores | 20 |
| XMX engines | 320 |
| Memory | 12 GB GDDR6, 192-bit |
| Theoretical BW | 456 GB/s |
| PCIe | Gen4 ×8 |
| Sub-group width | SIMD16 |
| L0 driver | `libze_intel_gpu.so` |

## Flex 170 (ATS-M)

Data center inference card. AOT target: `-device ats-m150`.

| Spec | Value |
|------|-------|
| Xe-cores | 32 |
| Memory | 16 GB GDDR6 |
| PCIe | Gen4 ×8 |

## Data Center GPU Max 1550 (PVC, Ponte Vecchio)

HPC/AI accelerator. AOT target: `-device pvc`.

| Spec | Value |
|------|-------|
| Xe-cores | 112 |
| Memory | 128 GB HBM2e |
| Sub-group width | SIMD32 |
| Key difference from Arc | SIMD32 subgroups (vs SIMD16). Affects kernel workgroup sizing. |

> The SIMD32 vs SIMD16 difference is the single largest architectural gap between PVC and Arc — it changes optimal workgroup sizes and sub-group shuffle patterns.
