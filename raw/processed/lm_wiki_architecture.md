# Andrej Karpathy’s AI Workflow: The Self-Organizing Knowledge Base

Andrej Karpathy recently revealed that he is shifting his AI usage away from heavy coding and toward building and maintaining a sophisticated personal knowledge base for his research.

---

### The Workflow Breakdown

* **Raw Data Ingestion:** He dumps all raw sources—research papers, articles, code repos, and images—into a single folder.
* **LLM as Librarian:** An LLM processes these sources to build a **Markdown-based Wiki**. It generates summaries, creates concept articles, and builds links between related ideas.
* **Obsidian Frontend:** Karpathy uses Obsidian to visualize the data. While he views the organized wiki and charts there, the LLM is the primary "writer"—he rarely edits the files manually.

### Key Optimization Strategies

| Feature | Description |
| :--- | :--- |
| **No-RAG Retrieval** | For topics up to ~400K words, he feeds the wiki directly to the LLM. It manages its own index files to find what it needs without complex retrieval pipelines. |
| **Multimodal Outputs** | The system doesn't just produce text; it generates **slide decks, charts, and visualizations** which are then filed back into the system. |
| **Automated Health Checks** | The LLM periodically scans the wiki to identify inconsistencies, fill information gaps via web search, and suggest new research directions. |
| **Custom Search** | He "vibe-coded" a bespoke search engine specifically for his wiki, usable via browser or as a tool for other LLMs. |

---

### The Future: Moving Beyond Context
Karpathy’s next goal is to **fine-tune a model** on his own research. This moves the knowledge from the "context window" (short-term memory) into the model's "weights" (long-term intuition), allowing for even deeper synthesis of his personal data.

> "Everything you research on a given topic — organized into one system you can query, build on, and return to forever."

#AndrejKarpathy #AIWorkflows #PersonalKnowledgeManagement #Obsidian #LLMs
