"""
Hook Generator
==============
Generates viral hooks and content scripts for each niche using:
- Human psychology frameworks (loss aversion, curiosity gap, etc.)
- Real language from Reddit/Quora posts
- Proven direct-response copywriting formulas
- AI enhancement via Claude API (optional but recommended)

If ANTHROPIC_API_KEY is set, uses Claude for 10x better hooks.
Otherwise falls back to template-based generation.
"""

import random

import config

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class HookGenerator:

    def __init__(self):
        self.use_ai = bool(config.ANTHROPIC_API_KEY) and HAS_ANTHROPIC
        if self.use_ai:
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def generate_hooks(self, niche):
        """Generate viral hooks for a niche. Returns list of hook dicts."""
        if self.use_ai:
            return self._generate_ai_hooks(niche)
        return self._generate_template_hooks(niche)

    def generate_content_strategy(self, niche):
        """Generate a full content strategy for the niche."""
        if self.use_ai:
            return self._generate_ai_strategy(niche)
        return self._generate_template_strategy(niche)

    # ------------------------------------------------------------------
    # AI-powered generation (Claude API)
    # ------------------------------------------------------------------

    def _generate_ai_hooks(self, niche):
        """Use Claude to generate psychology-driven viral hooks."""
        top_post_titles = [
            p.get("post_title", "") for p in niche.top_posts[:10]
        ]
        themes = niche.themes.get("top_keywords", [])
        theme_words = [t["word"] for t in themes[:10]]

        prompt = f"""You are an elite direct-response copywriter and viral content strategist
who specializes in short-form video hooks for Instagram Reels. You understand human psychology
at a deep level — Cialdini's principles, Kahneman's cognitive biases, loss aversion,
the curiosity gap, identity-based persuasion, and pattern interrupts.

NICHE: {niche.name}
CATEGORY: {niche.category}
KEY THEMES: {', '.join(theme_words)}
PAIN SCORES: Desperation={niche.nlp_scores.get('desperation_score', 0):.0f}/100,
Emotional Intensity={niche.nlp_scores.get('emotional_intensity', 0):.0f}/100

REAL POSTS FROM THIS AUDIENCE (use their language):
{chr(10).join(f'- {t}' for t in top_post_titles if t)}

Generate exactly {config.HOOKS_PER_NICHE} viral hooks for an AI avatar Instagram page targeting
this niche. Each hook is the FIRST 3 SECONDS of a reel — it must stop the scroll instantly.

For each hook, provide:
1. The hook text (what the AI avatar says in the first 3 seconds)
2. The psychology principle it uses
3. A brief content outline for the full 30-60 second reel
4. A suggested caption with CTA driving to a digital product

RULES:
- Use the EXACT emotional language from the real posts above
- Every hook must create an open loop the viewer NEEDS to close
- Use pattern interrupts — start with something unexpected
- Leverage loss aversion > gain framing (what they'll LOSE, not gain)
- Make it feel like insider knowledge being leaked
- The avatar should feel like a mentor/authority figure, NOT a salesperson
- Hooks should be conversational, not corporate
- Each hook should use a DIFFERENT psychology principle

Format each hook as:
HOOK [number]:
Text: "..."
Psychology: [principle]
Reel outline: ...
Caption: ...

---"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            return self._parse_ai_hooks(raw_text)
        except Exception as e:
            print(f"    AI hook generation failed ({e}), using templates...")
            return self._generate_template_hooks(niche)

    def _generate_ai_strategy(self, niche):
        """Use Claude to generate a full content + monetization strategy."""
        top_post_titles = [
            p.get("post_title", "") for p in niche.top_posts[:8]
        ]
        themes = niche.themes.get("top_keywords", [])
        theme_words = [t["word"] for t in themes[:10]]
        quora_qs = niche.quora_questions[:5] if niche.quora_questions else []

        prompt = f"""You are a growth strategist who has built multiple 7-figure Instagram pages
from zero using AI avatars. You understand viral content, digital product funnels,
and human psychology at an expert level.

NICHE: {niche.name}
SUPER NICHE SCORE: {getattr(niche, 'super_niche_score', 'N/A')}/100
CATEGORY: {niche.category}
KEY THEMES: {', '.join(theme_words)}
AUDIENCE SIZE: {niche.subscriber_reach:,} across {niche.cross_subreddit_count} communities
QUORA QUESTIONS: {chr(10).join(f'- {q}' for q in quora_qs)}

TOP PAIN POINTS FROM REAL POSTS:
{chr(10).join(f'- {t}' for t in top_post_titles if t)}

Create a COMPLETE content and monetization strategy for an AI avatar Instagram page in this niche.

Include:

1. **AVATAR PERSONA**: Who is this character? Name, background, speaking style, visual aesthetic.
   Make them an aspirational authority figure the audience trusts instantly.

2. **CONTENT PILLARS** (5 recurring content themes with examples):
   Each pillar should map to a different stage of the audience journey.

3. **POSTING STRATEGY**: Frequency, best times, content mix ratios.

4. **DIGITAL PRODUCT LADDER** (3 products from free to premium):
   - Free lead magnet (grows the list)
   - Low-ticket ($7-27 range)
   - Mid-ticket ($47-97 range)
   For each: name, what it contains, why it converts, price point.

5. **FUNNEL FLOW**: How reels → profile → link in bio → product → upsell works.

6. **WEEK 1 LAUNCH PLAN**: Exact 7-day content calendar to get first 1000 followers.

7. **MONTH 1 REVENUE PROJECTION**: Realistic revenue estimate with assumptions.

Be specific, actionable, and psychologically sophisticated. No fluff."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"    AI strategy generation failed ({e}), using template...")
            return self._generate_template_strategy(niche)

    def _parse_ai_hooks(self, raw_text):
        """Parse Claude's hook output into structured dicts."""
        hooks = []
        current_hook = {}
        lines = raw_text.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("HOOK") and ":" in line:
                if current_hook:
                    hooks.append(current_hook)
                current_hook = {"number": len(hooks) + 1}
            elif line.startswith("Text:"):
                current_hook["text"] = line[5:].strip().strip('"')
            elif line.startswith("Psychology:"):
                current_hook["psychology"] = line[11:].strip()
            elif line.startswith("Reel outline:") or line.startswith("Reel Outline:"):
                current_hook["reel_outline"] = line.split(":", 1)[1].strip()
            elif line.startswith("Caption:"):
                current_hook["caption"] = line[8:].strip()
            elif current_hook and line and not line.startswith("---"):
                # Append to the last field
                for field in ["caption", "reel_outline", "psychology", "text"]:
                    if field in current_hook:
                        current_hook[field] += " " + line
                        break

        if current_hook:
            hooks.append(current_hook)

        return hooks

    # ------------------------------------------------------------------
    # Template-based fallback (no API needed)
    # ------------------------------------------------------------------

    def _generate_template_hooks(self, niche):
        """Generate hooks using proven templates + niche data."""
        templates = self._get_hook_templates()

        # Use the niche NAME as the topic (not random keywords)
        # Clean it up: "Tech & Skills: Coding" -> "coding"
        niche_name = niche.name
        if ":" in niche_name:
            topic = niche_name.split(":")[-1].strip().lower()
        else:
            topic = niche_name.lower()

        # Get meaningful theme phrases for variety (filter junk words)
        junk_words = {
            "years", "days", "day", "time", "people", "life", "thing",
            "things", "lot", "way", "guy", "girl", "feel", "post",
            "week", "month", "year", "ago", "old", "new", "good",
            "bad", "best", "worst", "big", "small", "long", "short",
            "really", "actually", "literally", "basically", "getting",
            "porn", "porno", "masturbation", "sex", "nsfw", "nude",
            "kill", "suicide", "dead", "died", "death",
            "started", "start", "help", "advice", "question", "update",
            "rant", "story", "experience", "first", "last", "back",
        }
        themes = niche.themes.get("top_keywords", [])
        good_keywords = [
            t["word"] for t in themes
            if t["word"] not in junk_words and len(t["word"]) > 3
        ]

        # Build topic variations using niche name + good keywords
        topic_variations = [topic]
        for kw in good_keywords[:4]:
            topic_variations.append(kw)

        # Get real post titles for inspiration hooks
        real_titles = [
            p.get("post_title", "")
            for p in niche.top_posts[:10]
            if p.get("post_title") and len(p.get("post_title", "")) > 20
        ]

        hooks = []
        used_templates = random.sample(
            templates, min(config.HOOKS_PER_NICHE, len(templates))
        )

        for i, template in enumerate(used_templates):
            # Rotate through topic variations but always use clean names
            current_topic = topic_variations[i % len(topic_variations)]
            title_ref = real_titles[i % len(real_titles)] if real_titles else ""

            hook = {
                "number": i + 1,
                "text": template["template"].format(
                    topic=current_topic,
                    niche=topic,
                    title=title_ref[:80],
                ),
                "psychology": template["psychology"],
                "reel_outline": template["outline"].format(
                    topic=current_topic, niche=topic
                ),
                "caption": template["caption"].format(
                    topic=current_topic, niche=topic
                ),
            }
            hooks.append(hook)

        # Add 3 "real post inspired" hooks based on actual high-performing titles
        for j, title in enumerate(real_titles[:3]):
            hooks.append({
                "number": len(hooks) + 1,
                "text": f"I saw someone say '{title[:70]}' — and they're wrong. Here's why.",
                "psychology": "Contrarian + curiosity gap + pattern interrupt",
                "reel_outline": f"Reference the real post, explain the common misconception, give the real answer about {topic}.",
                "caption": f"The internet has {topic} all wrong. Let me fix that. | Follow for more",
            })

        return hooks[:config.HOOKS_PER_NICHE]

    def _generate_template_strategy(self, niche):
        """Generate a niche-specific strategy without AI."""
        topic = niche.name.split(":")[-1].strip() if ":" in niche.name else niche.name

        # Pull real pain points from top posts
        pain_points = []
        for p in niche.top_posts[:5]:
            title = p.get("post_title", "")
            if title:
                pain_points.append(f"  - \"{title[:80]}\"")
        pain_section = "\n".join(pain_points) if pain_points else "  - (Run with more subreddits for richer data)"

        # Niche-specific product ideas
        product_map = {
            "money_and_career": {
                "free": "The 5 Money Mistakes Keeping You Broke (PDF checklist)",
                "low": "'The Wealth Blueprint' — step-by-step guide to building your first $10K ($17)",
                "mid": "'Money Mastery System' — full video course + templates + community ($67)",
            },
            "relationships_and_dating": {
                "free": "10 Texts That Make Them Chase You (PDF)",
                "low": "'The Connection Code' — guide to building deep relationships ($19)",
                "mid": "'Relationship Reset' — 30-day transformation program ($57)",
            },
            "health_and_fitness": {
                "free": "7-Day Transformation Starter Kit (PDF + meal plan)",
                "low": "'The Body Blueprint' — complete nutrition & workout guide ($17)",
                "mid": "'Total Health System' — 90-day program with coaching ($67)",
            },
            "self_improvement": {
                "free": "The Morning Routine That Changed My Life (PDF)",
                "low": "'The Discipline Playbook' — 30-day habit system ($19)",
                "mid": "'Life Mastery Program' — full course with accountability ($67)",
            },
            "tech_and_skills": {
                "free": "The Beginner's Cheat Sheet (PDF quick-start guide)",
                "low": "'From Zero to Pro' — complete learning roadmap ($17)",
                "mid": "'Skill Accelerator' — hands-on course with projects ($67)",
            },
            "parenting_and_family": {
                "free": "5 Parenting Hacks That Actually Work (PDF)",
                "low": "'The Calm Parent Guide' — stress-free parenting system ($17)",
                "mid": "'Family Transformation Program' — full course ($57)",
            },
            "housing_and_living": {
                "free": "First-Time Buyer Checklist (PDF)",
                "low": "'The Housing Playbook' — insider tips + negotiation scripts ($19)",
                "mid": "'Real Estate Starter System' — full course ($67)",
            },
            "legal_and_life_crises": {
                "free": "Know Your Rights Checklist (PDF)",
                "low": "'Crisis Navigation Guide' — step-by-step action plan ($17)",
                "mid": "'Life Reset System' — recovery roadmap + templates ($57)",
            },
        }
        products = product_map.get(niche.category, product_map["self_improvement"])

        # Quora questions for content ideas
        quora_section = ""
        if niche.quora_questions:
            quora_items = "\n".join(f"  - {q}" for q in niche.quora_questions[:5])
            quora_section = f"""
### Content Ideas from Quora (Real Questions People Ask)
{quora_items}
Each of these is a reel. Answer the question in 30-60 seconds as your avatar."""

        return f"""## Content Strategy for {topic}

### Real Pain Points Found (from Reddit)
{pain_section}

### Avatar Persona
A {self._get_avatar_archetype(niche.category)} who has mastered {topic.lower()}.
Speaks with calm authority. Uses "I used to struggle with this too" framing.
Dresses well, high-end setting. Feels like a mentor, never a salesman.

### Content Pillars
1. **Pain point callouts** — directly reference the Reddit posts above. "If you're lying awake at 2am worrying about {topic.lower()}..."
2. **Myth-busting** — "Everyone says [common advice], but here's what actually works..."
3. **Quick wins** — "Do this ONE thing today and you'll see results by Friday..."
4. **Story hooks** — "3 years ago I was exactly where you are. Then I discovered..."
5. **Controversial takes** — "This is going to make people mad, but {topic.lower()} advice is broken..."

### Digital Product Ladder
1. **FREE lead magnet:** {products['free']}
2. **Low-ticket:** {products['low']}
3. **Mid-ticket:** {products['mid']}

### Funnel Flow
Reel (hook → value → CTA) → Profile ("Link in bio for free guide") →
Free PDF (captures email) → Email sequence (3 emails over 5 days) →
Low-ticket offer → Upsell to mid-ticket on thank you page

### Posting Strategy
- 2 reels per day for first 30 days (volume is everything early on)
- Best times: 7am, 12pm, 6pm (test and adjust)
- Mix: 50% pain-point/myth-bust, 30% story hooks, 20% controversial

### Week 1 Launch Plan
- **Day 1-2:** 3 pain point reels each day (high volume, test what resonates)
- **Day 3-4:** 2 myth-busting reels + 1 story hook per day
- **Day 5:** Controversial take reel (designed to get comments/shares)
- **Day 6-7:** Double down on whatever got the most views in days 1-5
- **Goal:** 1,000 followers by end of week 1 if one reel pops
{quora_section}

### Month 1 Revenue Estimate
- Followers: 1,000-5,000 (conservative)
- Email list: 200-500 from free lead magnet
- Low-ticket sales: 20-50 at $17 = $340-$850
- Mid-ticket sales: 3-8 at $67 = $200-$536
- **Estimated Month 1: $540-$1,386**
- *Scales dramatically with follower growth — accounts with 50K+ followers report $5K-$20K/month*
"""

    def _get_avatar_archetype(self, category):
        """Return avatar archetype based on category."""
        archetypes = {
            "money_and_career": "wealthy, self-made business figure in a luxury office",
            "relationships_and_dating": "wise, emotionally intelligent relationship coach",
            "health_and_fitness": "fit, disciplined wellness expert in a clean modern space",
            "self_improvement": "calm, centered mentor figure with quiet confidence",
            "tech_and_skills": "sharp, successful tech professional in a sleek workspace",
            "parenting_and_family": "warm, experienced parent who radiates wisdom",
            "housing_and_living": "successful real estate investor in an upscale home",
            "legal_and_life_crises": "authoritative, empathetic advisor in a professional office",
        }
        return archetypes.get(category, "authoritative mentor figure")

    def _get_hook_templates(self):
        """Proven hook templates based on psychology."""
        return [
            {
                "template": "Nobody talks about the dark side of {topic}. Let me tell you what I learned the hard way.",
                "psychology": "Curiosity gap + pattern interrupt",
                "outline": "Reveal a hidden truth about {topic} that contradicts common advice. End with actionable takeaway.",
                "caption": "The truth about {topic} that nobody wants to hear. Save this. | Follow for more {niche} insights",
            },
            {
                "template": "If you're struggling with {topic}, stop doing what everyone else is doing. Here's why.",
                "psychology": "Contrarian positioning + identity",
                "outline": "Challenge the mainstream approach to {topic}. Present a counterintuitive alternative. Show social proof.",
                "caption": "Stop following the crowd on {topic}. There's a better way. | Link in bio for the full guide",
            },
            {
                "template": "I wish someone told me this about {topic} 10 years ago. It would have saved me everything.",
                "psychology": "Loss aversion + authority",
                "outline": "Share a pivotal lesson about {niche}. Frame as a costly mistake. Deliver the insight. CTA to product.",
                "caption": "This one lesson changed everything for me. Don't make the same mistake. | Free guide in bio",
            },
            {
                "template": "The real reason you can't fix your {topic} problem has nothing to do with {topic}.",
                "psychology": "Curiosity gap + reframing",
                "outline": "Reframe the {topic} problem as a deeper issue. Provide the real root cause. Give one actionable step.",
                "caption": "It's not about {topic}. It never was. | Follow for daily {niche} wisdom",
            },
            {
                "template": "Rich people don't talk about this. But it's the #1 thing that changed my {topic}.",
                "psychology": "Scarcity + social proof + curiosity",
                "outline": "Reveal a strategy used by successful people. Make it feel exclusive. Provide a simplified version anyone can use.",
                "caption": "The elite don't want you to know this about {topic}. But you deserve to. | Save this",
            },
            {
                "template": "You're not lazy. You're not broken. You just don't understand how {topic} actually works.",
                "psychology": "Identity validation + reframing",
                "outline": "Validate the audience's struggle. Explain the real mechanism behind {topic}. Give them a new mental model.",
                "caption": "It was never your fault. Here's what's really going on with {topic}. | Share with someone who needs this",
            },
            {
                "template": "If you earn under $100K and you're ignoring {topic}, this is your wake-up call.",
                "psychology": "Loss aversion + urgency + identity",
                "outline": "Paint the cost of inaction on {topic}. Show what they're leaving on the table. Give the first step.",
                "caption": "This is your sign to take {topic} seriously. Before it's too late. | Free playbook in bio",
            },
            {
                "template": "I spent 5 years making every mistake with {topic} so you don't have to. Here's the cheat code.",
                "psychology": "Authority + reciprocity + curiosity",
                "outline": "List 3 major mistakes you made with {niche}. For each, give the fix. End with the 'cheat code' framework.",
                "caption": "5 years of mistakes condensed into 60 seconds. You're welcome. | Follow for more",
            },
            {
                "template": "The {topic} advice that's all over the internet is actually making your problem worse.",
                "psychology": "Pattern interrupt + enemy framing",
                "outline": "Call out popular bad advice about {topic}. Explain why it backfires. Present the correct approach.",
                "caption": "Stop Googling {topic} advice. Most of it is wrong. Here's what actually works. | Save this",
            },
            {
                "template": "In 2026, if you understand {topic}, you'll be in the top 1%. Most people still don't get it.",
                "psychology": "Scarcity + social comparison + timeliness",
                "outline": "Frame {topic} as an emerging opportunity. Show why most people miss it. Give the viewer the first step to being early.",
                "caption": "The window is closing on {topic}. Are you going to act or watch? | Link in bio",
            },
            {
                "template": "Your parents never taught you this about {topic}. And it's costing you thousands.",
                "psychology": "Loss aversion + blame displacement",
                "outline": "Reveal a generational blind spot about {niche}. Quantify the cost. Show the fix is simpler than they think.",
                "caption": "What they never taught us about {topic} is holding us back. Time to fix that. | Follow for daily tips",
            },
            {
                "template": "I need to get this off my chest about {topic}. This might make some people angry.",
                "psychology": "Pattern interrupt + vulnerability + controversy",
                "outline": "Start vulnerable, then pivot to a bold truth about {topic}. Back it up with evidence. CTA to deeper content.",
                "caption": "Uncomfortable truths about {topic} that need to be said. | Like if you agree",
            },
            {
                "template": "Stop telling yourself you'll figure out {topic} later. Later is how people end up broke.",
                "psychology": "Urgency + loss aversion + tough love",
                "outline": "Paint the consequences of procrastination on {niche}. Use a specific example. Give one action they can take TODAY.",
                "caption": "'Later' is the most expensive word in {topic}. Start now. | Free starter guide in bio",
            },
            {
                "template": "The 3-minute {topic} trick that the internet hasn't ruined yet.",
                "psychology": "Curiosity + scarcity + simplicity",
                "outline": "Deliver a genuinely useful quick tip for {topic}. Frame it as time-sensitive before it gets oversaturated.",
                "caption": "This {topic} trick still works in 2026. Won't last forever though. | Save before it goes viral",
            },
            {
                "template": "If {topic} makes you anxious, you're actually closer to a breakthrough than you think.",
                "psychology": "Reframing + hope + identity validation",
                "outline": "Normalize the anxiety around {niche}. Reframe it as a sign of growth. Give the next step past the anxiety.",
                "caption": "Your anxiety about {topic} is a signal, not a setback. | Follow for the mindset shift",
            },
        ]
