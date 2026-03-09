# AgentSentinel

**Mission:** Building the world’s first "Governance and Control Plane" for autonomous AI agents to close the "Agent Trust Gap" through a middleware that prevents hallucinations, financial leakage, and unauthorized access.

---

### 🌟 Project Origin: The STAR Method

**Situation**  
As AI agents gain autonomy, they act on behalf of users—updating databases, sending emails, or processing refunds. However, underlying LLMs are prone to "hallucinations," jailbreaks, or logical errors. Trusting an agent directly with full system access creates a massive security risk, known as the "Agent Trust Gap."

**Task**  
We needed to build a robust "Governance and Control Plane" that acts as a secure middleware. This proxy layer must intercept every *Tool Call* an AI agent attempts, enforce hard programmatic rules, and semantically evaluate the agent's intent *before* allowing the action to execute. Our goal was to build a production-grade MVP within 30 days.

**Action**  
We built **AgentSentinel**, entirely designed around the "Trust but Verify" paradigm:
1. **The Intercept Layer (FastAPI):** A gateway API that receives and pauses every agent action before it reaches the target system.
2. **The Policy Engine (YAML & Pydantic):** A static rules engine that instantly blocks explicitly forbidden actions. For instance, it prevents a "basic_agent" from calling the `delete_user_database` tool, regardless of what the agent says.
3. **The Reasoning Auditor ("The Sentinel"):** A secondary, low-latency LLM that reviews the agent's payload. If an agent tries to use an *allowed* tool (`query_database`) but injects a malicious payload (like a SQL Injection `DROP TABLE`), the Auditor assigns a "Hallucination/Risk Score."
4. **The Circuit Breaker:** If the risk score exceeds our safe threshold (e.g., 0.8), the execution is halted and flagged.
5. **Interactive Dashboard (Streamlit):** A human-in-the-loop dashboard to visualize rejected and approved tool calls across different auditor models.

**Result**  
The MVP successfully demonstrates that an autonomous "AI Car" can go fast safely, because we built robust "Brakes". During simulations, AgentSentinel consistently deflects legitimate SQL injection attacks and unauthorized deletion commands, proving the effectiveness of dual-layer governance in making AI agents enterprise-ready.

---

## Architecture

1. **The Intercept Layer**: FastAPI-based API acting as the proxy gateway.
2. **The Policy Engine**: YAML-driven logic handler enforcing hard constraints (`policies.yaml`).
3. **The Reasoning Auditor**: Secondary model reviewing the main agent's intent (`app/auditor.py`).
4. **The Circuit Breaker**: Blocks the action if the "Hallucination Score" runs too high.

## Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# Install UI dashboard dependencies
pip install streamlit pandas plotly
```

## Running the Application

**1. Run the Interactive Streamlit Dashboard Demo**
```bash
# Important: Run this inside your virtual environment using the `-m streamlit run` module method
python -m streamlit run dashboard/app.py
```

**2. Run the Backend API Server (Optional Standalone)**
```bash
uvicorn app.policy_evaluator:app --reload
```
