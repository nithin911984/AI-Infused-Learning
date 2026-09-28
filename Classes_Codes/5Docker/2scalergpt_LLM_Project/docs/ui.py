import streamlit as st
import requests

# Set up page configurations
st.set_page_config(page_title="ScalerGPT Chat", page_icon="📚", layout="centered")

st.title("📚 ScalerGPT AI Teaching Assistant")
st.caption("Ask questions grounded against your ChromaDB vector store documents.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if user_query := st.chat_input("What would you like to know? (e.g., What is Docker?)"):
    
    # 1. Display user message in chat UI
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Send request to your running FastAPI backend server
    FASTAPI_URL = "http://localhost:8000/ask"
    payload = {"query": user_query}
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("*Thinking...*")
        
        try:
            response = requests.post(FASTAPI_URL, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No response received.")
                sources = data.get("sources_used", 0)
                
                # Format the response with source metadata info
                full_response = f"{answer}\n\n---\n*📚 Sources referenced from ChromaDB: {sources}*"
                response_placeholder.markdown(full_response)
                
                # Save assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = f"⚠️ Backend error: {response.json().get('detail', 'Unknown error')}"
                response_placeholder.markdown(error_msg)
                
        except requests.exceptions.ConnectionError:
            response_placeholder.markdown("❌ Connection Error: Is your FastAPI server running on port 8000?")
