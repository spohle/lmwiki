# 🤖 Project Agents: OpenCode + Gemma 4

This project utilizes a local multi-agent orchestration via OpenCode to manage the Python development lifecycle.

## 🛠 Model Setup
- **Core LLM:** Gemma 4 (Local)
- **Primary Language:** Python 3.10+
- **Infrastructure:** OpenCode Local Server

---

## 👥 Agent Directory

### 🏗 The Architect (`@architect-agent`)
- **Focus:** System Design & Logic.
- **Usage:** Call this agent when starting a new feature to define the "How" before the "What."

### 🐍 The Python Developer (`@coder-agent`)
- **Focus:** Clean, executable Python code.
- **Usage:** Provide the architect's specs to this agent to generate `.py` files.

### 🛡 The QA Specialist (`@test-agent`)
- **Focus:** Security, Performance, & Unit Tests.
- **Usage:** Pass finished code to this agent to generate `pytest` files or find logic gaps.

### 📝 The Documentarian (`@docs-agent`)
- **Focus:** User Guides & Docstrings.
- **Usage:** Use this agent to keep `README.md` and inline comments up to date.

---

## 🔄 Local Workflow
1. **Plan:** `@architect-agent "Design a rate-limiter for my FastAPI app."`
2. **Build:** `@coder-agent "Implement the design provided by the architect."`
3. **Verify:** `@test-agent "Write 5 edge-case tests for the new rate-limiter."`
4. **Finalize:** `@docs-agent "Update the API documentation."`

---

> **Note:** Since we are running **Gemma 4** locally, ensure your local inference server (Ollama/LM Studio) is active before calling these agents.
