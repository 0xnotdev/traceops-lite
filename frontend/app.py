import uuid
import httpx
import streamlit as st

st.set_page_config(
    page_title="HR Assistant",
    page_icon="💼",
    layout="centered",
)

st.title("HR Assistant")
st.caption(
    "Powered by TraceOps Lite — failures become tests automatically"
)

API_BASE = "http://localhost:8000"

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# Display chat history
for i, msg in enumerate(st.session_state.messages):

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        # Show thumbs-down button for assistant replies
        if (
            msg["role"] == "assistant"
            and msg.get("trace_id")
        ):

            if st.button(
                "👎 Report Failure",
                key=f"thumbs_{i}"
            ):

                with httpx.Client(timeout=None) as client:
                    client.post(
                        f"{API_BASE}/failure/report",
                        json={
                            "trace_id": msg["trace_id"]
                        }
                    )

                st.success(
                    "Failure reported. "
                    "Regression PR generation triggered."
                )

# Chat input
if prompt := st.chat_input(
    "Ask about HR policies..."
):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            with httpx.Client(timeout=None) as client:

                resp = client.post(
                    f"{API_BASE}/chat",
                    json={
                        "question": prompt,
                        "session_id": (
                            st.session_state.session_id
                        ),
                    }
                )

                data = resp.json()

        st.write(data["answer"])

        st.session_state.messages.append({
            "role": "assistant",
            "content": data["answer"],
            "trace_id": data.get("trace_id"),
        })

        # Immediate thumbs-down button for new response
        if st.button(
            "👎 Report Failure",
            key=f"new_{len(st.session_state.messages)}"
        ):

            with httpx.Client(timeout=None) as client:
                client.post(
                    f"{API_BASE}/failure/report",
                    json={
                        "trace_id": data.get("trace_id")
                    }
                )

            st.success(
                "Failure reported. "
                "Regression PR generation triggered."
            )