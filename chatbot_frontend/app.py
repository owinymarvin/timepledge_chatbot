import streamlit as st
import requests
import uuid
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8081")

st.set_page_config(layout="wide")
st.title("_DMARV_ :blue[LLM Chatbot] :sunglasses:")

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

# Navigation
selected_tab = st.sidebar.radio("Navigation", ["Chat", "Upload Documents"])

# -------- Chat Tab --------
if selected_tab == "Chat":
    st.subheader("Chat with your assistant")

    # List previous chat sessions
    chat_ids = requests.get(f"{BACKEND_URL}/api/user/{st.session_state.user_id}/chats").json()

    with st.sidebar:
        st.markdown("### 💬 Chat History")
        for cid in chat_ids:
            if st.button(f"Resume: {cid[:8]}"):
                st.session_state.chat_id = cid

    # Display history if exists
    if st.session_state.chat_id:
        messages = requests.get(f"{BACKEND_URL}/api/history/{st.session_state.user_id}/{st.session_state.chat_id}").json()
        for msg in messages:
            if msg["role"] == "human":
                with st.chat_message("user"):
                    st.markdown(msg["message"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["message"])

    # Input prompt
    if prompt := st.chat_input("Ask a question..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "user_id": st.session_state.user_id,
                "chat_id": st.session_state.chat_id,
                "question": prompt
            }
        ).json()

        st.session_state.chat_id = response["chat_id"]

        with st.chat_message("assistant"):
            st.markdown(response["answer"])

# -------- Upload Tab --------
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
