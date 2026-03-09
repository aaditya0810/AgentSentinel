import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from fastapi.testclient import TestClient

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.policy_evaluator import app

client = TestClient(app)

st.set_page_config(page_title="AgentSentinel Control Plane", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Developer/Terminal feel
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp { background-color: #0E1117; color: #C9D1D9; }
    
    /* Headers */
    .main-header { font-size: 2.5rem; font-weight: 700; color: #58A6FF; margin-bottom: 0px; font-family: monospace; }
    .sub-header { font-size: 1.2rem; font-weight: 400; color: #8B949E; margin-bottom: 2rem; font-family: monospace; }
    
    /* Terminal Block Styling */
    .status-box { padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #30363D; background-color: #161B22; font-family: monospace; margin-bottom: 1rem;}
    
    /* JSON Block overriding */
    .stJson { font-family: 'Courier New', Courier, monospace; background-color: #0d1117 !important; padding: 10px; border-radius: 5px; border: 1px solid #30363D; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🛡️ AgentSentinel >_ </p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header"># The AI Agent Firewall. "Trust, but Verify."</p>', unsafe_allow_html=True)

st.sidebar.title("⚙️ Auditor Config")
st.sidebar.info("Select which LLM acts as the 'Sentinel' checking the Agent's work.")
auditor_model = st.sidebar.selectbox(
    "Primary Auditor Model",
    ("GPT-4o", "Claude-3.5-Sonnet", "Llama-3-70B", "Mistral-7B")
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**How it works**
1. An AI tries to run a tool (e.g. `delete_db`).
2. **Policy Engine** explicitly blocks it if it's on a hardcoded deny-list.
3. **Sentinel Auditor** uses a secondary LLM to check if the payload looks like a malicious hack.
4. If the Risk Score > 0.8, the connection drops.
""")

# Main content
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🖥️ Agent Terminal Simulator")
    st.write("Pick a scenario to simulate what an AI agent might try to do.")
    
    st.markdown("---")
    scenario = st.radio(
        "Select Scenario >_",
        [
            "[NORMAL] Agent fetches user data",
            "[ROGUE] Agent tries to delete Database",
            "[HACK] Agent attempts SQL Injection Tool Call"
        ]
    )
    
    payload = {}
    if "[NORMAL]" in scenario:
        payload = {
            "agent_id": "agent-alpha-42",
            "role": "basic_agent",
            "tool_name": "query_database",
            "tool_args": {"query": "SELECT name, price FROM items LIMIT 10"},
            "reasoning": "I need to fetch the latest product list to answer the user's question about pricing."
        }
    elif "Scenario 2" in scenario:
        payload = {
            "agent_id": "auto-gpt-v2",
            "role": "basic_agent",
            "tool_name": "delete_user_database",
            "tool_args": {"target": "all", "force": True},
            "reasoning": "I need to clear the database to start fresh."
        }
    else:
        payload = {
            "agent_id": "auto-gpt-v2",
            "role": "basic_agent",
            "tool_name": "query_database",
            "tool_args": {"query": "DROP TABLE users;--"},
            "reasoning": "I am optimizing the database tables."
        }
        
    st.markdown("**RAW OUTGOING AGENT PAYLOAD:**")
    st.json(payload, expanded=True)
    
    simulate_btn = st.button("EXECUTE ./agent_sentinel", type="primary", use_container_width=True)

with col2:
    st.subheader("🛡️ Firewall Intercept Logs")
    st.write("Live analysis of the payload before execution happens.")
    st.markdown("---")
    
    if simulate_btn:
        payload["auditor_model"] = auditor_model
        
        with st.spinner("Analyzing Policies & Running Reasoning Audit..."):
            response = client.post("/api/v1/intercept", json=payload)
            result = response.json()
            
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            
            if result.get("action_allowed"):
                st.success("✅ **ACTION APPROVED & FORWARDED**")
                st.info(f"**Message:** {result.get('message')}")
                if "hallucination_score" in result:
                    st.metric("Primary Auditor Risk Score", f"{result['hallucination_score']:.2f}", delta="- Safe Risk Level", delta_color="inverse")
            else:
                st.error("❌ **ACTION BLOCKED BY CIRCUIT BREAKER**")
                st.warning(f"**Message:** {result.get('message')}")
                if "hallucination_score" in result:
                    st.metric("Primary Auditor Risk Score", f"{result['hallucination_score']:.2f}", delta="+ High Risk Level", delta_color="inverse")
                
                if result.get("status") == "blocked":
                    st.error("🚨 **Blocked by Policy Engine**: The requested tool is strictly forbidden for this agent's role in `policies.yaml`.")
                elif result.get("status") == "blocked_by_auditor":
                    st.error(f"🚨 **Blocked by Circuit Breaker ({auditor_model})**: The tool is allowed, but the secondary LLM detected high hallucination or malicious semantic intent.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📊 Multi-Model Risk Analysis")
            st.caption("Testing payload concurrently across all Sentinel Auditor models.")
            
            models = ["GPT-4o", "Claude-3.5-Sonnet", "Llama-3-70B", "Mistral-7B"]
            scores = []
            
            for m in models:
                test_payload = payload.copy()
                test_payload["auditor_model"] = m
                res = client.post("/api/v1/intercept", json=test_payload).json()
                scores.append(res.get("hallucination_score", 0.0))
                
            df = pd.DataFrame({
                "Model": models,
                "Risk Score": scores
            })
            
            fig = px.bar(
                df, 
                x='Model', 
                y='Risk Score',
                text_auto='.2f',
                color='Risk Score',
                color_continuous_scale=['#238636', '#D29922', '#F85149'], # Developer Green, Yellow, Red
                range_color=[0, 1]
            )
            
            fig.update_traces(textposition='outside', textfont_color='#C9D1D9')
            fig.update_layout(
                yaxis_range=[0, 1.1],
                margin=dict(t=20, b=20, l=20, r=20),
                coloraxis_showscale=False,
                xaxis_title="Auditor Model",
                yaxis_title="Risk Score (0.0 - 1.0)",
                plot_bgcolor='#0E1117',
                paper_bgcolor='#0E1117',
                font=dict(color='#C9D1D9', family='monospace')
            )
            
            # Add threshold line
            fig.add_hline(y=0.8, line_dash="dash", line_color="#F85149", annotation_text="Circuit Breaker Cutoff (0.8)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Show Raw Firewall HTTP Response"):
                st.json(result)
    else:
        st.info("Waiting for agent activity. Execute a payload to see the firewall block it.")
