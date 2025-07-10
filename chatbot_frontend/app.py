import streamlit as st
import requests
import uuid
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(layout="wide")
st.title("_DMARV_ :blue[LLM Chatbot] :sunglasses:")

# Generate or restore session info
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

# Sidebar navigation
selected_tab = st.sidebar.radio("Navigation", ["Chat", "Upload Documents"])

# ==============================
# -------- Chat Tab ------------
# ==============================
if selected_tab == "Chat":
    st.subheader("Chat with your assistant")

    # Chat History Section
    with st.sidebar:
        st.markdown("### 💬 Chat History")

        # New Chat button
        if st.button("➕ Start New Chat"):
            st.session_state.chat_id = str(uuid.uuid4())

        # List chats
        try:
            chat_ids = requests.get(f"{BACKEND_URL}/api/user/{st.session_state.user_id}/chats").json()
            for cid in chat_ids:
                cols = st.columns([3, 1])
                with cols[0]:
                    if st.button(f"Resume: {cid[:8]}"):
                        st.session_state.chat_id = cid
                with cols[1]:
                    if st.button("❌", key=f"del_{cid}"):
                        requests.delete(f"{BACKEND_URL}/api/history/{st.session_state.user_id}/{cid}")
                        st.rerun()
        except Exception as e:
            st.error(f"Error loading chats: {e}")

    # Display messages if chat selected
    if st.session_state.chat_id:
        try:
            messages = requests.get(
                f"{BACKEND_URL}/api/history/{st.session_state.user_id}/{st.session_state.chat_id}"
            ).json()
            for msg in messages:
                if msg["role"] == "human":
                    with st.chat_message("user"):
                        st.markdown(msg["message"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg["message"])
        except Exception as e:
            st.error(f"Error loading chat history: {e}")

    # Input for user prompt
    if prompt := st.chat_input("Ask a question..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chat/stream",
                json={
                    "user_id": st.session_state.user_id,
                    "chat_id": st.session_state.chat_id,
                    "question": prompt
                },
                stream=True
            )

            # Streaming response
            answer = ""
            with st.chat_message("assistant"):
                message_box = st.empty()
                for chunk in response.iter_lines():
                    if chunk:
                        decoded = chunk.decode("utf-8")
                        answer += decoded
                        message_box.markdown(answer)

        except Exception as e:
            st.error(f"Error: {e}")

# ==============================
# ------- Upload Tab -----------
# ==============================
elif selected_tab == "Upload Documents":
    st.subheader("📄 Upload PDF Documents")
    uploaded_files = st.file_uploader("Upload your PDFs", type=["pdf"], accept_multiple_files=True)

    if st.button("Upload") and uploaded_files:
        with st.spinner("Uploading files to backend..."):
            files = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
            try:
                res = requests.post(f"{BACKEND_URL}/api/upload", files=files)
                if res.status_code == 200:
                    result = res.json()
                    st.success("Upload complete!")
                    for status in result["results"]:
                        st.write(f"{status['filename']}: {status['message']}")
                else:
                    st.error(f"Failed: {res.text}")
            except Exception as e:
                st.error(f"Error: {e}")
