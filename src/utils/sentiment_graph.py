import requests
import re
import nltk
import matplotlib.pyplot as plt
from nltk.sentiment import SentimentIntensityAnalyzer
import numpy as np

from src.utils.summarizer import chunk_text
from src.utils.book_downloader import split_into_chapters

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
sia = SentimentIntensityAnalyzer()

sentiments = []
for p in paragraphs:
    score = sia.polarity_scores(p)["compound"]
    sentiments.append(score)

# ---------------------------------------------------------
# 6. Smooth the sentiment curve
# ---------------------------------------------------------
def smooth(values, window=5):
    return np.convolve(values, np.ones(window)/window, mode='same')

smoothed = smooth(sentiments, window=7)

# ---------------------------------------------------------
# 7. Plot the emotional arc
# ---------------------------------------------------------
plt.figure(figsize=(14, 6))
plt.plot(sentiments, alpha=0.3, label="Raw sentiment", color="gray")
plt.plot(smoothed, label="Smoothed sentiment", color="blue", linewidth=2)

# Add chapter boundaries
for ch in chapter_boundaries:
    x = ch["start_index"]
    plt.axvline(x=x, color="red", linestyle="--", alpha=0.4)
    plt.text(x, 1.05, ch["title"], rotation=90, fontsize=8, color="red")

plt.title("Sentiment Arc of the Book (Paragraph-Level) with Chapter Boundaries")
plt.xlabel("Paragraph Index")
plt.ylabel("Sentiment Score (VADER Compound)")
plt.legend()
plt.grid(True)
plt.show()
