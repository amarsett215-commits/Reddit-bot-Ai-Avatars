import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

import requests

import config


@dataclass
class RedditPost:
    title: str
    selftext: str
    score: int
    num_comments: int
    subreddit: str
    url: str
    created_utc: float
    top_comments: list = field(default_factory=list)
    awards: int = 0


@dataclass
class SubredditData:
    name: str
    subscribers: int
    posts: list = field(default_factory=list)
    total_engagement: int = 0
    avg_comments: float = 0.0
    posts_per_day: float = 0.0


class RedditScraper:
    """
    Scrapes Reddit using public JSON endpoints (no API key needed).
    Every Reddit page is available as JSON by appending .json to the URL.
    """

    BASE_URL = "https://www.reddit.com"
    HEADERS = {
        "User-Agent": config.REDDIT_USER_AGENT,
        "Accept": "application/json",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _pick_subreddits(self, num_categories=4, subs_per_category=4):
        """Randomly select subreddits from the pool for this run."""
        categories = list(config.SUBREDDIT_POOLS.keys())
        chosen_categories = random.sample(
            categories, min(num_categories, len(categories))
        )
        selected = []
        for cat in chosen_categories:
            pool = config.SUBREDDIT_POOLS[cat]
            chosen = random.sample(pool, min(subs_per_category, len(pool)))
            selected.extend([(sub, cat) for sub in chosen])
        random.shuffle(selected)
        return selected

    def _fetch_json(self, url, retries=3):
        """Fetch a Reddit JSON endpoint with retry logic."""
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=15)

                if resp.status_code == 429:
                    wait = 2 ** (attempt + 2)
                    print(f"    Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                if resp.status_code == 403:
                    print("    Forbidden (private/quarantined)")
                    return None

                if resp.status_code == 404:
                    print("    Not found")
                    return None

                if resp.status_code >= 500:
                    time.sleep(2)
                    continue

                if resp.status_code == 200:
                    return resp.json()

            except requests.exceptions.Timeout:
                time.sleep(2)
            except requests.exceptions.JSONDecodeError:
                print("    Invalid JSON response")
                return None
            except Exception as e:
                print(f"    Error: {e}")
                return None

        return None

    def _get_subreddit_about(self, sub_name):
        """Get subreddit metadata (subscriber count, etc)."""
        url = f"{self.BASE_URL}/r/{sub_name}/about.json"
        data = self._fetch_json(url)
        if data and "data" in data:
            return data["data"]
        return None

    def _get_posts(self, sub_name, sort="hot", time_filter="month", limit=100):
        """Fetch posts from a subreddit."""
        if sort == "top":
            url = f"{self.BASE_URL}/r/{sub_name}/top.json?t={time_filter}&limit={limit}"
        else:
            url = f"{self.BASE_URL}/r/{sub_name}/{sort}.json?limit={limit}"

        all_posts = []
        after = None
        pages_fetched = 0
        max_pages = limit // 100 + 1

        while pages_fetched < max_pages:
            page_url = url
            if after:
                separator = "&" if "?" in url else "?"
                page_url = f"{url}{separator}after={after}"

            data = self._fetch_json(page_url)
            if not data or "data" not in data:
                break

            children = data["data"].get("children", [])
            if not children:
                break

            all_posts.extend(children)
            after = data["data"].get("after")
            pages_fetched += 1

            if not after:
                break

            time.sleep(1)  # Respect rate limits between pages

        return all_posts

    def _get_post_comments(self, permalink, limit=None):
        """Fetch top comments for a specific post."""
        if limit is None:
            limit = config.COMMENT_DEPTH
        url = f"{self.BASE_URL}{permalink}.json?sort=top&limit={limit}"
        data = self._fetch_json(url)

        comments = []
        if data and isinstance(data, list) and len(data) > 1:
            comment_listing = data[1].get("data", {}).get("children", [])
            for child in comment_listing[:limit]:
                if child.get("kind") == "t1":
                    comment_data = child.get("data", {})
                    comments.append({
                        "body": comment_data.get("body", ""),
                        "score": comment_data.get("score", 0),
                    })
        return comments

    def _scrape_subreddit(self, sub_name):
        """Scrape a single subreddit for high-engagement posts."""
        # Get subreddit info
        about = self._get_subreddit_about(sub_name)
        subscribers = about.get("subscribers", 0) if about else 0

        data = SubredditData(name=sub_name, subscribers=subscribers)
        posts_found = []

        # Grab hot + top (month) for a mix of trending and proven content
        for sort_method in ["hot", "top"]:
            raw_posts = self._get_posts(
                sub_name,
                sort=sort_method,
                limit=config.REDDIT_POST_LIMIT // 2,
            )

            for child in raw_posts:
                if child.get("kind") != "t3":
                    continue

                post_data = child.get("data", {})

                score = post_data.get("score", 0)
                num_comments = post_data.get("num_comments", 0)

                if score < config.MIN_UPVOTES:
                    continue
                if num_comments < config.MIN_COMMENTS:
                    continue
                if post_data.get("stickied", False):
                    continue

                permalink = post_data.get("permalink", "")

                # Fetch top comments for high-engagement posts
                top_comments = []
                if score >= config.MIN_UPVOTES * 2:
                    top_comments = self._get_post_comments(permalink)
                    time.sleep(0.5)  # Be nice to Reddit

                selftext = post_data.get("selftext", "") or ""

                reddit_post = RedditPost(
                    title=post_data.get("title", ""),
                    selftext=selftext[:2000],
                    score=score,
                    num_comments=num_comments,
                    subreddit=sub_name,
                    url=f"https://reddit.com{permalink}",
                    created_utc=post_data.get("created_utc", 0),
                    top_comments=top_comments,
                    awards=post_data.get("total_awards_received", 0),
                )
                posts_found.append(reddit_post)

        # Deduplicate by URL
        seen_urls = set()
        for p in posts_found:
            if p.url not in seen_urls:
                seen_urls.add(p.url)
                data.posts.append(p)

        if data.posts:
            data.total_engagement = sum(
                p.score + p.num_comments for p in data.posts
            )
            data.avg_comments = sum(p.num_comments for p in data.posts) / len(
                data.posts
            )

        return data

    def scrape(self, progress_callback=None):
        """Main scrape method. Returns dict of category -> list of SubredditData."""
        subreddits = self._pick_subreddits()
        results = defaultdict(list)
        total = len(subreddits)

        print(f"\n  Scanning {total} subreddits across random categories...\n")

        for i, (sub_name, category) in enumerate(subreddits, 1):
            label = f"  [{i}/{total}] r/{sub_name} ({category})"
            print(label, end=" ... ", flush=True)

            if progress_callback:
                progress_callback(i, total, sub_name)

            data = self._scrape_subreddit(sub_name)
            if data and data.posts:
                results[category].append(data)
                print(
                    f"{len(data.posts)} posts, "
                    f"{data.total_engagement:,} engagement"
                )
            else:
                print("skipped")

            # Delay between subreddits to avoid rate limiting
            time.sleep(1.5)

        return dict(results)
