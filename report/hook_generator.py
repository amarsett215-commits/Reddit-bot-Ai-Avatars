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

    def generate_hooks(self, niche, strategy_text=None):
        """Generate viral hooks for a niche. Returns list of hook dicts.
        If strategy_text is provided, uses the avatar persona from it."""
        if self.use_ai:
            return self._generate_ai_hooks(niche, strategy_text=strategy_text)
        return self._generate_template_hooks(niche)

    def generate_scripts(self, niche, strategy_text=None, hooks=None):
        """Generate full 60-second reel scripts. Returns list of script dicts."""
        if self.use_ai:
            return self._generate_ai_scripts(niche, strategy_text, hooks)
        return self._generate_template_scripts(niche, hooks)

    def generate_content_strategy(self, niche):
        """Generate a full content strategy for the niche."""
        if self.use_ai:
            return self._generate_ai_strategy(niche)
        return self._generate_template_strategy(niche)

    # ------------------------------------------------------------------
    # AI-powered generation (Claude API)
    # ------------------------------------------------------------------

    def _generate_ai_hooks(self, niche, strategy_text=None):
        """Use Claude to generate psychology-driven viral hooks."""
        top_post_titles = [
            p.get("post_title", "") for p in niche.top_posts[:10]
        ]
        themes = niche.themes.get("top_keywords", [])
        theme_words = [t["word"] for t in themes[:10]]

        # Extract avatar persona from strategy if available
        persona_context = ""
        if strategy_text:
            # Pull the avatar section from the strategy
            lines = strategy_text.split("\n")
            in_persona = False
            persona_lines = []
            for line in lines:
                if "AVATAR PERSONA" in line.upper() or "AVATAR" in line.upper() and "PERSONA" in line.upper():
                    in_persona = True
                    continue
                if in_persona:
                    if line.startswith("## ") or line.startswith("# ") or "CONTENT PILLAR" in line.upper():
                        break
                    persona_lines.append(line)
            if persona_lines:
                persona_context = f"""
AVATAR PERSONA (speak as this character):
{''.join(persona_lines[:20]).strip()}
"""

        # Default persona context if none extracted
        if not persona_context:
            archetype = self._get_avatar_archetype(niche.category)
            persona_context = f"""
AVATAR PERSONA (speak as this character):
You are an AI avatar playing the role of a {archetype}.
You are the EXPERT/COACH/GUIDE — NOT the person suffering.
You speak from experience helping hundreds of people, with calm authority.
"""

        prompt = f"""You are an elite direct-response copywriter and viral content strategist
who specializes in short-form video hooks for Instagram Reels. You understand human psychology
at a deep level — Cialdini's principles, Kahneman's cognitive biases, loss aversion,
the curiosity gap, identity-based persuasion, and pattern interrupts.

NICHE: {niche.name}
CATEGORY: {niche.category}
KEY THEMES: {', '.join(theme_words)}
PAIN SCORES: Desperation={niche.nlp_scores.get('desperation_score', 0):.0f}/100,
Emotional Intensity={niche.nlp_scores.get('emotional_intensity', 0):.0f}/100
{persona_context}
REAL POSTS FROM THIS AUDIENCE (use their language as INSPIRATION for the pain points):
{chr(10).join(f'- {t}' for t in top_post_titles if t)}

Generate exactly {config.HOOKS_PER_NICHE} viral hooks for an AI avatar Instagram page targeting
this niche. Each hook is the FIRST 3 SECONDS of a reel — it must stop the scroll instantly.

CRITICAL POV RULES:
- The avatar is an EXPERT/COACH/THERAPIST speaking TO the audience, NOT someone going through the problem
- NEVER write hooks in first-person sufferer voice ("I tracked my brain fog", "She used my identity")
- ALWAYS write hooks from the EXPERT POV: "Your brain fog isn't random — after coaching 200+ people..."
- The avatar HELPS people with these problems. They reference patterns they've SEEN in clients, not personal suffering
- Think: therapist on camera giving advice, NOT a Reddit poster sharing their story
- Acceptable first-person: "I've helped 500 people through this" or "In my experience coaching..."
- The avatar may reference seeing patterns: "Every client I work with makes this same mistake..."
- Use the real Reddit posts as PROOF OF DEMAND — reference the pain points but from an expert lens
  (e.g., real post: "woke up to a corpse" → hook: "If you've ever woken up and barely recognized yourself, here's what your body is telling you...")

For each hook, provide:
1. The hook text (what the AI avatar says in the first 3 seconds)
2. The psychology principle it uses
3. A brief content outline for the full 30-60 second reel
4. A suggested caption with CTA driving to a digital product (keep captions authentic, minimal emojis — max 1-2)

RULES:
- Understand the emotional language from the real posts but TRANSLATE it into expert advice
- Every hook must create an open loop the viewer NEEDS to close
- Use pattern interrupts — start with something unexpected
- Leverage loss aversion > gain framing (what they'll LOSE, not gain)
- Make it feel like insider knowledge being leaked by an authority
- The avatar IS the mentor/authority figure — they speak WITH authority, not as a peer in pain
- Hooks should be conversational, not corporate
- Each hook should use a DIFFERENT psychology principle
- Captions should feel real and human, not like a 2019 Instagram marketer (no emoji spam, no ALL CAPS hype)

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

    def _generate_ai_scripts(self, niche, strategy_text=None, hooks=None):
        """Use Claude to generate full 60-second reel scripts."""
        # Extract avatar persona from strategy
        persona_context = ""
        if strategy_text:
            lines = strategy_text.split("\n")
            in_persona = False
            persona_lines = []
            for line in lines:
                upper = line.upper()
                if "AVATAR PERSONA" in upper or ("AVATAR" in upper and "PERSONA" in upper):
                    in_persona = True
                    continue
                if in_persona:
                    if line.startswith("## ") or line.startswith("# ") or "CONTENT PILLAR" in upper:
                        break
                    persona_lines.append(line)
            if persona_lines:
                persona_context = "\n".join(persona_lines[:20]).strip()

        if not persona_context:
            archetype = self._get_avatar_archetype(niche.category)
            persona_context = f"A {archetype} who has helped hundreds of people in this space."

        # Pick the best hooks to expand into scripts
        hook_refs = ""
        if hooks:
            best_hooks = hooks[:config.SCRIPTS_PER_NICHE]
            for h in best_hooks:
                hook_refs += f"- \"{h.get('text', '')}\"\n"

        top_post_titles = [
            p.get("post_title", "") for p in niche.top_posts[:10]
        ]
        themes = niche.themes.get("top_keywords", [])
        theme_words = [t["word"] for t in themes[:10]]

        prompt = f"""You are the world's best short-form video scriptwriter. You write scripts
for AI avatar Instagram Reels that get 95%+ watch-through rates. You understand pacing,
tension, open loops, and spoken-word rhythm at a master level.

You are writing scripts for an AI avatar — a digital character who appears on camera
delivering these scripts. The avatar is an EXPERT/COACH/AUTHORITY in their field.

NICHE: {niche.name}
CATEGORY: {niche.category}
KEY THEMES: {', '.join(theme_words)}

AVATAR PERSONA:
{persona_context}

REAL PAIN POINTS FROM THE AUDIENCE:
{chr(10).join(f'- {t}' for t in top_post_titles if t)}

{"HOOKS TO EXPAND INTO FULL SCRIPTS:" + chr(10) + hook_refs if hook_refs else ""}

Generate exactly {config.SCRIPTS_PER_NICHE} complete 60-second reel scripts. Each script must
follow this EXACT structure:

=== SCRIPT STRUCTURE ===

**HOOK (0-3 seconds):** The scroll-stopper. One sentence that creates an open loop so powerful
they CANNOT keep scrolling. This is life or death — if this line doesn't hit, nothing else matters.

**TENSION (3-15 seconds):** Deepen the problem. Make them FEEL it in their gut. Use specific
details, paint a picture they recognize from their own life. This is where you agitate the wound.
They should be thinking "this person is reading my mind."

**VALUE (15-45 seconds):** This is the meat. Deliver a genuine insight, framework, or revelation
that makes them think "holy shit, that makes so much sense." This should be something they've
never heard framed this way before. NOT generic advice. NOT "just do X." It should feel like
the expert just cracked open their skull and showed them how the machine works.

**PAYOFF (45-55 seconds):** The "aha moment." Tie everything together with one clean,
quotable line they'll want to screenshot or repeat to a friend. This is the moment
the reel becomes shareable.

**CTA (55-60 seconds):** Simple. Not salesy. Just: "Comment [KEYWORD] and I'll send you
the full [specific resource]." The keyword should be a single word that relates to the
script topic (e.g., "BOUNDARY", "RESET", "CLARITY"). Never say "link in bio" — always
drive comments because that's what the algorithm rewards.

=== WRITING RULES ===

1. SPOKEN WORD ONLY — write how people TALK, not how they write. Short sentences. Fragments.
   Pauses indicated by "..." or line breaks. No one speaks in perfect paragraphs.

2. EXPERT POV ALWAYS — the avatar is the coach/therapist/expert speaking TO the viewer.
   Never first-person sufferer. Use: "I see this with every client...", "After working with
   hundreds of people...", "Here's what nobody in your life will tell you..."

3. SPECIFICITY OVER GENERALITY — use exact numbers, timeframes, and details.
   Bad: "A lot of people struggle with this."
   Good: "I've worked with 347 people on this exact problem. 90% make the same mistake."

4. EVERY LINE MUST EARN THE NEXT LINE — if any single line doesn't make the viewer
   NEED to hear the next one, the script fails. There should be zero filler. Zero fluff.
   Every sentence either deepens tension, delivers value, or creates a new open loop.

5. PATTERN INTERRUPTS — break expectations. Start with something unexpected. Contradict
   common wisdom. Use "The real reason..." and "What nobody tells you..." framing.

6. NO SALESY LANGUAGE — never say "my course", "buy my", "check out my product."
   The CTA is just "comment [WORD] for the full guide." That's it. Let the value sell.

7. EMOTIONAL PACING — the script should feel like a rollercoaster:
   Hook = shock/curiosity → Tension = anxiety/recognition → Value = relief/understanding →
   Payoff = empowerment/clarity → CTA = simple action

8. WRITE FOR THE EAR — read each script out loud. If it sounds like a blog post, rewrite it.
   Use conversational connectors: "Look.", "Here's the thing.", "And this is the part that
   gets me.", "Stay with me on this."

Format each script as:

SCRIPT [number]:
Title: [short title for this script]
Keyword: [CTA keyword]
Psychology: [main psychology principle used]

[HOOK - 0:00-0:03]
(the exact words the avatar says)

[TENSION - 0:03-0:15]
(the exact words)

[VALUE - 0:15-0:45]
(the exact words — this is the longest section)

[PAYOFF - 0:45-0:55]
(the exact words)

[CTA - 0:55-0:60]
(the exact words)

Caption: (the Instagram caption — authentic, 1-2 sentences max, no emoji spam)

==="""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            return self._parse_ai_scripts(raw_text)
        except Exception as e:
            print(f"    AI script generation failed ({e}), using templates...")
            return self._generate_template_scripts(niche, hooks)

    def _parse_ai_scripts(self, raw_text):
        """Parse Claude's script output into structured dicts."""
        scripts = []
        current = {}
        current_section = None
        section_map = {
            "[HOOK": "hook",
            "[TENSION": "tension",
            "[VALUE": "value",
            "[PAYOFF": "payoff",
            "[CTA": "cta",
        }

        for line in raw_text.split("\n"):
            stripped = line.strip()

            if stripped.startswith("SCRIPT") and ":" in stripped:
                if current and current.get("hook"):
                    scripts.append(current)
                current = {"number": len(scripts) + 1}
                current_section = None
            elif stripped.startswith("Title:"):
                current["title"] = stripped[6:].strip()
            elif stripped.startswith("Keyword:"):
                current["keyword"] = stripped[8:].strip()
            elif stripped.startswith("Psychology:"):
                current["psychology"] = stripped[11:].strip()
            elif stripped.startswith("Caption:"):
                current["caption"] = stripped[8:].strip()
                current_section = "caption"
            else:
                # Check for section markers
                found_section = False
                for marker, section_name in section_map.items():
                    if stripped.startswith(marker):
                        current_section = section_name
                        found_section = True
                        break
                if not found_section and current_section and stripped and not stripped.startswith("==="):
                    existing = current.get(current_section, "")
                    current[current_section] = (existing + "\n" + stripped).strip()

        if current and current.get("hook"):
            scripts.append(current)

        return scripts

    def _generate_template_scripts(self, niche, hooks=None):
        """Fallback template scripts when AI is unavailable."""
        topic = niche.name.split(":")[-1].strip() if ":" in niche.name else niche.name
        scripts = []

        hook_texts = []
        if hooks:
            hook_texts = [h.get("text", "") for h in hooks[:config.SCRIPTS_PER_NICHE]]
        if not hook_texts:
            hook_texts = [f"Nobody is telling you the truth about {topic.lower()}. So let me."]

        for i, hook_text in enumerate(hook_texts):
            scripts.append({
                "number": i + 1,
                "title": f"{topic} Script #{i + 1}",
                "keyword": topic.upper().split()[0] if topic else "GUIDE",
                "psychology": "Authority + curiosity gap",
                "hook": hook_text,
                "tension": f"I see this every single day in my practice. People come to me struggling with {topic.lower()}, "
                           f"and they're all making the same mistake. The advice they're following? It's actually making things worse.",
                "value": f"Here's what actually works — and I know because I've walked hundreds of people through this exact situation. "
                         f"The key isn't what everyone thinks. It's not about willpower or motivation. "
                         f"It's about understanding the system that's working against you and flipping it.",
                "payoff": f"Once you see this, you can't unsee it. And that's when everything changes.",
                "cta": f"Comment {topic.upper().split()[0]} and I'll send you the complete breakdown.",
                "caption": f"The truth about {topic.lower()} that changes everything. Save this.",
            })

        return scripts

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
                "text": f"Someone posted '{title[:70]}' — and here's what they're actually dealing with.",
                "psychology": "Contrarian + curiosity gap + expert authority",
                "reel_outline": f"Reference the real post as a case study, break down the real issue from an expert lens, give the actual solution for {topic}.",
                "caption": f"I see this pattern every day. Here's what's really going on. | Follow for more {niche} insights",
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
        """Proven hook templates based on psychology — all from EXPERT/COACH POV."""
        return [
            {
                "template": "Nobody in your life is going to tell you the truth about {topic}. So let me.",
                "psychology": "Curiosity gap + authority positioning",
                "outline": "Reveal a hidden truth about {topic} from an expert lens. Reference patterns seen across hundreds of clients. End with actionable takeaway.",
                "caption": "The truth about {topic} that nobody around you will say out loud. Save this. | Follow for more {niche} insights",
            },
            {
                "template": "If you're struggling with {topic}, stop doing what everyone tells you. Here's what I tell my clients instead.",
                "psychology": "Contrarian positioning + expert authority",
                "outline": "Challenge the mainstream approach to {topic}. Present the counterintuitive method that actually works. Back with client results.",
                "caption": "Stop following the crowd on {topic}. There's a better way. | Link in bio for the full guide",
            },
            {
                "template": "Every person I've coached on {topic} makes this same mistake in the first week.",
                "psychology": "Loss aversion + authority + pattern recognition",
                "outline": "Share the #1 mistake you see across all clients. Frame as avoidable. Deliver the fix. CTA to free guide.",
                "caption": "This one mistake is costing you more than you think. Don't make it. | Free guide in bio",
            },
            {
                "template": "The real reason you can't fix your {topic} problem has nothing to do with {topic}.",
                "psychology": "Curiosity gap + reframing",
                "outline": "Reframe the {topic} problem as a deeper root cause issue. Provide expert diagnosis. Give one actionable step.",
                "caption": "It's not about {topic}. It never was. | Follow for daily {niche} wisdom",
            },
            {
                "template": "After helping 300+ people with {topic}, here's the pattern nobody talks about.",
                "psychology": "Social proof + curiosity + authority",
                "outline": "Reveal a hidden pattern only visible after coaching many people. Make it feel like insider knowledge. Give a simplified framework.",
                "caption": "This pattern changes everything once you see it. | Save this",
            },
            {
                "template": "You're not lazy. You're not broken. Your approach to {topic} is just wrong. Let me show you.",
                "psychology": "Identity validation + reframing + authority",
                "outline": "Validate the audience's struggle. Diagnose the real issue from expert perspective. Give them a new mental model.",
                "caption": "It was never your fault. Here's what's actually going on. | Share with someone who needs this",
            },
            {
                "template": "If you earn under $100K and you're ignoring {topic}, let me show you what that's actually costing you.",
                "psychology": "Loss aversion + urgency + expert quantification",
                "outline": "Paint the cost of inaction using real numbers from client experience. Show what they're leaving on the table. Give the first step.",
                "caption": "This is your sign to take {topic} seriously. Before it gets worse. | Free playbook in bio",
            },
            {
                "template": "I've seen this destroy people's {topic} goals over and over. Here's how to avoid it.",
                "psychology": "Fear + authority + reciprocity",
                "outline": "Describe the pattern you see repeatedly as an expert. For each failure pattern, give the fix. End with a framework.",
                "caption": "I keep seeing this play out. Don't let it happen to you. | Follow for more",
            },
            {
                "template": "The {topic} advice all over the internet is making your problem worse. Here's what actually works.",
                "psychology": "Pattern interrupt + enemy framing + authority",
                "outline": "Call out popular bad advice from an expert perspective. Explain why it backfires. Present what works based on real results.",
                "caption": "Stop Googling {topic} advice. Most of it is wrong. Here's what I tell my clients. | Save this",
            },
            {
                "template": "Your {topic} problem isn't what you think it is. I've seen this hundreds of times.",
                "psychology": "Curiosity + authority + pattern recognition",
                "outline": "Diagnose the real problem behind {topic} struggles. Share the common misdiagnosis vs reality. Give the viewer the correct first step.",
                "caption": "Once you see the real problem, the solution becomes obvious. | Link in bio",
            },
            {
                "template": "Your parents never taught you this about {topic}. And it's costing you thousands.",
                "psychology": "Loss aversion + blame displacement + authority",
                "outline": "Reveal a generational blind spot about {niche} from expert perspective. Quantify the cost. Show the fix is simpler than they think.",
                "caption": "What they never taught us about {topic} is holding an entire generation back. | Follow for daily tips",
            },
            {
                "template": "I need to address something about {topic} that's going to make some people uncomfortable.",
                "psychology": "Pattern interrupt + controversy + authority",
                "outline": "Take a bold expert stance on {topic}. Back it up with evidence and client results. CTA to deeper content.",
                "caption": "Uncomfortable truths about {topic} that need to be said by someone who sees the full picture. | Like if you agree",
            },
            {
                "template": "Stop telling yourself you'll figure out {topic} later. I've seen what 'later' actually looks like.",
                "psychology": "Urgency + loss aversion + expert witness",
                "outline": "Paint the consequences of procrastination using real client stories. Give one action they can take TODAY.",
                "caption": "'Later' is the most expensive word in {topic}. Start now. | Free starter guide in bio",
            },
            {
                "template": "There's a 3-minute {topic} exercise I give all my clients. Most say it changed everything.",
                "psychology": "Curiosity + simplicity + social proof",
                "outline": "Deliver a genuinely useful quick technique for {topic}. Frame it as your go-to recommendation that gets consistent results.",
                "caption": "This exercise works every time. Simple but powerful. | Save it, try it tonight",
            },
            {
                "template": "If {topic} keeps you up at night, that actually tells me something important about where you are.",
                "psychology": "Reframing + empathy + expert diagnosis",
                "outline": "Normalize the anxiety around {niche}. Diagnose what the anxiety signals about their stage. Give the next step past it.",
                "caption": "Your anxiety about {topic} is data, not a death sentence. Let me decode it. | Follow for the mindset shift",
            },
        ]
