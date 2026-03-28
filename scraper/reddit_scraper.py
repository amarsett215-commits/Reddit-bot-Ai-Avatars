import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

import praw
from prawcore.exceptions import (
    Forbidden,
    NotFound,
    TooManyRequests,
    ServerError,
)

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
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )
        self.reddit.read_only = True

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

    def _safe_fetch(self, func, *args, retries=3, **kwargs):
        """Fetch with retry logic for rate limits and server errors."""
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except TooManyRequests:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
            except (Forbidden, NotFound) as e:
                print(f"    Skipping (access error): {e}")
                return None
            except ServerError:
                time.sleep(2)
            except Exception as e:
                print(f"    Error: {e}")
                return None
        return None

    def _scrape_subreddit(self, sub_name):
        """Scrape a single subreddit for high-engagement posts."""
        subreddit = self._safe_fetch(lambda: self.reddit.subreddit(sub_name))
        if subreddit is None:
            return None

        try:
            subscribers = subreddit.subscribers or 0
        except Exception:
            subscribers = 0

        data = SubredditData(name=sub_name, subscribers=subscribers)
        posts_found = []

        # Grab hot + top (month) for a mix of trending and proven content
        for sort_method in ["hot", "top"]:
            try:
                if sort_method == "hot":
                    listing = subreddit.hot(limit=config.REDDIT_POST_LIMIT // 2)
                else:
                    listing = subreddit.top(
                        time_filter="month",
                        limit=config.REDDIT_POST_LIMIT // 2,
                    )

                for post in listing:
                    if post.score < config.MIN_UPVOTES:
                        continue
                    if post.num_comments < config.MIN_COMMENTS:
                        continue
                    if post.stickied:
                        continue

                    # Grab top comments
                    top_comments = []
                    try:
                        post.comment_sort = "top"
                        post.comments.replace_more(limit=0)
                        for comment in post.comments[:config.COMMENT_DEPTH]:
                            if hasattr(comment, "body"):
                                top_comments.append({
                                    "body": comment.body,
                                    "score": comment.score,
                                })
                    except Exception:
                        pass

                    reddit_post = RedditPost(
                        title=post.title,
                        selftext=post.selftext[:2000] if post.selftext else "",
                        score=post.score,
                        num_comments=post.num_comments,
                        subreddit=sub_name,
                        url=f"https://reddit.com{post.permalink}",
                        created_utc=post.created_utc,
                        top_comments=top_comments,
                        awards=post.total_awards_received,
                    )
                    posts_found.append(reddit_post)
            except Exception as e:
                print(f"    Error fetching {sort_method} from r/{sub_name}: {e}")
                continue

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

            # Small delay to respect rate limits
            time.sleep(0.5)

        return dict(results)
