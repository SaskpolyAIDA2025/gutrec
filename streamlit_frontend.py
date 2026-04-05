import streamlit as st
from src.graph.workflow import app
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(layout='wide', page_title="Project Gutenberg Recommendation Platform", page_icon='📚')

# --- Initialize persistent chat history ---
if 'message_history' not in st.session_state:
    st.session_state.message_history = [
        AIMessage(content="Welcome to the Gutenberg Book Recommendation system.\n"
                          "Give me a title and author as reference to look for one similar to it.\n"
                          "Type 'exit' to quit.")
    ]

# --- Initialize graph state (this must NOT be recreated every rerun) ---
if 'graph_state' not in st.session_state:
    st.session_state.graph_state = {
        "messages": [],
        "loop_count": 0,
        "reset_messages": False,
        "broad_query": ""
    }

state = st.session_state.graph_state

left_col, main_col, right_col = st.columns([1, 2, 1])

# --- Clear Chat Button ---
with left_col:
    if st.button('Clear Chat'):
        st.session_state.message_history = []
        state["messages"] = []
        state["loop_count"] = 0
        state["reset_messages"] = False
        state["broad_query"] = ""

# --- Chat UI ---
with main_col:
    user_input = st.chat_input("Type here...")

    # Reset state after a completed cycle
    if state["reset_messages"]:
        state["messages"] = []
        state["loop_count"] = 0
        state["reset_messages"] = False
        state["broad_query"] = ""

    if user_input:
        # 1. Add user message to BOTH histories BEFORE invoking graph
        user_msg = HumanMessage(content=user_input)
        st.session_state.message_history.append(user_msg)
        state["messages"].append(user_msg)

        # 2. Invoke LangGraph with the updated state
        response = app.invoke(state)

        # 3. Update Streamlit chat history with graph output
        st.session_state.message_history = response["messages"]

        # 4. Update graph state with returned values
        state["messages"] = response["messages"]
        state["loop_count"] = response.get("loop_count", 0)
        state["reset_messages"] = response.get("reset_messages", False)
        state["broad_query"] = response.get("broad_query", "")

    # --- Render chat history ---
    for i in range(1, len(st.session_state.message_history) + 1):
        this_message = st.session_state.message_history[-i]
        if isinstance(this_message, AIMessage):
            box = st.chat_message("assistant")
        else:
            box = st.chat_message("user")
        box.markdown(this_message.content)

