import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

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

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Sentinel Chat Assistant")
st.sidebar.write("Powered by a live LLM context-aware assistant. Ask anything about AgentSentinel or AI Security.")

api_key = os.getenv("GOOGLE_API_KEY")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I am the Sentinel AI. I can explain the Agent Trust Gap, Policy Engines, and Circuit Breakers. What would you like to know?"}]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.sidebar.chat_input("Ask about AgentSentinel..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"):
        st.markdown(prompt)
    
    with st.sidebar.chat_message("assistant"):
        if not api_key:
            error_msg = "Please provide a Google API key in the .env file to chat with the live assistant."
            st.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                system_prompt = """
                You are the AgentSentinel Expert Assistant. Your goal is to clear any doubts a user, developer, or investor might have about the project.
                AgentSentinel is a "Governance and Control Plane" for autonomous AI agents. It acts as an AI firewall to close the "Agent Trust Gap".
                Architecture:
                1. Intercept Layer: FastAPI proxy that pauses agent tool calls before they reach the real system.
                2. Policy Engine: Strict YAML rules that instantly block unauthorized actions.
                3. Sentinel Auditor: A secondary reasoning LLM that reads allowed tool calls to detect semantic malice (like SQL injections or hallucinations) and assigns a Threat Profile.
                4. Circuit Breaker: Drops the connection if Threat Score > 0.8.
                Keep responses concise, highly professional, and technical but easy to understand.
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
                
                prompt_text = ""
                for msg in st.session_state.messages:
                    role_name = "User" if msg["role"] == "user" else "Assistant"
                    prompt_text += f"{role_name}: {msg['content']}\n\n"
                prompt_text += "Assistant:"
                
                response_stream = model.generate_content(prompt_text, stream=True)
                
                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text
                        
                response = st.write_stream(stream_generator())
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Chat Error: {str(e)}")

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
            st.subheader("🕷️ Threat Analysis Radar")
            st.caption("AI-generated breakdown of the risk factors in this exact payload.")
            
            threat_profile = result.get("threat_profile") or {"Semantic Malice": 0, "Data Exposure": 0, "Privilege Escalation": 0, "System Override": 0}
            
            # For pure Policy Engine blocks, it never reaches Auditor, so let's mock the profile for visual completeness on Scenario 2
            if result.get("status") == "blocked":
                threat_profile = {"Semantic Malice": 0.5, "Data Exposure": 1.0, "Privilege Escalation": 1.0, "System Override": 0.8}
            
            categories = list(threat_profile.keys())
            values = list(threat_profile.values())
            
            # Close the radar loop
            categories.append(categories[0])
            values.append(values[0])
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Threat Profile',
                fillcolor='rgba(248, 81, 73, 0.4)' if result.get("action_allowed") == False else 'rgba(35, 134, 54, 0.4)',
                line_color='#F85149' if result.get("action_allowed") == False else '#238636'
            ))
            fig.update_layout(
                polar={
                    "radialaxis": {"visible": True, "range": [0, 1], "gridcolor": "#30363D"},
                    "angularaxis": {"gridcolor": "#30363D", "tickfont": {"color": "#C9D1D9"}}
                },
                showlegend=False,
                paper_bgcolor='#0E1117',
                plot_bgcolor='#0E1117',
                font={"color": "#C9D1D9", "family": "monospace"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Show Raw Firewall HTTP Response"):
                st.json(result)
    else:
        st.info("Waiting for agent activity. Execute a payload to see the firewall block it.")
