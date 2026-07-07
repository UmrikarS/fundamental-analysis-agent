"""
Agent Pipeline

  A. Interpreter      -> plain-English summary of financial health
  B. Anomaly Detector -> flags unusual YoY metric changes
  C. Synthesizer      -> Strengths / Risks / Summary narrative
  D. Chat Agent       -> answers user questions about the company
"""

import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"


def _call_gemini(system_prompt: str, user_content: str, max_tokens: int = 1200) -> str:
    cfg = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_tokens,
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=user_content,
        config=cfg,
    )
    return response.text or ""


def run_interpreter_agent(ratios: dict) -> tuple[str, str]:
    """Returns (output_text, input_summary) for lineage display."""
    system_prompt = (
        "You are a junior equity analyst writing a financial health note. "
        "Using ONLY the data provided, write a thorough analysis covering: "
        "1) Revenue and profit growth trends over the years shown, "
        "2) Profitability quality — margins and return ratios, "
        "3) Balance sheet — leverage and liquidity position, "
        "4) Free cash flow generation and trend. "
        "Write 6-8 clear sentences in plain prose. "
        "No markdown, no bullet points, no bold text, no asterisks, no headings. "
        "Be specific — reference actual numbers from the data."
    )
    input_json = json.dumps({
        "ratios_by_year": ratios.get("ratios_by_year", {}),
        "trends": ratios.get("trends", {}),
        "valuation": ratios.get("valuation", {}),
    }, indent=2, default=str)
    user_content = f"Financial data for {ratios.get('company_name', '')}:\n{input_json}"
    output = _call_gemini(system_prompt, user_content)
    return output, input_json


def run_anomaly_agent(ratios: dict) -> tuple[str, str]:
    """Returns (output_text, input_summary) for lineage display."""
    system_prompt = (
        "You are a financial risk analyst reviewing multi-year ratios for anomalies. "
        "Identify ALL metrics that changed notably year-over-year — both positive and negative surprises. "
        "For each flag: state the metric, the specific values and years involved, and why it is notable. "
        "Format as a plain numbered list: 1. 2. 3. etc. "
        "Write at least 4 flags if the data supports it. "
        "No markdown bold, no asterisks. Plain text only. "
        "End with one sentence summarising the overall risk level: Low / Moderate / Elevated."
    )
    input_json = json.dumps({
        "ratios_by_year": ratios.get("ratios_by_year", {}),
        "trends": ratios.get("trends", {}),
    }, indent=2, default=str)
    user_content = f"Multi-year financial ratios for {ratios.get('company_name', '')}:\n{input_json}"
    output = _call_gemini(system_prompt, user_content)
    return output, input_json


def run_synthesis_agent(interpreter_output: str, anomaly_output: str,
                        company_name: str) -> tuple[str, str]:
    """Returns (output_text, input_summary) for lineage display."""
    system_prompt = (
        "You are a senior analyst combining a junior analyst note and an anomaly report "
        "into a balanced investment-quality summary. "
        "Use exactly these three section labels on their own line, each followed by "
        "3-4 clear sentences:\n\n"
        "STRENGTHS\n"
        "RISKS AND WATCH ITEMS\n"
        "SUMMARY\n\n"
        "Be specific — reference actual metrics and figures from the inputs. "
        "No markdown, no bold, no asterisks, no bullet points. Plain text only. "
        "Do not give a buy/sell/hold recommendation."
    )
    input_text = (
        f"Company: {company_name}\n\n"
        f"--- Junior Analyst Note (Agent A output) ---\n{interpreter_output}\n\n"
        f"--- Anomaly Report (Agent B output) ---\n{anomaly_output}"
    )
    output = _call_gemini(system_prompt, input_text, max_tokens=1400)
    return output, input_text


def run_chat_agent(question: str, ratios: dict, pipeline_results: dict,
                   history: list[dict]) -> str:
    """
    Answers a user question about the company using financial data + prior agent outputs.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    system_prompt = (
        f"You are a knowledgeable equity research assistant answering questions about "
        f"{ratios.get('company_name', 'this company')} ({ratios.get('ticker', '')}) "
        f"from a data-literate but non-specialist user. "
        f"You have access to the company's multi-year financial ratios, an analyst summary, "
        f"and an anomaly report — all provided in the context below. "
        f"Answer the user's question directly and specifically, referencing actual numbers. "
        f"Keep answers to 3-5 sentences. "
        f"No markdown formatting, no asterisks, no bold. Plain conversational prose. "
        f"If the question asks for a buy/sell recommendation, politely decline and "
        f"offer an analytical perspective instead."
    )
    context = (
        f"=== FINANCIAL DATA ===\n"
        f"{json.dumps(ratios.get('ratios_by_year', {}), indent=2, default=str)}\n\n"
        f"Valuation: {json.dumps(ratios.get('valuation', {}), default=str)}\n\n"
        f"=== ANALYST SUMMARY (Agent C) ===\n{pipeline_results.get('synthesis', '')}\n\n"
        f"=== ANOMALY FLAGS (Agent B) ===\n{pipeline_results.get('anomaly', '')}\n\n"
        f"=== CONVERSATION HISTORY ===\n"
    )
    for msg in history[-6:]:  # Last 3 turns for context
        role = "User" if msg["role"] == "user" else "Assistant"
        context += f"{role}: {msg['content']}\n"
    context += f"\nUser question: {question}"
    return _call_gemini(system_prompt, context, max_tokens=600)


def run_pipeline(ratios: dict) -> dict:
    """Runs all 3 agents and returns outputs + inputs for lineage tracing."""
    interp_out, interp_in   = run_interpreter_agent(ratios)
    anomaly_out, anomaly_in = run_anomaly_agent(ratios)
    synth_out, synth_in     = run_synthesis_agent(
        interp_out, anomaly_out, ratios.get("company_name", "")
    )
    return {
        "interpreter": interp_out,
        "anomaly":     anomaly_out,
        "synthesis":   synth_out,
        # Lineage inputs (what each agent received)
        "lineage": {
            "agent_a_input": interp_in,
            "agent_b_input": anomaly_in,
            "agent_c_input": synth_in,
        },
    }
