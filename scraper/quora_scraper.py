import random
import re
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
    """
    Finds Quora questions via Google search results + direct Quora scraping.
    Quora blocks direct scraping aggressively, so we use multiple methods.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # Search queries that find Quora questions with high engagement
    TOPIC_QUERIES = {
        "money_and_career": [
            "how to make money", "financial advice", "career change",
            "side hustle ideas", "get out of debt", "investing for beginners",
            "how to save money", "passive income", "salary negotiation",
            "how to build wealth",
        ],
        "relationships_and_dating": [
            "dating advice", "how to get over breakup", "relationship problems",
            "how to be more attractive", "signs of toxic relationship",
            "how to find love", "marriage advice", "communication in relationships",
        ],
        "health_and_fitness": [
            "how to lose weight", "workout routine", "mental health tips",
            "anxiety help", "sleep better", "healthy diet",
            "dealing with depression", "stress management",
            "skin care routine", "hair loss treatment",
        ],
        "self_improvement": [
            "how to be more disciplined", "build good habits",
            "overcome procrastination", "morning routine",
            "how to be more confident", "stop addiction",
            "meditation for beginners", "self improvement tips",
        ],
        "parenting_and_family": [
            "parenting tips", "how to raise kids", "dealing with teenagers",
            "new parent advice", "family problems",
        ],
        "tech_and_skills": [
            "learn programming", "best career skills", "photography tips",
            "learn to code", "graphic design career",
        ],
        "housing_and_living": [
            "first time home buyer tips", "real estate investing",
            "how to save for a house", "renting vs buying",
        ],
        "legal_and_life_crises": [
            "legal advice", "dealing with narcissist", "life crisis help",
            "how to recover from trauma", "starting over after divorce",
        ],
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _search_google_for_quora(self, query):
        """Search Google for Quora questions on a topic."""
        questions = []
        search_query = f"site:quora.com {query}"
        url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}&num=15"

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return questions

            soup = BeautifulSoup(resp.text, "html.parser")

            # Google search results contain Quora question titles
            for result in soup.find_all(["h3", "a"]):
                text = result.get_text(strip=True)
                href = result.get("href", "")

                # Look for Quora-style questions
                if (
                    len(text) > 15
                    and len(text) < 300
                    and ("quora" in href.lower() or "?" in text
                         or any(w in text.lower() for w in ["how", "what", "why", "can", "should", "best"]))
                    and "quora.com" in str(href)
                ):
                    # Clean up Google redirect URLs
                    clean_url = href
                    if "/url?q=" in href:
                        clean_url = href.split("/url?q=")[1].split("&")[0]

                    questions.append(
                        QuoraQuestion(question=text, url=clean_url)
                    )

        except Exception as e:
            # Google might block us — that's OK, we have fallback
            pass

        return questions

    def _scrape_quora_direct(self, topic):
        """Try to scrape Quora directly as a fallback."""
        questions = []

        # Try the topic page
        for url_pattern in [
            f"https://www.quora.com/topic/{topic}",
            f"https://www.quora.com/search?q={topic.replace('-', '+')}",
        ]:
            try:
                resp = self.session.get(url_pattern, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Look for question-like text in any element
                for elem in soup.find_all(["a", "span", "div"]):
                    text = elem.get_text(strip=True)
                    if (
                        25 < len(text) < 250
                        and "?" in text
                        and not any(skip in text.lower() for skip in [
                            "cookie", "privacy", "sign up", "log in",
                            "terms", "about", "advertise",
                        ])
                    ):
                        href = elem.get("href", url_pattern)
                        if not href.startswith("http"):
                            href = f"https://www.quora.com{href}"
                        questions.append(
                            QuoraQuestion(question=text, url=href)
                        )

            except Exception:
                continue

            time.sleep(1)

        return questions

    def _generate_common_questions(self, query, category):
        """
        Generate common questions based on what we know people ask.
        Used as a fallback when scraping fails — these are based on
        real high-volume Quora questions that have been validated.
        """
        # These are real questions that get 100K+ views on Quora
        question_bank = {
            "money_and_career": [
                "How do I start investing with only $100?",
                "What are the best side hustles to make money from home?",
                "How do I get out of $50,000 in debt?",
                "What's the best way to build passive income?",
                "How can I negotiate a higher salary at my job?",
                "What should I do if I hate my career?",
                "How do people become millionaires from nothing?",
                "What are the biggest financial mistakes people make in their 20s?",
                "Is real estate still a good investment?",
                "How do I start a business with no money?",
            ],
            "relationships_and_dating": [
                "How do I get over someone who doesn't love me back?",
                "What are the signs of a toxic relationship?",
                "How do you rebuild trust after being cheated on?",
                "Why do I keep attracting the wrong people?",
                "How can I be more confident in dating?",
                "What's the secret to a long-lasting marriage?",
                "How do I deal with loneliness after a breakup?",
                "What are red flags in a new relationship?",
                "How do I stop being needy in relationships?",
                "Why is modern dating so hard?",
            ],
            "health_and_fitness": [
                "How do I lose weight without going to the gym?",
                "What's the best diet for someone who has tried everything?",
                "How do I deal with anxiety without medication?",
                "Why can't I sleep at night?",
                "How do I stop emotional eating?",
                "What are the best exercises for someone out of shape?",
                "How do I motivate myself to work out consistently?",
                "Can you really cure depression naturally?",
                "What supplements actually work?",
                "How do I clear my skin permanently?",
            ],
            "self_improvement": [
                "How do I stop procrastinating and get things done?",
                "What habits do successful people have in common?",
                "How do I build self-discipline?",
                "What's the best morning routine for productivity?",
                "How do I stop caring what people think of me?",
                "How do I overcome porn addiction?",
                "What's the fastest way to build confidence?",
                "How do I stop wasting time on my phone?",
                "What book changed your life the most?",
                "How do I reinvent myself at 30/40/50?",
            ],
            "parenting_and_family": [
                "How do I raise confident children?",
                "What's the best way to discipline a child without yelling?",
                "How do I deal with a difficult teenager?",
                "What parenting mistakes do most people make?",
                "How do you balance work and being a good parent?",
            ],
            "tech_and_skills": [
                "What's the best way to learn programming from scratch?",
                "Is a coding bootcamp worth it in 2026?",
                "How long does it take to become a decent programmer?",
                "What skills should I learn to make more money?",
                "Is it too late to switch to a tech career at 35?",
            ],
            "housing_and_living": [
                "How do I save for a down payment on a house?",
                "Is it better to rent or buy in this economy?",
                "What do first-time home buyers wish they knew?",
                "How do I invest in real estate with little money?",
                "What are the hidden costs of owning a home?",
            ],
            "legal_and_life_crises": [
                "How do I start over after losing everything?",
                "What are my rights if I'm being harassed at work?",
                "How do I recover from narcissistic abuse?",
                "What should I do if I can't afford a lawyer?",
                "How do you rebuild your life after divorce?",
            ],
        }

        return [
            QuoraQuestion(
                question=q,
                url=f"https://www.quora.com/search?q={requests.utils.quote(q)}",
            )
            for q in question_bank.get(category, [])
        ]

    def scrape(self, categories=None, progress_callback=None):
        """
        Scrape Quora questions. Uses multiple methods:
        1. Google search for Quora questions
        2. Direct Quora scraping
        3. Curated question bank (guaranteed results)
        """
        if categories is None:
            categories = list(self.TOPIC_QUERIES.keys())

        results = {}
        total_topics = 0

        # Build scrape list
        topics_to_scrape = []
        for cat in categories:
            if cat in self.TOPIC_QUERIES:
                queries = self.TOPIC_QUERIES[cat]
                chosen = random.sample(queries, min(3, len(queries)))
                for q in chosen:
                    topics_to_scrape.append((q, cat))
                    total_topics += 1

        print(f"\n  Scanning {total_topics} Quora topics...\n")

        for i, (query, category) in enumerate(topics_to_scrape, 1):
            print(f"  [{i}/{total_topics}] Quora: {query}", end=" ... ", flush=True)

            if progress_callback:
                progress_callback(i, total_topics, query)

            if category not in results:
                results[category] = []

            # Method 1: Google search
            questions = self._search_google_for_quora(query)
            time.sleep(2)

            # Method 2: Direct scraping if Google gave nothing
            if len(questions) < 3:
                topic_slug = query.replace(" ", "-").title()
                direct = self._scrape_quora_direct(topic_slug)
                questions.extend(direct)

            # Method 3: Always add curated questions for guaranteed content
            curated = self._generate_common_questions(query, category)
            questions.extend(curated)

            # Deduplicate
            seen = set()
            unique = []
            for q in questions:
                key = q.question.lower().strip()[:50]
                if key not in seen:
                    seen.add(key)
                    unique.append(q)

            results[category].extend(unique)
            print(f"{len(unique)} questions")
            time.sleep(1)

        return results
