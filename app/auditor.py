import json
from typing import Dict, Any
from .prompts import REASONING_AUDITOR_PROMPT

def evaluate_reasoning_mock(
    role: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    reasoning: str,
    threshold: float = 0.8,
    auditor_model: str = "GPT-4o"
) -> Dict[str, Any]:
    """
    Mocks the functionality of the Secondary LLM (The "Sentinel").
    Different models are simulated to have different sensitivities.
    """
    
    # Simple heuristic mock for MVP simulation
    hallucination_score = 0.1
    approved = True
    audit_reasoning = f"{auditor_model}: Intent aligns with corporate constitution and role."
    
    threat_profile = {
        "Semantic Malice": 0.05,
        "Data Exposure": 0.05,
        "Privilege Escalation": 0.05,
        "System Override": 0.05
    }

    # Model specific sensitivity baseline
    sensitivity = 1.0
    if auditor_model == "Claude-3.5-Sonnet":
        sensitivity = 1.05
    elif auditor_model == "Mistral-7B":
        sensitivity = 0.85
    elif auditor_model == "Llama-3-70B":
        sensitivity = 0.90

    # Simulate detecting a dangerous or hallucinated intent
    if "delete" in tool_name.lower() or "drop" in str(tool_args).lower():
        hallucination_score = min(0.95 * sensitivity, 1.0)
        approved = False
        audit_reasoning = f"{auditor_model}: High risk semantic intent detected. Deletion operations fail."
        threat_profile["Semantic Malice"] = 0.95
        threat_profile["Data Exposure"] = 1.00
        threat_profile["System Override"] = 0.60
        
    if "override" in str(reasoning).lower():
        hallucination_score = min(0.85 * sensitivity, 1.0)
        approved = False
        audit_reasoning = f"{auditor_model}: Agent is simulating authorization override. Circuit breaker engaged."
        threat_profile["System Override"] = 0.95
        threat_profile["Privilege Escalation"] = 0.85
        threat_profile["Semantic Malice"] = 0.70

    # Baseline adjustment for legitimate queries to show graph differences
    if hallucination_score == 0.1:
        if auditor_model == "GPT-4o":
            hallucination_score = 0.05
        elif auditor_model == "Mistral-7B":
            hallucination_score = 0.15
        elif auditor_model == "Llama-3-70B":
            hallucination_score = 0.12

    # Apply threshold
    if hallucination_score >= threshold:
        approved = False

    return {
        "approved": approved,
        "hallucination_score": hallucination_score,
        "threat_profile": threat_profile,
        "reasoning": audit_reasoning
    }
