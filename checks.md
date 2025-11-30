Intermediate Requirements
- [ ] Duplicate and store articles in SQLite or CSV file
- [ ] Batch processing: summarize 10+ articles automatically.
- [ ] Implement text chunking and embeddings using a vector store (FAISS, Chroma, or
LangChain)
    - LLMs have context limits. You can’t just dump 300 pages of lecture notes into the
prompt every time the student asks a question.
- [ ] When the user asks a question:
    - Retrieve the top-k relevant chunks of text by semantic similarity.
    - Construct a context-aware prompt that includes only retrieved snippets
- [ ] Provide a simple chat-style interface:
    - Display the user question and model answer in conversation format.
    - Allow follow-up questions using recent context (basic short-term memory).
- [ ] Visualization: simple chart (e.g., bar plot of sentiments by source).

