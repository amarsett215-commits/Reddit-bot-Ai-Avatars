import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class NicheCandidate:
    """A potential niche identified from the data."""
    name: str
    category: str
    description: str = ""
    subreddits: list = field(default_factory=list)
    quora_questions: list = field(default_factory=list)
    total_posts: int = 0
    total_engagement: int = 0
    total_comments: int = 0
    avg_post_score: float = 0
    subscriber_reach: int = 0
    cross_subreddit_count: int = 0
    content_velocity: float = 0.0  # posts per day on topic
    top_posts: list = field(default_factory=list)
    nlp_scores: dict = field(default_factory=dict)
    themes: dict = field(default_factory=dict)
    quora_question_count: int = 0
    scores: dict = field(default_factory=dict)
    super_niche_score: float = 0.0


class DemandAnalyzer:
    """Analyzes scraped data to identify and validate niche demand."""

    def __init__(self, nlp_engine):
        self.nlp = nlp_engine

    def analyze(self, reddit_data, quora_data=None):
        """
        Takes raw scraped data, runs NLP, clusters into niche candidates.
        Returns list of NicheCandidate objects.
        """
        # Step 1: Analyze all Reddit posts with NLP
        all_analyzed = []
        category_posts = defaultdict(list)

        print("\n  Running NLP analysis on scraped posts...")

        for category, subreddit_list in reddit_data.items():
            for sub_data in subreddit_list:
                for post in sub_data.posts:
                    analysis = self.nlp.analyze_post(post)
                    analysis["category"] = category
                    analysis["subscribers"] = sub_data.subscribers
                    all_analyzed.append(analysis)
                    category_posts[category].append(analysis)

        print(f"  Analyzed {len(all_analyzed)} posts across {len(category_posts)} categories")

        # Step 2: Cluster into niche candidates by category
        niches = []
        for category, posts in category_posts.items():
            niche = self._build_niche_from_posts(category, posts, reddit_data)

            # Enrich with Quora data if available
            if quora_data and category in quora_data:
                quora_qs = quora_data[category]
                niche.quora_questions = [q.question for q in quora_qs[:20]]
                niche.quora_question_count = len(quora_qs)

            niches.append(niche)

        # Step 3: Sub-cluster within large categories
        # If a category has 100+ posts, look for sub-niches
        expanded_niches = []
        for niche in niches:
            if niche.total_posts > 80:
                sub_niches = self._find_sub_niches(niche, category_posts[niche.category])
                expanded_niches.extend(sub_niches)
            else:
                expanded_niches.append(niche)

        # Step 4: Calculate content velocity
        for niche in expanded_niches:
            self._calculate_velocity(niche)

        print(f"  Identified {len(expanded_niches)} niche candidates")
        return expanded_niches

    def _build_niche_from_posts(self, category, analyzed_posts, reddit_data):
        """Build a NicheCandidate from analyzed posts in a category."""
        niche = NicheCandidate(
            name=self._category_to_name(category),
            category=category,
        )

        # Gather subreddit info
        if category in reddit_data:
            for sub_data in reddit_data[category]:
                niche.subreddits.append(sub_data.name)
                niche.subscriber_reach += sub_data.subscribers

        niche.cross_subreddit_count = len(niche.subreddits)
        niche.total_posts = len(analyzed_posts)

        # Aggregate engagement
        niche.total_engagement = sum(
            p.get("raw_engagement", 0) for p in analyzed_posts
        )
        if niche.total_posts > 0:
            niche.avg_post_score = niche.total_engagement / niche.total_posts

        # Aggregate NLP scores
        score_keys = [
            "desperation_score", "payment_intent_score",
            "viral_potential_score", "emotional_intensity",
        ]
        avg_scores = {}
        for key in score_keys:
            values = [p.get(key, 0) for p in analyzed_posts]
            avg_scores[key] = sum(values) / len(values) if values else 0
        niche.nlp_scores = avg_scores

        # Get top posts by engagement
        sorted_posts = sorted(
            analyzed_posts, key=lambda x: x.get("raw_engagement", 0), reverse=True
        )
        niche.top_posts = sorted_posts[:15]

        # Extract themes
        niche.themes = self.nlp.extract_themes(analyzed_posts)

        return niche

    def _find_sub_niches(self, parent_niche, analyzed_posts):
        """
        Split a large niche into sub-niches based on keyword clusters.
        Only split if there are genuinely distinct sub-topics with enough
        posts each. Filters out generic words that don't make good niche names.
        """
        themes = self.nlp.extract_themes(analyzed_posts, min_frequency=5)
        top_keywords = themes.get("top_keywords", [])

        if len(top_keywords) < 3:
            return [parent_niche]

        # Filter out words that don't make meaningful niche names
        junk_words = {
            "years", "days", "day", "time", "people", "life", "thing",
            "things", "lot", "way", "guy", "girl", "feel", "post",
            "week", "month", "year", "ago", "old", "new", "good",
            "bad", "best", "worst", "big", "small", "long", "short",
            "really", "actually", "literally", "basically", "getting",
            "started", "start", "help", "advice", "question", "update",
            "rant", "story", "experience", "first", "last", "back",
            "found", "need", "want", "looking", "trying", "anyone",
            "does", "much", "many", "made", "making", "work", "working",
        }
        valid_keywords = [
            kw for kw in top_keywords
            if kw["word"] not in junk_words and len(kw["word"]) > 3
        ]

        if len(valid_keywords) < 2:
            return [parent_niche]

        # Group posts by dominant keyword
        sub_groups = defaultdict(list)
        keyword_list = [kw["word"] for kw in valid_keywords[:5]]

        for post in analyzed_posts:
            title = post.get("post_title", "").lower()
            best_kw = None
            best_count = 0
            for kw in keyword_list:
                if kw in title:
                    count = title.count(kw)
                    if count > best_count:
                        best_count = count
                        best_kw = kw
            if best_kw:
                sub_groups[best_kw].append(post)
            else:
                sub_groups["_general"].append(post)

        # Only create sub-niches with 8+ posts (meaningful cluster)
        sub_niches = []
        for keyword, posts in sub_groups.items():
            if keyword == "_general" or len(posts) < 8:
                continue

            # Build a meaningful sub-niche name
            sub_name = self._make_sub_niche_name(keyword, parent_niche.name, posts)
            sub_niche = NicheCandidate(
                name=sub_name,
                category=parent_niche.category,
                subreddits=parent_niche.subreddits,
                subscriber_reach=parent_niche.subscriber_reach,
                cross_subreddit_count=parent_niche.cross_subreddit_count,
                quora_questions=parent_niche.quora_questions,
                quora_question_count=parent_niche.quora_question_count,
            )
            sub_niche.total_posts = len(posts)
            sub_niche.total_engagement = sum(p.get("raw_engagement", 0) for p in posts)
            sub_niche.avg_post_score = (
                sub_niche.total_engagement / sub_niche.total_posts
                if sub_niche.total_posts > 0
                else 0
            )

            score_keys = [
                "desperation_score", "payment_intent_score",
                "viral_potential_score", "emotional_intensity",
            ]
            avg_scores = {}
            for key in score_keys:
                values = [p.get(key, 0) for p in posts]
                avg_scores[key] = sum(values) / len(values) if values else 0
            sub_niche.nlp_scores = avg_scores
            sub_niche.top_posts = sorted(
                posts, key=lambda x: x.get("raw_engagement", 0), reverse=True
            )[:15]
            sub_niche.themes = self.nlp.extract_themes(posts)

            sub_niches.append(sub_niche)

        # Always keep parent niche, add sub-niches alongside it
        if not sub_niches:
            return [parent_niche]

        return [parent_niche] + sub_niches

    def _calculate_velocity(self, niche):
        """Estimate posts per day for this niche."""
        if not niche.top_posts:
            niche.content_velocity = 0
            return

        # Use post timestamps to estimate velocity
        timestamps = []
        for p in niche.top_posts:
            # We don't store created_utc in analyzed data, estimate from count
            pass

        # Rough estimate: posts found / 30 days (we scraped ~1 month of data)
        niche.content_velocity = niche.total_posts / 30.0

    def _make_sub_niche_name(self, keyword, parent_name, posts):
        """Create a meaningful sub-niche name from keyword + context."""
        # Check if we can find a better two-word phrase in the posts
        import re
        from collections import Counter

        phrase_counter = Counter()
        for post in posts:
            title = post.get("post_title", "").lower()
            # Find two-word phrases containing the keyword
            words = re.findall(r"[a-z]+", title)
            for i in range(len(words) - 1):
                if words[i] == keyword or words[i + 1] == keyword:
                    phrase = f"{words[i]} {words[i + 1]}"
                    if len(phrase) > 5:
                        phrase_counter[phrase] += 1

        # Use the most common phrase if it appears 3+ times
        if phrase_counter:
            best_phrase, count = phrase_counter.most_common(1)[0]
            if count >= 3:
                return f"{parent_name}: {best_phrase.title()}"

        return f"{parent_name}: {keyword.title()}"

    def _category_to_name(self, category):
        """Convert category slug to human name."""
        names = {
            "money_and_career": "Money & Career",
            "relationships_and_dating": "Relationships & Dating",
            "health_and_fitness": "Health & Fitness",
            "self_improvement": "Self Improvement",
            "parenting_and_family": "Parenting & Family",
            "tech_and_skills": "Tech & Skills",
            "housing_and_living": "Housing & Living",
            "legal_and_life_crises": "Legal & Life Crises",
        }
        return names.get(category, category.replace("_", " ").title())
