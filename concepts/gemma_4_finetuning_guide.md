TAGS: #llm #ai-workflow #productivity #data-management #obsidian #gemma-4 #fine-tuning

Links: [[llm]] [[ai-workflow]] [[productivity]] [[data-management]] [[obsidian]] [[gemma-4]] [[fine-tuning]]

## Training Gemma 4 Models with Unsloth

This guide details how to train Google's [[Gemma 4]] models (E2B, E4B, 26B-A4B, and 31B) using the **Unsloth** library. Unsloth offers significant performance benefits:

*   Trains Gemma 4 approximately **~1.5x faster** with **~60% less VRAM** compared to FA2 setups (with no accuracy loss).
*   Gemma 4 E2B training is possible on **8GB VRAM**, and E4B requires 10GB VRAM.

### Training Methods & Resources

You can fine-tune Gemma 4 using:

1.  **Unsloth Studio:** A free, UI-based notebook available in [[Unsloth Studio]] for training on MacOS, Windows, Linux, and NVIDIA GPUs (Intel, MLX, AMD support is forthcoming).
2.  **Code-Based Guide:** Free Google Colab notebooks are provided for E2B/E4B models, while larger models like 26B-A4B and 31B require A100 GPUs.

### Model Variants & Memory Requirements

*   **Multimodal (E2B / E4B):** These variants support [[image]] and [[audio]] fine-tuning. For LoRA:
    *   Gemma 4 E2B LoRA works on **8-10GB VRAM**.
    *   Gemma 4 E4B LoRA requires **17GB VRAM**.
*   **QLoRA:** 31B QLoRA requires **22GB** of VRAM, and 26B-A4B LoRA needs >40GB.

### Key Training Considerations & Bug Fixes

#### Loss Quirks
*   For Gemma-4 E2B and E4B, a loss between **13-15 is normal** due to multimodal model quirks. 
*   Gemma 26B and 31B typically have lower losses (1-3 or less), with vision models showing higher losses (3-5).

#### Gradient Accumulation Warning
If observed losses are significantly higher (e.g., 100 or 300), it is likely that **gradient accumulation is not accounted for properly**. Unsloth and Unsloth Studio have fixed this.

#### Critical Inference Fixes
*   **`use_cache = True` vs `False`:** For E2B/E4B, setting `use_cache=False` (often forced by `gradient_checkpointing=True`) causes garbage logits because KV-shared layers rely on the cache. Unsloth has fixed this issue.
*   **Audio Overflow:** On fp16 (Tesla T4), `Gemma4AudioAttention` can cause a `RuntimeError: value cannot be converted to type c10::Half without overflow` due to `-1e9` overflowing the fp16 max value.

### Multimodal Data Formatting Best Practices

When fine-tuning multimodal models (E2B/E4B):

*   **Image Format:** Place the image **before** the text instruction in the user content block.
*   **Audio Format:** Audio is only for E2B/E4B. Keep clips short and task-specific.

### Data Preparation & Chat Templates

1.  **Chat Roles:** Use standard roles: `system`, `user`, and `assistant`.
2.  **Thinking Mode:** If preserving reasoning is key, mix reasoning examples (minimum 75% reasoning). Use the `gemma-4-thinking` chat template for larger models (26B/31B) and `gemma-4` for smaller ones.
3.  **Multi-turn Rule:** For multi-turn chats, only include the **final visible answer** in the conversation history; do not feed earlier thought blocks into later turns.

### Saving and Exporting Models

Fine-tuned models can be exported to various formats using Unsloth Studio or code:

*   **GGUF:** Use `model.save_pretrained_gguf()` for quantization methods like `q4_k_m`, `q8_0`, or `f16`.
*   **Deployment:** Guides are available for [[llama.cpp]], [[vLLM]], [[llama-server]], [[Ollama]], and [[SGLang]].

> **⚠️ Warning:** If the exported model performs poorly in another runtime, the most common cause is using the **wrong chat template / EOS token** during inference.