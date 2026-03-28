"""
Super Niche Scorer
==================
Computes a composite score (0-100) for each niche candidate based on:

  1. Pain Point Intensity   (20%) — How badly do people need this solved?
  2. Demand Volume          (12%) — Raw audience size and engagement
  3. Willingness to Pay     (22%) — Signals that people spend money here
  4. Viral Potential        (15%) — Can this blow up on short-form video?
  5. Content Potential      (10%) — Depth of stories, hooks, and angles
  6. Monetization Readiness (10%) — Existing product ecosystem
  7. Low Competition         (6%) — Fewer AI avatar pages = better
  8. Scalability             (5%) — Evergreen + adjacent niches

Human psychology multipliers are applied on top.
"""

import config


class SuperNicheScorer:

    def __init__(self):
        self.weights = config.SCORING_WEIGHTS

    def score_all(self, niche_candidates):
        """Score all candidates and return them sorted best-first."""
        scored = []
        for niche in niche_candidates:
            scores = self._compute_scores(niche)
            niche.scores = scores
            niche.super_niche_score = scores["total"]
            scored.append(niche)

        scored.sort(key=lambda n: n.super_niche_score, reverse=True)
        return scored

    def _compute_scores(self, niche):
        """Compute all sub-scores and the weighted total."""
        nlp = niche.nlp_scores

        pain = self._score_pain_point(niche, nlp)
        demand = self._score_demand(niche)
        pay = self._score_willingness_to_pay(niche, nlp)
        viral = self._score_viral_potential(niche, nlp)
        content = self._score_content_potential(niche)
        monetization = self._score_monetization_readiness(niche, nlp)
        competition = self._score_low_competition(niche)
        scalability = self._score_scalability(niche)

        # Weighted total
        raw_total = (
            pain * self.weights["pain_point_intensity"]
            + demand * self.weights["demand_volume"]
            + pay * self.weights["willingness_to_pay"]
            + viral * self.weights["viral_potential"]
            + content * self.weights["content_potential"]
            + monetization * self.weights["monetization_readiness"]
            + competition * self.weights["low_competition"]
            + scalability * self.weights["scalability"]
        )

        # Psychology multiplier: niches that hit multiple emotional triggers
        # score higher because they convert better
        psych_multiplier = self._psychology_multiplier(niche, nlp)
        total = min(raw_total * psych_multiplier, 100)

        return {
            "pain_point_intensity": round(pain, 1),
            "demand_volume": round(demand, 1),
            "willingness_to_pay": round(pay, 1),
            "viral_potential": round(viral, 1),
            "content_potential": round(content, 1),
            "monetization_readiness": round(monetization, 1),
            "low_competition": round(competition, 1),
            "scalability": round(scalability, 1),
            "psychology_multiplier": round(psych_multiplier, 3),
            "total": round(total, 1),
        }

    # ------------------------------------------------------------------
    # Individual scoring functions (each returns 0-100)
    # ------------------------------------------------------------------

    def _score_pain_point(self, niche, nlp):
        """How badly do people need this solved?"""
        desperation = nlp.get("desperation_score", 0)
        emotional = nlp.get("emotional_intensity", 0)

        # High comment counts = people need to talk about it
        comment_signal = min(niche.avg_post_score / 10, 100) if niche.avg_post_score else 0

        # Cross-subreddit presence = widespread pain
        cross_sub_bonus = min(niche.cross_subreddit_count * 8, 30)

        raw = desperation * 0.40 + emotional * 0.25 + comment_signal * 0.20 + cross_sub_bonus
        return min(raw, 100)

    def _score_demand(self, niche):
        """Raw audience size and engagement volume."""
        # Subscriber reach (log scale — 1M subs = 100)
        import math
        sub_score = min(math.log10(max(niche.subscriber_reach, 1)) / 7 * 100, 100)

        # Engagement volume
        eng_score = min(niche.total_engagement / 500, 100)

        # Post count
        post_score = min(niche.total_posts / 5, 100)

        # Quora presence adds demand validation
        quora_bonus = min(niche.quora_question_count * 2, 20)

        raw = sub_score * 0.30 + eng_score * 0.35 + post_score * 0.20 + quora_bonus
        return min(raw, 100)

    def _score_willingness_to_pay(self, niche, nlp):
        """Signals that people actually spend money in this space."""
        payment_intent = nlp.get("payment_intent_score", 0)

        # Categories with proven monetization get a base boost
        high_spend_categories = {
            "money_and_career": 25,
            "health_and_fitness": 20,
            "relationships_and_dating": 18,
            "self_improvement": 15,
            "tech_and_skills": 15,
            "parenting_and_family": 12,
            "housing_and_living": 20,
            "legal_and_life_crises": 22,
        }
        category_boost = high_spend_categories.get(niche.category, 10)

        # Desperation correlates with willingness to pay
        desperation_boost = nlp.get("desperation_score", 0) * 0.15

        raw = payment_intent * 0.50 + category_boost + desperation_boost
        return min(raw, 100)

    def _score_viral_potential(self, niche, nlp):
        """Can this blow up on Instagram Reels / TikTok?"""
        viral_score = nlp.get("viral_potential_score", 0)
        emotional = nlp.get("emotional_intensity", 0)

        # Controversial / emotionally charged content goes viral
        controversy_bonus = 0
        themes = niche.themes.get("top_keywords", [])
        viral_keywords = {
            "money", "rich", "broke", "cheat", "lie", "secret",
            "toxic", "narcissist", "divorce", "fired", "scam",
            "anxiety", "depression", "lonely", "addicted",
            "debt", "homeless", "pregnant", "weight", "ugly",
        }
        for theme in themes:
            if theme["word"] in viral_keywords:
                controversy_bonus += 5

        # Relatability: high engagement = people see themselves in this
        relatability = min(niche.avg_post_score / 8, 30) if niche.avg_post_score else 0

        raw = viral_score * 0.35 + emotional * 0.25 + controversy_bonus + relatability
        return min(raw, 100)

    def _score_content_potential(self, niche):
        """Depth of stories, hooks, and angles available."""
        # More diverse themes = more content angles
        keyword_count = len(niche.themes.get("top_keywords", []))
        phrase_count = len(niche.themes.get("top_phrases", []))
        theme_diversity = min((keyword_count + phrase_count) * 3, 40)

        # More top posts = more story material
        story_depth = min(len(niche.top_posts) * 4, 30)

        # Quora questions = more content angles
        quora_angles = min(niche.quora_question_count, 30)

        raw = theme_diversity + story_depth + quora_angles
        return min(raw, 100)

    def _score_monetization_readiness(self, niche, nlp):
        """Is there an existing product ecosystem?"""
        payment_intent = nlp.get("payment_intent_score", 0)

        # Categories where digital products already sell well
        product_ecosystem = {
            "money_and_career": 30,
            "health_and_fitness": 28,
            "self_improvement": 25,
            "relationships_and_dating": 22,
            "tech_and_skills": 25,
            "parenting_and_family": 15,
            "housing_and_living": 18,
            "legal_and_life_crises": 20,
        }
        ecosystem_score = product_ecosystem.get(niche.category, 10)

        # Digital product fit — some niches lend themselves to ebooks, courses, templates
        digital_fit = {
            "money_and_career": 30,
            "tech_and_skills": 30,
            "self_improvement": 25,
            "health_and_fitness": 25,
            "relationships_and_dating": 20,
            "parenting_and_family": 18,
            "housing_and_living": 15,
            "legal_and_life_crises": 15,
        }
        fit_score = digital_fit.get(niche.category, 10)

        raw = payment_intent * 0.30 + ecosystem_score + fit_score
        return min(raw, 100)

    def _score_low_competition(self, niche):
        """Fewer AI avatar pages = better opportunity."""
        # Without Instagram API, we estimate based on niche specificity
        # More specific niches = less competition
        specificity = 0

        # Sub-niches (containing ":") are more specific
        if ":" in niche.name:
            specificity += 30

        # Niche categories with fewer existing AI pages
        low_saturation = {
            "legal_and_life_crises": 35,
            "parenting_and_family": 30,
            "housing_and_living": 28,
            "tech_and_skills": 20,
            "health_and_fitness": 15,
            "self_improvement": 12,
            "relationships_and_dating": 10,
            "money_and_career": 8,  # Most saturated
        }
        saturation_score = low_saturation.get(niche.category, 20)

        # Smaller subscriber reach can mean less mainstream = less competition
        import math
        if niche.subscriber_reach > 0:
            inverse_reach = max(100 - math.log10(niche.subscriber_reach) / 7 * 60, 0)
        else:
            inverse_reach = 50

        raw = specificity + saturation_score + inverse_reach * 0.3
        return min(raw, 100)

    def _score_scalability(self, niche):
        """Evergreen potential + adjacent niche expansion."""
        # Evergreen topics score higher (not tied to current events)
        evergreen_scores = {
            "money_and_career": 85,
            "relationships_and_dating": 90,
            "health_and_fitness": 88,
            "self_improvement": 92,
            "parenting_and_family": 85,
            "tech_and_skills": 70,  # Tech changes fast
            "housing_and_living": 75,
            "legal_and_life_crises": 80,
        }
        evergreen = evergreen_scores.get(niche.category, 70)

        # Content velocity = sustainable content pipeline
        velocity_score = min(niche.content_velocity * 10, 30)

        # Cross-subreddit = can expand into adjacent niches
        expansion = min(niche.cross_subreddit_count * 5, 20)

        raw = evergreen * 0.50 + velocity_score + expansion
        return min(raw, 100)

    # ------------------------------------------------------------------
    # Psychology multiplier
    # ------------------------------------------------------------------

    def _psychology_multiplier(self, niche, nlp):
        """
        Apply human psychology principles to boost niches that will
        convert better. Based on Cialdini, Kahneman, and direct response
        marketing psychology.

        Returns a multiplier between 1.0 and 1.25.
        """
        triggers = 0

        # 1. Loss aversion — people fear losing more than gaining
        #    High desperation = fear of loss
        if nlp.get("desperation_score", 0) > 40:
            triggers += 1

        # 2. Identity threat — the problem threatens who they are
        #    High emotional intensity = identity-level pain
        if nlp.get("emotional_intensity", 0) > 35:
            triggers += 1

        # 3. Social comparison — others have solved this, why can't I?
        #    High cross-subreddit = everyone's talking about it
        if niche.cross_subreddit_count >= 3:
            triggers += 1

        # 4. Urgency / time pressure — this needs fixing NOW
        #    High content velocity = trending, timely
        if niche.content_velocity > 3:
            triggers += 1

        # 5. Information gap — people WANT to know the answer
        #    Question density in posts = curiosity gap
        viral = nlp.get("viral_potential_score", 0)
        if viral > 30:
            triggers += 1

        # 6. Proven spending behavior
        if nlp.get("payment_intent_score", 0) > 25:
            triggers += 1

        # Each trigger adds 4% to the multiplier, max 25%
        multiplier = 1.0 + (triggers * 0.04)
        return min(multiplier, 1.25)
