# PyTorch `torch-xpu` Reference

> Sources: [PyTorch XPU docs](https://pytorch.org/docs/stable/notes/xpu.html) · [Intel Extension for PyTorch](https://intel.github.io/intel-extension-for-pytorch/)

PyTorch with Intel GPU backend. Same API surface as CUDA; substitutes `.cuda()` → `.xpu()`.

## Installation

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu
```

Minimum: PyTorch 2.4+ (XPU backend moved from `intel_extension_for_pytorch` into upstream). For 2.3 and earlier, use IPEX directly.

## Usage

```python
import torch
assert torch.xpu.is_available()
model = model.to('xpu')
tensor = tensor.to('xpu')
# Same API as CUDA: .xpu(), loss.backward(), optimizer.step()
```

Quick check:
```bash
python3 -c "import torch; print(torch.xpu.is_available()); print(torch.xpu.get_device_name(0))"
```

## Porting from CUDA

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

## Known Limits

- **No explicit XMX exposure** — Arc GPUs have 512 XMX systolic arrays (16 per Xe-core × 32 cores) but PyTorch XPU routes matmul through oneDNN, which auto-selects XMX based on shapes and quant types.
- **BF16 matmul** — Arc A770 achieves ~269 GB/s effective BW with BF16 on Vulkan; XPU path is slower (~182 GB/s). The gap is kernel codegen, not hardware.
- **Multi-GPU** — `torch.xpu.device_count()` + `torch.nn.DataParallel`, similar to CUDA. Peer-to-peer uses L0 IPC.
