#!/usr/bin/env python3
# poke_scraper.py

import argparse
import os
import time
import re
import logging
from urllib.parse import urljoin, urlparse, unquote
from dataclasses import dataclass
from typing import Optional
import requests
from bs4 import BeautifulSoup

@dataclass
class CreatureData:
    index: int
    name: str
    url: str
    image_url: Optional[str] = None

def sanitize_filename(name: str) -> str:
    name = unquote(name)
    return re.sub(r"[^\w\-.]+", "_", name).strip("_")

class WebScraper:
    def __init__(self, base_url: str, delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def fetch_page(self, url: str) -> BeautifulSoup:
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def extract_creature_data(self, element) -> Optional[CreatureData]:
        cells = element.find_all("td")
        if len(cells) < 3:
            return None

        index_match = re.search(r"\d+", cells[0].get_text(strip=True))
        if not index_match:
            return None

        link_element = element.find("a", href=True)
        if not link_element:
            return None

        return CreatureData(
            index=int(index_match.group()),
            name=link_element.get_text(strip=True),
            url=urljoin(self.base_url, link_element["href"])
        )

class ImageDownloader:
    def __init__(self, output_dir: str = "collected_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_image(self, url: str, filename: str) -> bool:
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}")
            return False

class DataCollector:
    def __init__(self, output_dir: str = "collected_data", delay: float = 1.0):
        self.base_url = "https://bulbapedia.bulbagarden.net"
        self.list_url = f"{self.base_url}/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"
        self.scraper = WebScraper(self.base_url, delay=delay)
        self.downloader = ImageDownloader(output_dir)

    def find_creature_image(self, url: str) -> Optional[str]:
        try:
            soup = self.scraper.fetch_page(url)
            info_table = soup.find("table", {"class": re.compile(r"infobox|roundy")})
            if not info_table:
                return None
            img_tag = info_table.find("img")
            if not img_tag or not img_tag.get("src"):
                return None
            src = img_tag["src"]
            return f"https:{src}" if src.startswith("//") else src
        except Exception:
            return None

    def collect_data(self, limit: Optional[int] = None):
        soup = self.scraper.fetch_page(self.list_url)
        tables = soup.find_all("table", {"class": re.compile(r"(roundy|sortable)")})

        count = 0
        for table in tables:
            for row in table.find_all("tr"):
                creature = self.scraper.extract_creature_data(row)
                if not creature:
                    continue

                logging.info(f"Processing #{creature.index:04d} {creature.name}")

                image_url = self.find_creature_image(creature.url)
                if not image_url:
                    logging.warning(f"No image found for {creature.name}")
                    continue

                ext = os.path.splitext(urlparse(image_url).path)[-1] or ".png"
                safe_name = sanitize_filename(creature.name)
                filename = f"{self.downloader.output_dir}/{creature.index:04d}_{safe_name}{ext}"

                if self.downloader.save_image(image_url, filename):
                    logging.info(f"Saved {filename}")

                count += 1
                if limit and count >= limit:
                    logging.info(f"Limit {limit} reached, stopping.")
                    return

                time.sleep(self.scraper.delay)

def main():
    parser = argparse.ArgumentParser(description="Scrape Pokémon images from Bulbapedia")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of Pokémon to download")
    parser.add_argument("--output", type=str, default="collected_data", help="Output directory")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s - %(levelname)s - %(message)s")

    collector = DataCollector(output_dir=args.output, delay=args.delay)
    collector.collect_data(limit=args.limit)

if __name__ == "__main__":
    main()
