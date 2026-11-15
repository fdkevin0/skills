# IPEX-LLM (ARCHIVED)

> Source: [intel/ipex-llm on GitHub](https://github.com/intel/ipex-llm) — archived January 28, 2026

**This project is archived and read-only.** Intel will not provide development or support. Patches are no longer accepted. The repository has known security issues.

## What It Was

IPEX-LLM (Intel® LLM Library for PyTorch, formerly `bigdl-llm`) was an LLM acceleration library for Intel GPU, NPU, and CPU. It integrated with Ollama, llama.cpp, vLLM, HuggingFace Transformers, LangChain, and other tools.

### Key Features

- **Low-bit quantization** — INT4/INT8/FP8/FP6/FP4 weight-only quantization, plus experimental INT2 via llama.cpp's IQ2 mechanism
- **70+ verified models** — LLaMA, Mistral, Mixtral, DeepSeek, Qwen, Phi, ChatGLM, MiniCPM, and multimodal (Qwen-VL, StableDiffusion)
- **DeepSeek V3/R1 671B** on 1–2 Arc GPUs via FlashMoE
- **ESIMD kernels** — Explicit SIMD (Intel's assembly-level GPU programming via SYCL extension) for matvec with `dpas` instructions hitting XMX hardware
- **QKV+Norm+RoPE fusion** — single kernel combining QKV projection, LayerNorm, and RoPE
- **FP8 KV cache** — 2× memory traffic reduction vs BF16 for KV cache
- **Persistent kernel decode** — all model weights loaded into registers once, then streaming activations in a persistent loop
- **Self-speculative decoding** — ~30% speedup for FP16/BF16 inference latency
- **Finetuning** — LoRA, QLoRA, DPO, QA-LoRA, ReLoRA on Intel GPUs

## Optimization Techniques — Portability Analysis

### ESIMD DPAS for Matvec
Uses Intel's `dpas` (Dot Product Accumulate Systolic) instructions to hit XMX hardware. Effective for GEMM (prefill). For matvec (decode), the arithmetic intensity of quantized dot products is already **memory-bound** — XMX doesn't help. *Not portable to llama.cpp's decode path.*

### QKV+Norm+RoPE Fusion
Works when Q, K, V weights are stored as one concatenated tensor. llama.cpp stores them separately. Maps to 3-way fused matvec dispatch (Q/K/V share src1 activation, three output rows in one kernel). *Partially portable — 3-way approach already exists in some optimized branches.*

### Persistent Kernel Decode
Loads all model weights into registers once, processes all tokens in a persistent loop. Requires full backend re-architecture around a persistent execution model (like CUDA MPS or Vulkan's single-submit model). *Not portable without backend rewrite.*

### FP8 KV Cache
Reduces KV cache memory traffic 2× vs BF16. The SYCL backend doesn't currently have FP8 support. **This is the most actionable remaining optimization** — portable if FP8 quant types are added to llama.cpp's type system.

## Migration Path

Intel merged XPU support into upstream PyTorch (`torch.xpu`) starting from 2.4. IPEX-LLM's model-specific optimizations have been superseded by:
- `torch.compile` with XPU backend for graph-level fusion
- oneDNN for matmul (handles XMX dispatch internally)
- `torch.xpu.optimize_for_inference()` for whole-model optimization

**For new projects, use `torch.xpu` directly.** Reference IPEX-LLM's source only for studying specific kernel optimization techniques.
