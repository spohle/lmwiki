TAGS: #llm #ai-workflow #productivity #data-management #aws-s3 #object-storage #gemma-4

Links: [[llm]] [[ai-workflow]] [[productivity]] [[data-management]] [[aws-s3]] [[object-storage]] [[gemma-4]]

The high cost and token consumption of advanced LLMs like [[Claude]] necessitate various optimization strategies. This document outlines several techniques, ranging from simple viral prompts to complex engineering solutions, aimed at reducing operational costs and improving efficiency.

### Optimization Techniques Overview

The methods can be categorized by their complexity and impact:

*   **Meme-Tier / Viral Hacks:**
    *   **Caveman Mode:** Forces Claude to respond with extreme brevity (e.g., *"Why use many token when few token do trick."*), resulting in a significant reduction of output tokens (65% fewer).

*   **Recommended Practices & Workflow Tweaks:**
    *   **Token-efficient CLAUDE.md:** A configuration file implementing 8 rules to prevent verbose responses, flattery, and full file rewrites, leading to a 17% total cost reduction.
    *   **Manual `/compact` at 60%:** Instead of waiting for the default 95% context trigger, manually running compaction at 60% while specifying what to preserve keeps the context 'lean' proactively.

*   **Serious Engineering & High-Performance Tools:**
    *   **RTK (Rust Token Killer):** A high-performance Rust binary that intercepts and compresses command output *before* it enters the context window, achieving up to an 80% reduction per session.
    *   **ccusage:** An essential CLI tool for real-time tracking of actual token expenditure, adhering to the principle: "You can't fix what you don't measure."

*   **Strategic & Cost Control Measures:**
    *   **Model Routing:** Strategically assigning subagent tasks to less expensive models like [[Haiku]] instead of using the most powerful model ([[Opus]]) for every task, potentially saving up to 92%.
    *   **Thinking Budget:** Controlling internal processing overhead by setting `MAX_THINKING_TOKENS` or utilizing the `/effort` command to cap Claude's default 32K thinking tokens per request when only smaller amounts are needed.

These optimizations demonstrate a spectrum of approaches for managing [[LLM]] interaction, moving from simple prompt engineering to dedicated system tooling.