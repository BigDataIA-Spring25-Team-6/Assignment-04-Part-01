import streamlit as st
import requests
import os
import time

# FastAPI Backend URL
BASE_URL = "https://backend-541167511413.us-central1.run.app"

# Set up the page layout
st.set_page_config(page_title="PDF Analyzer", layout="centered")
st.title("PDF Analyzer with LLMs - Assignment 4 (Team 6)")

# === Initialize session state variables ===
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "New PDF"
if "summary_text" not in st.session_state:
    st.session_state["summary_text"] = ""
if "active_document_url" not in st.session_state:
    st.session_state["active_document_url"] = None
if "last_active_document" not in st.session_state:
    st.session_state["last_active_document"] = None
if "user_question" not in st.session_state:
    st.session_state["user_question"] = "" 
if "answer_text" not in st.session_state:
    st.session_state["answer_text"] = ""
if "question_input_key" not in st.session_state:
    st.session_state["question_input_key"] = 0 

# === Function to reset session state when switching tabs or selecting a new document ===
def reset_session():
    """Reset summary, document URL, user question, and answer text when switching tabs or selecting a new document."""
    st.session_state["summary_text"] = ""
    st.session_state["user_question"] = ""  
    st.session_state["answer_text"] = ""
    st.session_state["active_document_url"] = None
    st.session_state["last_active_document"] = None
    st.session_state["question_input_key"] += 1  # Change input key to force UI refresh

# === File Selection (Upload or Select Processed PDF) ===
st.markdown("### Upload a New PDF or Select a Processed PDF")

# Define tab selection
selected_tab = st.radio("Select an option:", ["New PDF", "Processed PDF"], horizontal=True)

# If user switches tabs, reset session state
if selected_tab != st.session_state["active_tab"]:
    st.session_state["active_tab"] = selected_tab
    reset_session()  # Reset everything when switching tabs

uploaded_document_url = None
selected_document_url = None

# === Tab 1: Upload & Process New PDF ===
if selected_tab == "New PDF":
    st.markdown("#### Upload New PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_upload")

    if uploaded_file and st.button("Process PDF"):
        st.write("Processing your PDF...")

        # Reset everything when a new file is uploaded
        reset_session()

        files = {"file": uploaded_file}
        response = requests.post(f"{BASE_URL}/upload_pdf/", files=files)

        if response.status_code == 200:
            data = response.json()
            st.success("PDF processed successfully!")
            st.session_state["active_document_url"] = data['markdown_s3_url']
        else:
            st.error(f"Failed to process PDF! Error: {response.text}")

# === Tab 2: Select a Processed PDF ===
elif selected_tab == "Processed PDF":
    st.markdown("#### Select a Previously Processed PDF")

    response = requests.get(f"{BASE_URL}/select_pdfcontent/")
    if response.status_code == 200:
        processed_pdfs = response.json().get("processed_pdfs", {})
        markdown_files = {
            os.path.basename(pdf_info["markdown"]): pdf_info["markdown"]
            for pdf_info in processed_pdfs.values()
        }
        markdown_files = {"Select a PDF": None, **markdown_files}

        selected_name = st.selectbox(
            "Choose a processed PDF:", 
            list(markdown_files.keys()), 
            key="processed_pdf_select"
        )

        # Reset everything (including question input) when selecting a new processed PDF
        if selected_name and markdown_files[selected_name] != st.session_state["active_document_url"]:
            reset_session()  # Ensures question field resets
            st.session_state["active_document_url"] = markdown_files[selected_name]
            st.write(f"Selected Markdown file: {selected_name}")

# === Choose LLM Model (Triggers Reset Like Document Selection) ===
st.markdown("### Choose an LLM Model")

# Track the previous LLM choice
previous_llm_choice = st.session_state.get("llm_choice", "select llm")

# LLM Dropdown
st.session_state["llm_choice"] = st.selectbox(
    "Select LLM Model:", 
    ["select llm", "gpt-4o", "gemini-flash", "deepseek", "claude", "grok"], 
    index=["select llm", "gpt-4o", "gemini-flash", "deepseek", "claude", "grok"].index(previous_llm_choice),
    key="llm_selection"
)

# **If LLM Model is changed, reset summary & question like when changing a document**
if st.session_state["llm_choice"] != previous_llm_choice:
    st.session_state["summary_text"] = ""
    st.session_state["user_question"] = ""  
    st.session_state["answer_text"] = ""
    st.session_state["question_input_key"] += 1


# === Summarization & Q&A Section ===
st.markdown("### Summarization & Q&A")

if st.session_state["active_document_url"]:
    st.write(f"**Active Document:** {st.session_state['active_document_url']}")
else:
    st.warning("No document selected. Please upload or select a processed PDF.")


# Summary
st.markdown("### Document Summary")

summary_status = st.empty()  

# Display summary
if st.session_state["summary_text"]:
    st.text_area(
        label="Generated Summary:",
        value=st.session_state["summary_text"],
        height=200,
        disabled=True
    )

#Summarization Button
if st.button("Summarize Document"):
    if not st.session_state["active_document_url"]:
        st.warning("Please select or upload a document before summarization.")
    elif st.session_state["llm_choice"] == "select llm":
        st.warning("Please select a valid LLM model.")
    else:
        # Update status before calling API
        summary_status.markdown("**Generating summary...**", unsafe_allow_html=True)

        response = requests.post(
            f"{BASE_URL}/summarize",
            json={"document_url": st.session_state["active_document_url"], "model_name": st.session_state["llm_choice"]}
        )

        if response.status_code == 200:
            task_id = response.json().get("task_id")

            summary = None
            input_tokens = None
            output_tokens = None
            cost = None

            for _ in range(30):
                result_response = requests.get(f"{BASE_URL}/get_result/{task_id}")
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    summary = result_data.get("result", "No summary available.")
                    input_tokens = result_data.get("input_tokens", "N/A")
                    output_tokens = result_data.get("output_tokens", "N/A")
                    cost = result_data.get("cost", "Cost unavailable.")
                    break
                else:
                    time.sleep(5)

            st.session_state["summary_text"] = summary
            st.session_state["input_tokens"] = input_tokens
            st.session_state["output_tokens"] = output_tokens
            st.session_state["summary_cost"] = cost

            summary_status.markdown("**Generated Summary:**", unsafe_allow_html=True)

            st.text_area(
                label="Generated Summary:",
                value=st.session_state["summary_text"],
                height=200,
                disabled=True
            )

            with st.expander("Token Usage & Cost Details"):
                st.markdown(f"**Total Cost:** {st.session_state['summary_cost']}")
                st.markdown(f"**Input Tokens (Prompt):** {st.session_state['input_tokens']}")
                st.markdown(f"**Output Tokens (Completion):** {st.session_state['output_tokens']}")
        else:
            st.error(f"Failed to generate summary: {response.text}")
            summary_status.empty()

# Q&A
st.markdown("### Ask a Question")

# Use a dynamic key to force UI update when switching documents
user_question = st.text_input(
    "Ask a question about the document:",
    value=st.session_state["user_question"],
    key=f"question_input_{st.session_state['question_input_key']}"
)

if st.button("Get Answer"):
    if not st.session_state["active_document_url"]:
        st.warning("Please select or upload a document before asking a question.")
    elif st.session_state["llm_choice"] == "select llm":
        st.warning("Please select a valid LLM model.")
    elif user_question:
        st.write(f"Finding answer for: {user_question}")
        response = requests.post(
            f"{BASE_URL}/ask_question",
            json={"document_url": st.session_state["active_document_url"], "question": user_question, "model_name": st.session_state["llm_choice"]}
        )

        if response.status_code == 200:
            task_id = response.json().get("task_id")

            answer_result = None
            input_tokens = None
            output_tokens = None
            cost = None

            for _ in range(30):
                result_response = requests.get(f"{BASE_URL}/get_result/{task_id}")
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    answer_result = result_data.get("result", "No answer found.")
                    input_tokens = result_data.get("input_tokens", "N/A")
                    output_tokens = result_data.get("output_tokens", "N/A")
                    cost = result_data.get("cost", "Cost unavailable.")
                    break  
                else:
                    time.sleep(5)

            st.session_state["answer_text"] = answer_result
            st.session_state["qa_input_tokens"] = input_tokens
            st.session_state["qa_output_tokens"] = output_tokens
            st.session_state["qa_cost"] = cost

            st.markdown("### Answer")
            st.write(st.session_state["answer_text"])

            with st.expander("Token Usage & Cost Details"):
                st.markdown(f"**Total Cost:** {st.session_state['qa_cost']}")
                st.markdown(f"**Input Tokens (Prompt):** {st.session_state['qa_input_tokens']}")
                st.markdown(f"**Output Tokens (Completion):** {st.session_state['qa_output_tokens']}")

        else:
            st.error(f"Failed to get answer: {response.text}")