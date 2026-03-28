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
        themes = niche.themes.get("top_keywords", [])
        theme_words = [t["word"] for t in themes[:5]] if themes else ["this"]

        top_titles = [
            p.get("post_title", "")
            for p in niche.top_posts[:5]
            if p.get("post_title")
        ]

        hooks = []
        used_templates = random.sample(
            templates, min(config.HOOKS_PER_NICHE, len(templates))
        )

        for i, template in enumerate(used_templates):
            topic = random.choice(theme_words) if theme_words else "this"
            title_ref = top_titles[i % len(top_titles)] if top_titles else ""

            hook = {
                "number": i + 1,
                "text": template["template"].format(
                    topic=topic,
                    niche=niche.name.split(":")[0].strip(),
                    title=title_ref[:60],
                ),
                "psychology": template["psychology"],
                "reel_outline": template["outline"].format(
                    topic=topic, niche=niche.name
                ),
                "caption": template["caption"].format(
                    topic=topic, niche=niche.name
                ),
            }
            hooks.append(hook)

        return hooks

    def _generate_template_strategy(self, niche):
        """Generate a basic strategy without AI."""
        return f"""## Content Strategy for {niche.name}

### Avatar Persona
An authoritative, relatable figure in the {niche.name} space.
Speaks directly, uses conversational language, and shares
insider knowledge that feels exclusive.

### Content Pillars
1. Pain point callouts — "If you're struggling with {niche.name.lower()}..."
2. Myth-busting — "Everyone says X, but the truth is..."
3. Quick wins — "Do this ONE thing today..."
4. Story-based — "I used to [pain point], until I discovered..."
5. Controversial takes — "Unpopular opinion about {niche.name.lower()}..."

### Digital Product Ideas
1. Free lead magnet: Checklist or cheat sheet
2. Low-ticket ($17): Comprehensive guide / ebook
3. Mid-ticket ($67): Video course or coaching template

### Posting Strategy
- 2 reels per day for first 30 days
- Post at 7am, 12pm, or 7pm (test all three)
- 60% educational, 25% story-based, 15% controversial

### Week 1 Focus
Days 1-3: Post 2 pain-point callout reels per day
Days 4-5: Post myth-busting content
Days 6-7: Post story-based transformation content
"""

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
