import re
from collections import Counter

import config


class NLPEngine:
    """
    Lightweight NLP for analyzing Reddit/Quora text.
    Scores emotional intensity, desperation, payment signals, and viral potential.
    No heavy ML dependencies — pattern-based for speed and reliability.
    """

    def __init__(self):
        self.desperation_patterns = [
            re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
            for kw in config.DESPERATION_KEYWORDS
        ]
        self.payment_patterns = [
            re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
            for kw in config.PAYMENT_SIGNALS
        ]
        self.viral_patterns = [
            re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
            for kw in config.VIRAL_SIGNALS
        ]

    def analyze_text(self, text):
        """Analyze a single text block. Returns dict of scores."""
        if not text:
            return self._empty_scores()

        text_lower = text.lower()
        word_count = len(text.split())

        desperation_hits = sum(
            1 for p in self.desperation_patterns if p.search(text_lower)
        )
        payment_hits = sum(
            1 for p in self.payment_patterns if p.search(text_lower)
        )
        viral_hits = sum(
            1 for p in self.viral_patterns if p.search(text_lower)
        )

        # Normalize by text length (per 100 words)
        normalizer = max(word_count / 100, 1)

        return {
            "desperation_score": min(desperation_hits / normalizer * 25, 100),
            "payment_intent_score": min(payment_hits / normalizer * 30, 100),
            "viral_potential_score": min(viral_hits / normalizer * 20, 100),
            "emotional_intensity": self._emotional_intensity(text_lower),
            "question_density": self._question_density(text),
            "desperation_keywords_found": desperation_hits,
            "payment_keywords_found": payment_hits,
            "viral_keywords_found": viral_hits,
        }

    def _emotional_intensity(self, text):
        """Score emotional language intensity 0-100."""
        # Exclamation marks, ALL CAPS words, strong emotional words
        exclamations = text.count("!")
        caps_words = len(re.findall(r"\b[A-Z]{3,}\b", text))

        intensity_words = [
            "love", "hate", "amazing", "terrible", "worst", "best",
            "incredible", "awful", "insane", "crazy", "unbelievable",
            "devastating", "life-changing", "nightmare", "miracle",
            "obsessed", "furious", "ecstatic", "miserable", "thrilled",
            "heartbroken", "euphoric", "tormented", "blessed",
        ]
        emotion_hits = sum(1 for w in intensity_words if w in text)

        word_count = max(len(text.split()), 1)
        raw = (exclamations * 3 + caps_words * 2 + emotion_hits * 5)
        normalized = raw / (word_count / 100)
        return min(normalized * 10, 100)

    def _question_density(self, text):
        """How many questions are being asked — signals confusion/need for help."""
        questions = text.count("?")
        sentences = max(text.count(".") + text.count("!") + questions, 1)
        return min((questions / sentences) * 100, 100)

    def _empty_scores(self):
        return {
            "desperation_score": 0,
            "payment_intent_score": 0,
            "viral_potential_score": 0,
            "emotional_intensity": 0,
            "question_density": 0,
            "desperation_keywords_found": 0,
            "payment_keywords_found": 0,
            "viral_keywords_found": 0,
        }

    def analyze_post(self, post):
        """Analyze a Reddit post (title + body + comments)."""
        title_scores = self.analyze_text(post.title)
        body_scores = self.analyze_text(post.selftext)

        comment_scores = []
        for comment in post.top_comments:
            body = comment.get("body", "") if isinstance(comment, dict) else str(comment)
            cs = self.analyze_text(body)
            cs["comment_score"] = comment.get("score", 0) if isinstance(comment, dict) else 0
            comment_scores.append(cs)

        # Weighted combination: title matters most, then body, then comments
        combined = {}
        for key in title_scores:
            if isinstance(title_scores[key], (int, float)):
                title_val = title_scores[key]
                body_val = body_scores[key]
                comment_avg = (
                    sum(c[key] for c in comment_scores) / len(comment_scores)
                    if comment_scores
                    else 0
                )
                combined[key] = title_val * 0.4 + body_val * 0.3 + comment_avg * 0.3

        # Boost score based on engagement
        engagement_multiplier = 1.0
        if post.score > 1000:
            engagement_multiplier = 1.3
        elif post.score > 500:
            engagement_multiplier = 1.2
        elif post.score > 200:
            engagement_multiplier = 1.1

        if post.awards > 0:
            engagement_multiplier += 0.1 * min(post.awards, 5)

        for key in combined:
            combined[key] = min(combined[key] * engagement_multiplier, 100)

        combined["raw_engagement"] = post.score + post.num_comments
        combined["post_title"] = post.title
        combined["post_url"] = post.url
        combined["subreddit"] = post.subreddit

        return combined

    def extract_themes(self, analyzed_posts, min_frequency=3):
        """Extract common themes/topics from analyzed posts."""
        # Simple keyword extraction from titles
        stop_words = {
            "i", "me", "my", "we", "our", "you", "your", "it", "its",
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "am", "are",
            "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "can", "this", "that", "these", "those",
            "not", "no", "so", "if", "then", "than", "too", "very",
            "just", "about", "up", "out", "how", "what", "when", "where",
            "why", "who", "which", "there", "here", "all", "any", "both",
            "each", "few", "more", "most", "some", "such", "only", "own",
            "same", "into", "over", "after", "before", "between", "under",
            "again", "further", "once", "during", "while", "through",
            "don", "t", "s", "m", "ve", "re", "ll", "d", "didn",
            "doesn", "won", "isn", "aren", "wasn", "weren", "hasn",
            "haven", "hadn", "wouldn", "couldn", "shouldn", "like",
            "get", "got", "know", "think", "want", "need", "make",
            "going", "go", "one", "also", "still", "even", "much",
            "really", "way", "thing", "things", "people", "every",
            "anyone", "someone", "anything", "something", "nothing",
            "everything", "always", "never", "ever",
        }

        word_counter = Counter()
        bigram_counter = Counter()

        for post_data in analyzed_posts:
            title = post_data.get("post_title", "").lower()
            words = re.findall(r"[a-z]+", title)
            filtered = [w for w in words if w not in stop_words and len(w) > 2]

            word_counter.update(filtered)

            # Bigrams (two-word phrases)
            for i in range(len(filtered) - 1):
                bigram_counter[f"{filtered[i]} {filtered[i+1]}"] += 1

        themes = {
            "top_keywords": [
                {"word": w, "count": c}
                for w, c in word_counter.most_common(20)
                if c >= min_frequency
            ],
            "top_phrases": [
                {"phrase": p, "count": c}
                for p, c in bigram_counter.most_common(15)
                if c >= min_frequency
            ],
        }
        return themes
