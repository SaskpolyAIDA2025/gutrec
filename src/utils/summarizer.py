from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "facebook/bart-large-cnn"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


def summarize_chunk(text, max_len=200, min_len=50):
    """
    Returns: Summary of the given text.
    """
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=max_len,
        min_length=min_len,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def chunk_text(text, max_tokens=900, overlap=100):
    """
    Returns: text divided in chunks.
    """
    tokens = tokenizer.tokenize(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))
        i += max_tokens - overlap
    return chunks

def summarize_long(text):
    """
    Returns: Summary of the given (long) text.
    """
    chunks = chunk_text(text)

    # Summarize each chunk
    partial_summaries = [summarize_chunk(chunk) for chunk in chunks]

    # Combine summaries
    combined = " ".join(partial_summaries)

    # Final summary pass
    final_summary = summarize_chunk(combined, max_len=180, min_len=60)

    return final_summary
