"""Streamlit UI for Vectorless RAG Chatbot."""

import os
import tempfile
import streamlit as st
from src.document_processor import DocumentProcessor
from src.retriever import BM25Retriever
from src.chat_engine import ChatEngine


def main():
    st.set_page_config(page_title="Vectorless RAG Chatbot", layout="wide")
    st.title("📄 Vectorless RAG Chatbot")
    st.caption(
        "Upload documents, then ask questions. Answers are grounded in your documents using keyword search (no embeddings)."
    )

    # Initialize session state
    if "processor" not in st.session_state:
        st.session_state.processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    if "retriever" not in st.session_state:
        st.session_state.retriever = BM25Retriever(top_k=5)
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = ChatEngine()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "docs_loaded" not in st.session_state:
        st.session_state.docs_loaded = False

    # Sidebar: Document upload
    with st.sidebar:
        st.header("📁 Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF, TXT, or MD files",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            file_names = [f.name for f in uploaded_files]
            st.info(f"{len(uploaded_files)} file(s) selected: {', '.join(file_names)}")

            if st.button("🔄 Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    all_chunks = []
                    for uploaded_file in uploaded_files:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                        ) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        try:
                            chunks = st.session_state.processor.process_file(tmp_path)
                            all_chunks.extend(chunks)
                        finally:
                            os.unlink(tmp_path)

                    # Reset and reindex
                    st.session_state.retriever.reset()
                    st.session_state.retriever.add_chunks(all_chunks)
                    st.session_state.docs_loaded = True
                    st.session_state.messages = []
                    st.success(
                        f"✅ Processed {len(all_chunks)} chunks from {len(uploaded_files)} file(s)"
                    )

        if st.session_state.docs_loaded:
            st.success(f"📚 {len(st.session_state.retriever.chunks)} chunks indexed")
            if st.button("🗑️ Clear Documents"):
                st.session_state.retriever.reset()
                st.session_state.docs_loaded = False
                st.session_state.messages = []
                st.rerun()

    # Main area: Chat interface
    if not st.session_state.docs_loaded:
        st.warning("👈 Upload and process documents to get started.")
        return

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if query := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        # Retrieve relevant chunks
        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                results = st.session_state.retriever.retrieve(query)

            if results:
                # Show sources
                with st.expander("📋 Sources"):
                    for i, (chunk, source, score) in enumerate(results, 1):
                        st.markdown(f"**Source {i}:** `{source}` (score: {score:.3f})")
                        st.text(chunk[:200] + "...")

                # Generate answer
                with st.spinner("Generating answer..."):
                    try:
                        answer = st.session_state.chat_engine.answer(query, results)
                        st.write(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )
                    except Exception as e:
                        error_msg = f"❌ Error generating answer: {str(e)}"
                        st.error(error_msg)
                        if (
                            "API key" in str(e).lower()
                            or "authentication" in str(e).lower()
                        ):
                            st.info(
                                "Make sure your API key is set in the `.env` file or environment variables."
                            )
            else:
                no_results = "No relevant information found in the documents for this query. Try rephrasing your question."
                st.warning(no_results)
                st.session_state.messages.append(
                    {"role": "assistant", "content": no_results}
                )


if __name__ == "__main__":
    main()
