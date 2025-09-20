import requests
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime
import logging
import os
import time
import xml.etree.ElementTree as ET

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- RSS Feeds ---
RSS_FEEDS = [
    # CNBC feeds
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",  # Markets
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",  # Business
    "https://www.cnbc.com/id/10000108/device/rss/rss.html",  # World
    "https://www.cnbc.com/id/10001054/device/rss/rss.html",  # Economy
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",  # Technology
    "https://www.cnbc.com/id/10000113/device/rss/rss.html",  # Politics
    "https://www.cnbc.com/id/10000116/device/rss/rss.html",  # Health Care
    "https://www.cnbc.com/id/10000739/device/rss/rss.html",  # Real Estate
    "https://www.cnbc.com/id/100646281/device/rss/rss.html", # Personal Finance
    "https://www.cnbc.com/id/10000115/device/rss/rss.html",  # Lifestyle

    # Financial Times feeds
    "https://www.ft.com/rss/world",
    "https://www.ft.com/rss/companies",
    "https://www.ft.com/rss/markets",
    "https://www.ft.com/rss/opinion",
    "https://www.ft.com/rss/uk"
]

def fetch_rss_headlines(url, retries=3, backoff=2):
    """Fetch headlines from RSS feed with retry + backoff."""
    headlines = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            for item in root.findall(".//item/title"):
                headlines.append(item.text.strip())

            logging.info(f"{url} → {len(headlines)} headlines")
            return headlines

        except Exception as e:
            wait = backoff ** attempt
            logging.warning(f"Retry {attempt+1}/{retries} for {url} in {wait}s")
            time.sleep(wait)

    logging.warning(f"Skipping {url} after {retries} failed attempts")
    return headlines

def analyze_sentiment(headlines):
    sid = SentimentIntensityAnalyzer()
    results = []
    for headline in headlines:
        blob = TextBlob(headline)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        vader_scores = sid.polarity_scores(headline)
        compound = vader_scores["compound"]

        if compound >= 0.05:
            sentiment = "Positive"
        elif compound <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        results.append({
            "Headline": headline,
            "TextBlob Polarity": polarity,
            "TextBlob Subjectivity": subjectivity,
            "VADER Compound Score": compound,
            "Overall Sentiment": sentiment
        })
    return results

def save_results(data):
    if not data:
        logging.warning("No data to save.")
        return None
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(BASE_DIR, f"financial_sentiment_report_{timestamp}.csv")
    xlsx_file = os.path.join(BASE_DIR, f"financial_sentiment_report_{timestamp}.xlsx")
    df.to_csv(csv_file, index=False)
    df.to_excel(xlsx_file, index=False)
    logging.info(f"Saved CSV: {csv_file}")
    logging.info(f"Saved Excel: {xlsx_file}")
    return df

def visualize_sentiment(df):
    counts = df["Overall Sentiment"].value_counts()
    plt.figure(figsize=(6,4))
    counts.plot(kind="bar", color=["green","red","gray"])
    plt.title("Financial News Sentiment Distribution")
    plt.xlabel("Sentiment")
    plt.ylabel("Number of Headlines")
    plt.xticks(rotation=0)
    plt.tight_layout()
    chart_file = os.path.join(BASE_DIR, "sentiment_distribution.png")
    plt.savefig(chart_file)
    plt.close()
    logging.info(f"Saved chart: {chart_file}")

def summarize_sentiment(df):
    summary = df["Overall Sentiment"].value_counts(normalize=True) * 100
    logging.info("Market Sentiment Summary:")
    for sentiment, pct in summary.items():
        logging.info(f"{sentiment}: {pct:.1f}%")
    return summary

def main():
    logging.info("Starting Stable Multi-RSS Analyzer...")
    all_headlines = []
    for feed in RSS_FEEDS:
        all_headlines.extend(fetch_rss_headlines(feed))
    unique_headlines = list(set(all_headlines))
    logging.info(f"Total unique headlines collected: {len(unique_headlines)}")
    if unique_headlines:
        results = analyze_sentiment(unique_headlines)
        df = save_results(results)
        if df is not None:
            visualize_sentiment(df)
            summarize_sentiment(df)
    else:
        logging.warning("No headlines retrieved.")
    logging.info("Process finished.")

if __name__ == "__main__":
    main()
