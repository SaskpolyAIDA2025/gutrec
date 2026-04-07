import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.utils.summarizer import chunk_text
from src.utils.book_downloader import split_into_chapters, download_gutenberg_book


model_name = "j-hartmann/emotion-english-distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
TARGET_EMOTIONS = ["joy", "fear", "anger", "sadness"]

# # ---------------------------------------------------------
# # Get the emotion score
# # ---------------------------------------------------------
def get_emotion_scores(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=1).numpy()[0]
    return {emotion: float(probs[i]) for i, emotion in enumerate(EMOTIONS)}


# # ---------------------------------------------------------
# # Smooth the sentiment curve
# # ---------------------------------------------------------
def smooth(values, window=7):
    return np.convolve(values, np.ones(window)/window, mode='same')


def build_emotion_arc_data(book_id: int):
    """
    Returns:
      - smoothed_emotions: dict {emotion: [values]}
      - chapter_boundaries: list of {title, start_index}
    """

    # ---------------------------------------------------------
    # Get book text (and chapters)
    # ---------------------------------------------------------
    # Download book and split into chapters
    text = download_gutenberg_book(book_id)
    chapters = split_into_chapters(text)

    if not chapters:
        return None  # caller can handle "no chapters" case

    # ---------------------------------------------------------
    # Split into paragraphs and track chapter boundaries
    # ---------------------------------------------------------
    chapter_boundaries = []
    paragraphs = []
    current_index = 0

    for ch in chapters:
        ch_paragraphs = chunk_text(ch["content"])
        paragraphs.extend(ch_paragraphs)
        chapter_boundaries.append({
            "title": ch["title"],
            "start_index": current_index
        })
        current_index += len(ch_paragraphs)

    if not paragraphs:
        return None

    # ---------------------------------------------------------
    # Emotion analysis per paragraph
    # ---------------------------------------------------------
    emotion_series = {e: [] for e in TARGET_EMOTIONS}

    for p in paragraphs:
        scores = get_emotion_scores(p)
        for e in TARGET_EMOTIONS:
            emotion_series[e].append(scores[e])

    # ---------------------------------------------------------
    # Smooth curves
    # ---------------------------------------------------------
    smoothed_emotions = {
        e: smooth(emotion_series[e], window=9)
        for e in TARGET_EMOTIONS
    }

    if smoothed_emotions and chapter_boundaries:
        return smoothed_emotions, chapter_boundaries
    else:
        return [], []


def plot_emotion_arc(smoothed_emotions, chapter_boundaries, visible_emotions):
    """
    Given a Gutenberg book id, returns a matplotlib Figure
    with the multi-emotion arc of the book.
    """
    # ---------------------------------------------------------
    # Build the figure (do NOT plt.show())
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(18, 8))

    colors = {
        "joy": "#f4c542",
        "fear": "#6a4c93",
        "anger": "#d1495b",
        "sadness": "#3a7ca5"
    }

    for emotion in visible_emotions:
        y = smoothed_emotions[emotion]
        ax.plot(y, label=emotion.capitalize(), color=colors[emotion], linewidth=2.5)
        ax.fill_between(range(len(y)), y, alpha=0.08, color=colors[emotion])

    # Chapter boundaries
    for ch in chapter_boundaries:
        x = ch["start_index"]
        ax.axvline(x=x, color="gray", linestyle="--", alpha=0.3)
        ax.text(
            x, -0.015, ch["title"].replace("CHAPTER ", "Ch "),
            rotation=90, fontsize=7, color="gray", va="top"
        )

    ax.set_title("Multi-Emotion Arc of the Book (Paragraph-Level)", fontsize=16, pad=20)
    ax.set_ylabel("Emotion Probability", fontsize=12)
    ax.set_ylim(0, 1.0)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)

    fig.tight_layout()
    return fig
