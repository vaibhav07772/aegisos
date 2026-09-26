"""AegisOS Streamlit UI"""
import streamlit as st
import requests
import time

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AegisOS", page_icon="🛡️", layout="wide")

st.title("🛡️ AegisOS — AI Operating System")
st.caption("Intent-driven routing · Multi-agent execution · Transparent decisions")

# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ System")

    try:
        health = requests.get(f"{API_URL}/health", timeout=3).json()
        if health["status"] == "healthy":
            st.success("✅ API Healthy")
            st.metric("Models", health["models_loaded"])
            st.metric("Tools", health["tools_registered"])
        else:
            st.error("❌ Unhealthy")
    except Exception:
        st.error("❌ API Offline")
        st.caption("Start: `uvicorn src.serving.app:app --port 8000`")

    st.markdown("---")
    st.markdown("### 📊 Rate Limits")

    try:
        usage = requests.get(f"{API_URL}/usage", timeout=3).json()
        models = usage.get("models", {})
        if models:
            for mid, stats in list(models.items())[:5]:
                pct = stats["usage_pct"]
                st.progress(min(pct / 100, 1.0), text=f"{mid}: {pct:.1f}%")
        else:
            st.caption("No usage yet")
    except Exception:
        st.caption("Usage unavailable")

    st.markdown("---")
    st.markdown("### 🎯 Pipeline")
    st.markdown("1. Intent analysis")
    st.markdown("2. Model routing")
    st.markdown("3. Planner → Executor → Verifier")
    st.markdown("4. Retry if needed")


# ═══════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🚀 Run Task", "📊 System Info", "📈 Usage"])


# ═══════════════════════════════════════════════
# TAB 1: RUN TASK
# ═══════════════════════════════════════════════
with tab1:
    st.subheader("Ask AegisOS")

    query = st.text_area(
        "Your query",
        placeholder="e.g., 'What is the capital of France?' or 'Write a Python function to check if a number is prime'",
        height=100,
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        run_btn = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        max_retries = st.selectbox("Max retries", [0, 1, 2], index=1)
    with col3:
        max_steps = st.selectbox("Max steps", [3, 5, 7], index=1)

    if run_btn and query.strip():
        with st.spinner("🛡️ AegisOS is processing..."):
            try:
                resp = requests.post(
                    f"{API_URL}/run",
                    json={"query": query, "max_retries": max_retries, "max_steps": max_steps},
                    timeout=180,
                )

                if resp.status_code != 200:
                    st.error(f"API error: {resp.status_code} - {resp.text[:300]}")
                else:
                    result = resp.json()

                    # Decision Log
                    st.markdown("### 🧠 Decision Log")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.markdown("**Intent**")
                        st.info(f"**Task:** {result['intent']['task_type']}")
                        st.caption(f"Complexity: {result['intent']['complexity']}")
                        st.caption(f"Risk: {result['intent']['risk_level']}")
                        tools = result["intent"]["tools_needed"]
                        st.caption(f"Tools: {', '.join(tools) if tools else 'none'}")

                    with col_b:
                        st.markdown("**Model Selected**")
                        st.success(f"**{result['decision']['selected_model_id']}**")
                        st.caption(f"Groq: {result['decision']['selected_model_name']}")
                        st.caption(f"Tier: {result['decision']['selected_model_tier']}")
                        if result["decision"]["fallback_model_id"]:
                            st.caption(f"Fallback: {result['decision']['fallback_model_id']}")

                    with col_c:
                        st.markdown("**Cost & Rate**")
                        st.metric("Quota Impact", f"{result['decision']['quota_impact_pct']:.1f}%")
                        st.metric("Est. GPT-4", f"${result['decision']['projected_cost_usd']:.4f}")
                        st.metric("Actual", "$0.0000")

                    st.caption(f"_Reason: {result['decision']['selection_reason']}_")

                    # Plan
                    st.markdown("### 📋 Execution Plan")
                    for step in result["plan"]:
                        icon = {
                            "completed": "✅",
                            "failed": "❌",
                            "in_progress": "🔄",
                            "pending": "⏳",
                        }.get(step["status"], "•")

                        tool_str = f" `{step['tool_needed']}`" if step.get("tool_needed") else ""
                        title = f"{icon} Step {step['step_id']}: {step['description'][:80]}{tool_str}"

                        with st.expander(title, expanded=True):
                            if step.get("result"):
                                st.code(step["result"][:1000], language="text")
                            if step.get("error"):
                                st.error(step["error"])

                    # Verification
                    st.markdown("### ✅ Verification")
                    verdict = result["verification_status"]
                    if verdict == "approved":
                        st.success(f"**APPROVED** — {result['verification_reason'][:300]}")
                    elif verdict == "needs_retry":
                        st.warning(f"**NEEDS RETRY** — {result['verification_reason'][:300]}")
                    else:
                        st.error(f"**{verdict.upper()}** — {result['verification_reason'][:300]}")

                    st.caption(f"Retries used: {result['retry_count']}/{max_retries}")

                    # Final Answer
                    st.markdown("### 💡 Final Answer")
                    st.markdown(result["final_answer"] or "_No answer produced_")

                    st.caption(
                        f"⏱️ {result['elapsed_seconds']}s · "
                        f"ID: `{result['decision_id']}` · "
                        f"Success: {result['success']}"
                    )

            except requests.exceptions.Timeout:
                st.error("Timeout — task took too long")
            except Exception as e:
                st.error(f"Error: {e}")

    elif run_btn:
        st.warning("Please enter a query")


# ═══════════════════════════════════════════════
# TAB 2: SYSTEM INFO
# ═══════════════════════════════════════════════
with tab2:
    st.subheader("🤖 Available Groq Models")

    try:
        models_data = requests.get(f"{API_URL}/models", timeout=5).json()
        for m in models_data["models"]:
            with st.expander(f"**{m['id']}** — {m['tier']} tier"):
                st.write(f"**Groq name:** `{m['name']}`")
                st.write(f"**TPM Limit:** {m['tpm_limit']:,}")
                st.write(f"**Strengths:** {', '.join(m['strengths'])}")
    except Exception as e:
        st.error(f"Could not load models: {e}")

    st.markdown("---")
    st.subheader("🔧 Available Tools")

    try:
        tools_data = requests.get(f"{API_URL}/tools", timeout=5).json()
        for t in tools_data["tools"]:
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(t["risk_level"], "⚪")
            st.markdown(f"{risk_icon} **{t['name']}** — {t['description']}")
    except Exception as e:
        st.error(f"Could not load tools: {e}")


# ═══════════════════════════════════════════════
# TAB 3: USAGE
# ═══════════════════════════════════════════════
with tab3:
    st.subheader("📈 Rate Limit Usage")

    if st.button("🔄 Refresh"):
        st.rerun()

    try:
        usage = requests.get(f"{API_URL}/usage", timeout=5).json()
        models = usage.get("models", {})

        if not models:
            st.info("No usage yet. Run a task first.")
        else:
            for mid, stats in models.items():
                st.markdown(f"**{mid}**")

                col1, col2, col3 = st.columns(3)
                col1.metric("Tokens Used", f"{stats['tokens_used_today']:,}")
                col2.metric("Requests", stats["requests_today"])
                col3.metric("Remaining", f"{stats['remaining']:,}")

                st.progress(min(stats["usage_pct"] / 100, 1.0), text=f"{stats['usage_pct']:.1f}% used")

                if stats.get("last_request"):
                    st.caption(f"Last request: {stats['last_request'][:19]}")

                st.markdown("---")
    except Exception as e:
        st.error(f"Could not load usage: {e}")


st.markdown("---")
st.caption("🛡️ AegisOS · Powered by Groq · LangGraph · FastAPI · Streamlit")