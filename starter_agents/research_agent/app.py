import streamlit as st

from agent import create_research_agent


st.set_page_config(
    page_title="Research Agent",
    page_icon="🔎",
    layout="wide",
)

# -----------------------------
# Sidebar — API Key
# -----------------------------

with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Enter your API key",
    )

    submit_key = st.button(
        "Submit",
        type="primary",
        use_container_width=True,
    )

    if submit_key:
        if api_key.strip():
            st.session_state["api_key"] = api_key
            st.session_state["api_key_submitted"] = True
            st.success("API key submitted.")
        else:
            st.session_state["api_key_submitted"] = False
            st.warning("Enter an API key.")


# -----------------------------
# Main UI
# -----------------------------

st.title("🔎 Research Agent")

if not st.session_state.get("api_key_submitted", False):

    st.info("Enter your Gemini API key in the sidebar to start researching.")

else:

    st.success("Research Agent is ready.")

    topic = st.text_area(
        "What would you like to research?",
        placeholder="e.g. Impact of climate change on polar bear populations",
        height=120,
    )

    research = st.button(
        "🔎 Research",
        type="primary",
    )

    if research:

        if not topic.strip():
            st.warning("Please enter a research topic.")

        else:
            agent = create_research_agent(
                st.session_state["api_key"]
            )

            with st.spinner("Researching..."):
                response = agent.run(topic)

            st.markdown("## Research Report")
            st.markdown(response.content)