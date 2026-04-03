import requests
import re
import nltk
import matplotlib.pyplot as plt
from nltk.sentiment import SentimentIntensityAnalyzer
import numpy as np

from src.utils.summarizer import chunk_text
from src.utils.book_downloader import split_into_chapters

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

model_name = "j-hartmann/emotion-english-distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
TARGET_EMOTIONS = ["joy", "fear", "anger", "sadness"]

def get_emotion_scores(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=1).numpy()[0]
    return {emotion: float(probs[i]) for i, emotion in enumerate(EMOTIONS)}


#nltk.download('vader_lexicon')

# ---------------------------------------------------------
# 1. Download a Project Gutenberg book
# ---------------------------------------------------------
url = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt" #"https://www.gutenberg.org/cache/epub/84/pg84.txt"  # Pride and Prejudice
raw_text = requests.get(url).text

# ---------------------------------------------------------
# 2. Remove Gutenberg header/footer
# ---------------------------------------------------------
def strip_gutenberg(text):
    start = re.search(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .* \*\*\*", text)
    end = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK .* \*\*\*", text)

    if start and end:
        return text[start.end():end.start()]
    return text

clean_text = strip_gutenberg(raw_text)

# ---------------------------------------------------------
# 3. Split into chapters
# ---------------------------------------------------------
chapters = split_into_chapters(clean_text)

# ---------------------------------------------------------
# 4. Split into paragraphs
# ---------------------------------------------------------
chapter_boundaries = []
paragraphs = []
current_index = 0

for ch in chapters:
    # Count paragraphs in this chapter
    ch_paragraphs = chunk_text(ch["content"])
    paragraphs.extend(ch_paragraphs)
    chapter_boundaries.append({
        "title": ch["title"],
        "start_index": current_index
    })
    current_index += len(ch_paragraphs)


print(f"Total paragraphs: {len(paragraphs)}")

# ---------------------------------------------------------
# 5. Sentiment analysis per paragraph
# ---------------------------------------------------------
# sia = SentimentIntensityAnalyzer()

# sentiments = []
# for p in paragraphs:
#     score = sia.polarity_scores(p)["compound"]
#     sentiments.append(score)
emotion_series = {e: [] for e in TARGET_EMOTIONS}

for p in paragraphs:
    scores = get_emotion_scores(p)
    for e in TARGET_EMOTIONS:
        emotion_series[e].append(scores[e])

# ---------------------------------------------------------
# 6. Smooth the sentiment curve
# ---------------------------------------------------------
# def smooth(values, window=5):
#     return np.convolve(values, np.ones(window)/window, mode='same')

# smoothed = smooth(sentiments, window=7)
def smooth(values, window=7):
    return np.convolve(values, np.ones(window)/window, mode='same')

smoothed_emotions = {
    e: smooth(emotion_series[e], window=9)
    for e in TARGET_EMOTIONS
}

# ---------------------------------------------------------
# 7. Plot the emotional arc
# ---------------------------------------------------------
plt.figure(figsize=(18, 8))

colors = {
    "joy": "#f4c542",      # warm gold
    "fear": "#6a4c93",     # deep purple
    "anger": "#d1495b",    # muted red
    "sadness": "#3a7ca5"   # cool blue
}

for emotion in TARGET_EMOTIONS:
    y = smoothed_emotions[emotion]
    plt.plot(y, label=emotion.capitalize(), color=colors[emotion], linewidth=2.5)
    plt.fill_between(range(len(y)), y, alpha=0.08, color=colors[emotion])

# Chapter boundaries
for ch in chapter_boundaries:
    x = ch["start_index"]
    plt.axvline(x=x, color="gray", linestyle="--", alpha=0.3)
    plt.text(
        x, -0.015, ch["title"].replace("CHAPTER ", "Ch "),
        rotation=90, fontsize=7, color="gray", va="top"
    )

plt.title("Multi-Emotion Arc of the Book (Paragraph-Level)", fontsize=16, pad=20)
# plt.xlabel("Paragraph Index", fontsize=12)
plt.ylabel("Emotion Probability", fontsize=12)
plt.ylim(0, 0.5)
plt.grid(alpha=0.25)

# Legend outside the plot
plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)

plt.tight_layout()
plt.show()
