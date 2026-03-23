def prepare_chapter_chunks(chapters, chunk_size=800, overlap=100):
    """
    Convert chapters into RAG-ready chunks.
    Returns list of dicts: [{chapter, chunk_id, text, title}, ...]
    """

    rag_chunks = []
    chunk_id = 0

    for idx, ch in enumerate(chapters, start=1):
        tokens = ch["content"].split()

        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = " ".join(chunk_tokens)

            rag_chunks.append({
                "chapter": idx,
                "title": ch["title"],
                "chunk_id": chunk_id,
                "text": chunk_text
            })

            chunk_id += 1
            i += chunk_size - overlap

    return rag_chunks
