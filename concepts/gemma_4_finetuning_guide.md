TAGS: #gemma-4 #fine-tuning #llm #ai-workflow #unsloth #multimodal-ai #cloud-computing #data-management

Links: [[gemma-4]] [[fine-tuning]] [[llm]] [[ai-workflow]] [[unsloth]] [[multimodal-ai]] [[cloud-computing]] [[data-management]]

This guide details the process of fine-tuning Google's [[Gemma 4]] models (E2B, E4B, 26B-A4B, and 31B) using the [[Unsloth]] framework. Unsloth significantly enhances the [[fine-tuning]] process by offering approximately 1.5x faster training and ~60% less VRAM consumption compared to traditional FA2 setups, without compromising accuracy. It also addresses several universal bugs specific to Gemma 4 training.

### Key Features and Benefits of Unsloth for Gemma 4
*   **Efficiency**: Reduced VRAM usage (e.g., Gemma 4 E2B on 8GB VRAM, E4B on 10GB VRAM for training; E2B LoRA on 8-10GB, E4B LoRA on 17GB, 31B QLoRA on 22GB).
*   **Bug Fixes**: Corrects issues like inflated losses due to gradient accumulation, `IndexError` during inference for 26B/31B models, `use_cache=True` generation producing gibberish for E2B/E4B, and Audio float16 overflow errors.
*   **Multimodal Support**: Supports vision, text, audio, and [[Reinforcement Learning]] (RL) fine-tuning for Gemma 4, particularly for E2B and E4B variants.
*   **Export Options**: Allows exporting fine-tuned models to formats like GGUF (for [[llama.cpp]], [[Ollama]]), safetensor, etc.

### Fine-tuning Approaches
Unsloth provides two primary methods for fine-tuning Gemma 4:

1.  **[[Unsloth Studio]] (UI-based)**:
    *   A new open-source web UI for local AI, supporting MacOS, Windows, and Linux with NVIDIA GPUs (Intel, MLX, AMD support planned).
    *   Offers a streamlined workflow: Install Unsloth, launch Studio, select model/dataset, adjust hyperparameters, monitor training, and export the model.
    *   Includes a 'Compare Mode' to evaluate the fine-tuned LoRA adapter against the original model.

2.  **[[Unsloth Core]] (Code-based)**:
    *   Utilizes [[Google Colab]] notebooks for free training, with specific notebooks for Gemma 4 E2B, E4B, 26B-A4B, and 31B (larger models requiring A100 GPUs).
    *   Involves loading models with `FastModel.from_pretrained`, applying LoRA adapters (`FastModel.get_peft_model`), preparing data using `get_chat_template` and `standardize_data_formats`, and training with `SFTTrainer`.
    *   Supports `train_on_responses_only` to focus training on assistant outputs, improving accuracy.

### Tips and Best Practices
*   **Loss Interpretation**: Normal loss for Gemma 4 E2B/E4B can be 13-15 (multimodal quirk); 26B/31B models typically have lower loss (1-3, vision 3-5).
*   **Reasoning Preservation**: Mix reasoning-style examples (min 75%) with direct answers. Use `gemma-4-thinking` chat template for larger models and `gemma-4` for smaller ones. Enable thinking mode via `enable_thinking = True` in `tokenizer.apply_chat_template`.
*   **Multilingual Capabilities**: Gemma 4 is powerful for multilingual fine-tuning, supporting 140 languages.
*   **Model Recommendation**: For better quantization accuracy, `E4B QLoRA` is generally recommended over `E2B LoRA`.
*   **MoE Fine-tuning (26B-A4B)**: Prefer LoRA (especially 16-bit/bf16 LoRA) over full fine-tuning. Start with shorter contexts and smaller ranks.
*   **Multimodal Fine-tuning (E2B/E4B)**: Use `FastVisionModel`. Initially, fine-tune only language, attention, and MLP layers, enabling vision/audio layers later if needed. Remember to place images/audio *before* text instructions in prompts.
*   **Data Formatting**: Adhere to standard chat roles (`system`, `user`, `assistant`). For thinking mode, decide whether to train on visible thought blocks or final answers only, and avoid mixing incompatible formats. For multi-turn conversations, only include the final visible answer in history.

This comprehensive guide provides the necessary tools and knowledge for efficient and effective [[Gemma 4]] [[LLM]] [[fine-tuning]] using [[Unsloth]].