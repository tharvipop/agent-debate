"""Streamlit UI for multi-model interaction."""

import asyncio

import streamlit as st
from core.engine import run_initial_models, summarize_responses

# Page config for clean white theme
st.set_page_config(
    page_title="AI Model Explorer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for clean, minimal design
st.markdown(
    """
    <style>
    .main {
        background-color: white;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
    .model-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .summary-card {
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header section with inspiring question
st.title("✨ AI Model Explorer")
st.markdown(
    """
    <h3 style='text-align: center; color: #666; font-weight: 300; margin-bottom: 30px;'>
    What insights will you discover today?
    </h3>
    """,
    unsafe_allow_html=True,
)

# User input section
user_question = st.text_area(
    "Enter your question:",
    placeholder="Ask something thought-provoking...",
    height=100,
    label_visibility="collapsed",
)

submit_button = st.button("🚀 Get Responses", type="primary", use_container_width=True)

# Process and display responses
if submit_button and user_question.strip():
    with st.spinner("Querying models..."):
        # Run async orchestrator
        responses = asyncio.run(run_initial_models(user_question))

    # Display model responses in 3 horizontal sections
    st.markdown("---")
    st.subheader("Model Responses")

    # Google Gemini 2.5 Flash Lite
    with st.container():
        st.markdown(
            "<div class='model-card'>",
            unsafe_allow_html=True,
        )
        st.markdown("**🔷 Google Gemini 2.5 Flash Lite**")
        st.write(responses.get("google/gemini-2.5-flash-lite", "No response"))
        st.markdown("</div>", unsafe_allow_html=True)

    # Anthropic Claude 3 Haiku
    with st.container():
        st.markdown(
            "<div class='model-card'>",
            unsafe_allow_html=True,
        )
        st.markdown("**🟣 Anthropic Claude 3 Haiku**")
        st.write(responses.get("anthropic/claude-3-haiku", "No response"))
        st.markdown("</div>", unsafe_allow_html=True)

    # OpenAI GPT-4o Mini
    with st.container():
        st.markdown(
            "<div class='model-card'>",
            unsafe_allow_html=True,
        )
        st.markdown("**🟢 OpenAI GPT-4o Mini**")
        st.write(responses.get("openai/gpt-4o-mini", "No response"))
        st.markdown("</div>", unsafe_allow_html=True)

    # Summarized section
    st.markdown("---")
    st.subheader("📊 Synthesized Summary")

    with st.spinner("Generating summary..."):
        summary = asyncio.run(summarize_responses(responses))

    with st.container():
        st.markdown(
            "<div class='summary-card'>",
            unsafe_allow_html=True,
        )
        st.write(summary)
        st.markdown("</div>", unsafe_allow_html=True)

elif submit_button:
    st.warning("⚠️ Please enter a question before submitting.")
