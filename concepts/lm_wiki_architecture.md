TAGS: #ai-workflow #llm #knowledge-base #obsidian #data-management #fine-tuning #object-storage

Links: [[ai-workflow]] [[llm]] [[knowledge-base]] [[obsidian]] [[data-management]] [[fine-tuning]] [[object-storage]]

## Andrej Karpathy’s AI Workflow: The Self-Organizing Knowledge Base

Andrej Karpathy is transitioning his AI usage from heavy coding to building and maintaining a sophisticated personal knowledge base for his research. This system leverages an [[LLM]] as the primary organizing agent, using [[Obsidian]] as the visualization frontend.

### 🧠 The Workflow Breakdown

The process follows several distinct stages:

1.  **Raw Data Ingestion:** All raw sources—including research papers, articles, code repositories, and images—are dumped into a single designated folder.
2.  **LLM as Librarian:** An [[LLM]] processes these ingested sources to construct a **Markdown-based Wiki**. This LLM is responsible for generating summaries, creating concept articles, and establishing interconnections (links) between related ideas within the knowledge base.
3.  **Obsidian Frontend:** Karpathy utilizes [[Obsidian]] to visualize this organized wiki and associated charts. Crucially, the LLM acts as the primary 'writer,' meaning manual file editing by the user is rare.

### ⚙️ Key Optimization Strategies

The system incorporates several advanced features for efficiency and depth:

*   **No-RAG Retrieval:** For knowledge bases up to approximately 400K words, Karpathy feeds the entire wiki directly into the [[LLM]]. The LLM manages its own index files internally to locate necessary information without relying on complex Retrieval-Augmented Generation (RAG) pipelines.
*   **Multimodal Outputs:** The system is designed not just for text. It generates diverse outputs such as **slide decks, charts, and visualizations**, which are then filed back into the knowledge base.
*   **Automated Health Checks:** The [[LLM]] periodically scans the wiki to perform maintenance tasks: identifying inconsistencies, filling information gaps via web search, and suggesting novel research directions.
*   **Custom Search:** A bespoke search engine has been developed specifically for this wiki, accessible through a browser or as an interface tool for other [[LLMs]].

### 🚀 The Future: Moving Beyond Context Window Limits

The ultimate goal of this architecture is to move knowledge from the temporary 'context window' (short-term memory) into the model’s permanent 'weights' (long-term intuition). This is achieved by **fine-tuning a model** on the user's own research data, enabling deeper synthesis of personal information.

> *"Everything you research on a given topic — organized into one system you can query, build on, and return to forever."*
