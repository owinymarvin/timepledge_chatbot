import streamlit as st
import requests
import time


st.title("_DMARV_ :blue[LLM Chatbot] :sunglasses:")
st.header("Add docs to the vector store")
st.subheader("Add documents to the vector store to query them later", divider="red")

with st.sidebar:
    messages = st.container(height=300)
    if prompt := st.chat_input("Say something"):
        messages.chat_message("user").write(prompt)
        messages.chat_message("assistant").write(f"Echo: {prompt}")


prompt = st.chat_input(
    "Add a document to embed and store in the vector database",
    accept_file="multiple",
    file_type=["csv", "pdf", "docx", "txt", "md"],
    key="add_doc_prompt",
)
if prompt and prompt.text:
    st.markdown(prompt.text)
if prompt and prompt["files"]:
    st.image(prompt["files"][0])



with st.status("Downloading data...", expanded=True) as status:
    st.write("Searching for data...")
    time.sleep(2)
    st.write("Found URL.")
    time.sleep(1)
    st.write("Downloading data...")
    time.sleep(1)
    status.update(
        label="Download complete!", state="complete", expanded=False
    )

st.button("Rerun")