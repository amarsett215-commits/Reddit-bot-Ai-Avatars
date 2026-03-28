import random
import time
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

import config


@dataclass
class QuoraQuestion:
    question: str
    url: str
    answer_count: int = 0
    follower_count: int = 0
    top_answers: list = field(default_factory=list)


class QuoraScraper:
    """Scrapes Quora for high-demand questions in various topics."""

    BASE_URL = "https://www.quora.com"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Topics that map to our Reddit categories
    TOPIC_POOLS = {
        "money_and_career": [
            "Personal-Finance", "Investing", "Making-Money",
            "Career-Advice", "Side-Hustles", "Entrepreneurship",
            "Real-Estate-Investing", "Debt-Management",
            "Financial-Independence", "Freelancing",
        ],
        "relationships_and_dating": [
            "Dating-Advice", "Relationships", "Marriage",
            "Breakups", "Dating-and-Relationships",
            "Social-Skills", "Loneliness",
        ],
        "health_and_fitness": [
            "Weight-Loss", "Fitness", "Mental-Health",
            "Anxiety", "Depression", "Sleep", "Nutrition",
            "Skin-Care", "Hair-Loss",
        ],
        "self_improvement": [
            "Self-Improvement", "Productivity", "Habits",
            "Motivation", "Discipline", "Meditation",
            "Stoicism", "Goal-Setting",
        ],
        "parenting_and_family": [
            "Parenting", "Raising-Children", "Family",
            "New-Parents", "Teenagers",
        ],
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _scrape_topic(self, topic):
        """Scrape questions from a Quora topic page."""
        questions = []
        url = f"{self.BASE_URL}/topic/{topic}"

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return questions

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract questions from the page
            # Quora's structure changes often, so we look for common patterns
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                # Quora question URLs contain the question
                if (
                    len(text) > 20
                    and ("?" in text or "How" in text or "What" in text or "Why" in text)
                    and not text.startswith("http")
                ):
                    question_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    questions.append(
                        QuoraQuestion(
                            question=text,
                            url=question_url,
                        )
                    )

            # Also try searching for the topic
            search_questions = self._search_topic(topic)
            questions.extend(search_questions)

        except Exception as e:
            print(f"    Quora error for {topic}: {e}")

        # Deduplicate by question text
        seen = set()
        unique = []
        for q in questions:
            key = q.question.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(q)

        return unique

    def _search_topic(self, topic):
        """Search Quora for questions about a topic."""
        questions = []
        search_terms = topic.replace("-", " ")
        url = f"{self.BASE_URL}/search?q={search_terms}"

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return questions

            soup = BeautifulSoup(resp.text, "html.parser")

            for span in soup.find_all("span"):
                text = span.get_text(strip=True)
                if (
                    len(text) > 25
                    and len(text) < 300
                    and "?" in text
                ):
                    questions.append(
                        QuoraQuestion(
                            question=text,
                            url=url,
                        )
                    )
        except Exception:
            pass

        return questions

    def scrape(self, categories=None, progress_callback=None):
        """
        Scrape Quora topics. If categories provided, only scrape those.
        Returns dict of category -> list of QuoraQuestion.
        """
        if categories is None:
            categories = list(self.TOPIC_POOLS.keys())

        results = {}
        topics_to_scrape = []

        for cat in categories:
            if cat in self.TOPIC_POOLS:
                pool = self.TOPIC_POOLS[cat]
                chosen = random.sample(pool, min(3, len(pool)))
                for topic in chosen:
                    topics_to_scrape.append((topic, cat))

        total = len(topics_to_scrape)
        print(f"\n  Scanning {total} Quora topics...\n")

        for i, (topic, category) in enumerate(topics_to_scrape, 1):
            print(f"  [{i}/{total}] Quora: {topic}", end=" ... ", flush=True)

            if progress_callback:
                progress_callback(i, total, topic)

            questions = self._scrape_topic(topic)

            if category not in results:
                results[category] = []
            results[category].extend(questions)

            print(f"{len(questions)} questions found")
            time.sleep(1.5)  # Be respectful

        return results
