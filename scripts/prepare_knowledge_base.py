# Requires: pip install requests beautifulsoup4
import os
import csv
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

RAW_DIR = Path('data/medical_knowledge/raw')
PROCESSED_DIR = Path('data/medical_knowledge/processed')
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# File paths
SYMPTOMS_CSV = RAW_DIR / 'Disease_and_Symptoms.csv'
PRECAUTIONS_CSV = RAW_DIR / 'Disease_precaution.csv'
LINKS_TXT = RAW_DIR / 'health_sources_list.txt'

SYMPTOMS_OUT = PROCESSED_DIR / 'diseases_symptoms_cleaned.json'
PRECAUTIONS_OUT = PROCESSED_DIR / 'disease_precautions_cleaned.json'
SCRAPED_OUT = PROCESSED_DIR / 'scraped_sources.json'


def clean_csv(input_path, output_path, key_fields=None):
    """
    Reads a CSV, optionally deduplicates by key_fields, and writes as JSON.
    """
    data = []
    seen = set()
    with open(input_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if key_fields:
                key = tuple(row[k] for k in key_fields)
                if key in seen:
                    continue
                seen.add(key)
            data.append(row)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Processed {input_path} -> {output_path} ({len(data)} records)")


def process_csvs():
    """
    Process and clean the diseases/symptoms and precautions CSVs.
    """
    if SYMPTOMS_CSV.exists():
        clean_csv(SYMPTOMS_CSV, SYMPTOMS_OUT, key_fields=['disease', 'symptom'])
    else:
        print(f"Warning: {SYMPTOMS_CSV} not found.")
    if PRECAUTIONS_CSV.exists():
        clean_csv(PRECAUTIONS_CSV, PRECAUTIONS_OUT, key_fields=['disease'])
    else:
        print(f"Warning: {PRECAUTIONS_CSV} not found.")


def extract_text_from_html(html):
    """
    Extracts main text content from HTML using BeautifulSoup.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Remove scripts and styles
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    # Get text
    text = soup.get_text(separator=' ', strip=True)
    # Collapse whitespace
    return ' '.join(text.split())


def scrape_url(url, timeout=10):
    """
    Fetches the URL and extracts readable text. Returns None on failure.
    """
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = extract_text_from_html(resp.text)
        return text
    except Exception as e:
        print(f"[WARN] Could not scrape {url}: {e}")
        return None


def process_links():
    """
    Read health_sources_list.txt, scrape/download content, and output as JSON.
    Each entry: {url, content}
    """
    if not LINKS_TXT.exists():
        print(f"Warning: {LINKS_TXT} not found.")
        return
    with open(LINKS_TXT, encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]
    scraped = []
    for url in links:
        print(f"Scraping: {url}")
        content = scrape_url(url)
        scraped.append({"url": url, "content": content})
    with open(SCRAPED_OUT, 'w', encoding='utf-8') as f:
        json.dump(scraped, f, indent=2, ensure_ascii=False)
    print(f"Processed {LINKS_TXT} -> {SCRAPED_OUT} ({len(scraped)} links)")


def main():
    """
    Main entry point: process CSVs and links (with scraping).
    """
    process_csvs()
    process_links()
    print("Knowledge base preparation complete.")


if __name__ == "__main__":
    main() 