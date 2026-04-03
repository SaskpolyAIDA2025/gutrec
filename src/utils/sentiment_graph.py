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
# 3. Split into paragraphs
# ---------------------------------------------------------
paragraphs = chunk_text(clean_text)
#paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 0]

print(f"Total paragraphs: {len(paragraphs)}")

# ---------------------------------------------------------
# 4. Sentiment analysis per paragraph
# ---------------------------------------------------------
sia = SentimentIntensityAnalyzer()

sentiments = []
for p in paragraphs:
    score = sia.polarity_scores(p)["compound"]
    sentiments.append(score)

# ---------------------------------------------------------
# 5. Smooth the sentiment curve
# ---------------------------------------------------------
def smooth(values, window=5):
    return np.convolve(values, np.ones(window)/window, mode='same')

smoothed = smooth(sentiments, window=7)

# ---------------------------------------------------------
# 6. Plot the emotional arc
# ---------------------------------------------------------
plt.figure(figsize=(14, 6))
plt.plot(sentiments, alpha=0.3, label="Raw sentiment", color="gray")
plt.plot(smoothed, label="Smoothed sentiment", color="blue", linewidth=2)
plt.title("Sentiment Arc of the Book (Paragraph-Level)")
plt.xlabel("Paragraph Index")
plt.ylabel("Sentiment Score (VADER Compound)")
plt.legend()
plt.grid(True)
plt.show()
