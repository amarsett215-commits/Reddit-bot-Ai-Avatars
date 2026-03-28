"""
Report Generator
================
Produces the final niche report in three formats:
  - JSON (machine-readable, for automation)
  - HTML (visual, shareable, beautiful)
  - Markdown (easy to read in any editor)
"""

import json
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

import config


class ReportGenerator:

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def generate(self, scored_niches, hooks_by_niche, strategies_by_niche):
        """Generate all three report formats. Returns dict of file paths."""
        top_niches = scored_niches[:config.TOP_NICHES_TO_REPORT]

        report_data = self._build_report_data(
            top_niches, hooks_by_niche, strategies_by_niche
        )

        paths = {}
        paths["json"] = self._write_json(report_data)
        paths["markdown"] = self._write_markdown(report_data)
        paths["html"] = self._write_html(report_data)

        return paths

    def _build_report_data(self, niches, hooks_by_niche, strategies_by_niche):
        """Structure all data for output."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_niches_analyzed": len(niches),
            "niches": [],
        }

        for rank, niche in enumerate(niches, 1):
            niche_data = {
                "rank": rank,
                "name": niche.name,
                "category": niche.category,
                "super_niche_score": getattr(niche, "super_niche_score", 0),
                "scores": getattr(niche, "scores", {}),
                "stats": {
                    "total_posts_analyzed": niche.total_posts,
                    "total_engagement": niche.total_engagement,
                    "avg_post_score": round(niche.avg_post_score, 1),
                    "subscriber_reach": niche.subscriber_reach,
                    "subreddits_found": niche.subreddits,
                    "cross_subreddit_count": niche.cross_subreddit_count,
                    "content_velocity": round(niche.content_velocity, 2),
                    "quora_questions_found": niche.quora_question_count,
                },
                "themes": niche.themes,
                "top_posts": [
                    {
                        "title": p.get("post_title", ""),
                        "url": p.get("post_url", ""),
                        "engagement": p.get("raw_engagement", 0),
                        "subreddit": p.get("subreddit", ""),
                    }
                    for p in niche.top_posts[:10]
                ],
                "quora_questions": niche.quora_questions[:10],
                "hooks": hooks_by_niche.get(niche.name, []),
                "content_strategy": strategies_by_niche.get(niche.name, ""),
            }
            report["niches"].append(niche_data)

        return report

    def _write_json(self, data):
        """Write JSON report."""
        path = os.path.join(self.output_dir, f"niche_report_{self.timestamp}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def _write_markdown(self, data):
        """Write Markdown report."""
        path = os.path.join(self.output_dir, f"niche_report_{self.timestamp}.md")
        lines = []

        lines.append("# Niche Scout Report")
        lines.append(f"*Generated: {data['generated_at']}*\n")
        lines.append("---\n")

        # Executive summary
        lines.append("## Executive Summary\n")
        top = data["niches"][0] if data["niches"] else None
        if top:
            lines.append(
                f"**#1 Recommended Niche: {top['name']}** "
                f"(Super Niche Score: **{top['super_niche_score']}/100**)\n"
            )
        lines.append(f"Analyzed **{data['total_niches_analyzed']}** niche candidates.\n")
        lines.append("---\n")

        for niche in data["niches"]:
            lines.append(f"## #{niche['rank']}: {niche['name']}")
            lines.append(f"**Super Niche Score: {niche['super_niche_score']}/100**\n")
            lines.append(f"Category: {niche['category']}\n")

            # Score breakdown
            scores = niche.get("scores", {})
            if scores:
                lines.append("### Score Breakdown\n")
                lines.append("| Factor | Score |")
                lines.append("|--------|-------|")
                score_labels = {
                    "pain_point_intensity": "Pain Point Intensity",
                    "demand_volume": "Demand Volume",
                    "willingness_to_pay": "Willingness to Pay",
                    "viral_potential": "Viral Potential",
                    "content_potential": "Content Potential",
                    "monetization_readiness": "Monetization Readiness",
                    "low_competition": "Low Competition",
                    "scalability": "Scalability",
                }
                for key, label in score_labels.items():
                    val = scores.get(key, 0)
                    bar = self._score_bar(val)
                    lines.append(f"| {label} | {val}/100 {bar} |")
                psych = scores.get("psychology_multiplier", 1.0)
                lines.append(f"\n*Psychology Multiplier: {psych}x*\n")

            # Stats
            stats = niche["stats"]
            lines.append("### Demand Signals\n")
            lines.append(f"- **Posts analyzed:** {stats['total_posts_analyzed']}")
            lines.append(f"- **Total engagement:** {stats['total_engagement']:,}")
            lines.append(f"- **Avg post score:** {stats['avg_post_score']}")
            lines.append(f"- **Subscriber reach:** {stats['subscriber_reach']:,}")
            lines.append(f"- **Subreddits:** {', '.join(stats['subreddits_found'])}")
            lines.append(f"- **Content velocity:** {stats['content_velocity']} posts/day")
            lines.append(f"- **Quora questions:** {stats['quora_questions_found']}\n")

            # Themes
            themes = niche.get("themes", {})
            keywords = themes.get("top_keywords", [])
            if keywords:
                lines.append("### Top Themes\n")
                for kw in keywords[:8]:
                    lines.append(f"- **{kw['word']}** (mentioned {kw['count']}x)")
                lines.append("")

            # Top posts
            top_posts = niche.get("top_posts", [])
            if top_posts:
                lines.append("### Top Posts (Proof of Demand)\n")
                for p in top_posts[:5]:
                    lines.append(
                        f"- [{p['title'][:80]}]({p['url']}) "
                        f"— {p['engagement']:,} engagement (r/{p['subreddit']})"
                    )
                lines.append("")

            # Quora questions
            quora = niche.get("quora_questions", [])
            if quora:
                lines.append("### Quora Questions (Additional Demand)\n")
                for q in quora[:5]:
                    lines.append(f"- {q}")
                lines.append("")

            # Hooks
            hooks = niche.get("hooks", [])
            if hooks:
                lines.append("### Viral Hooks\n")
                for hook in hooks:
                    lines.append(f"**Hook #{hook.get('number', '')}:**")
                    lines.append(f"> {hook.get('text', '')}\n")
                    lines.append(f"*Psychology: {hook.get('psychology', '')}*\n")
                    if hook.get("reel_outline"):
                        lines.append(f"Reel outline: {hook['reel_outline']}\n")
                    if hook.get("caption"):
                        lines.append(f"Caption: *{hook['caption']}*\n")
                    lines.append("---\n")

            # Strategy
            strategy = niche.get("content_strategy", "")
            if strategy:
                lines.append("### Full Content & Monetization Strategy\n")
                lines.append(strategy)
                lines.append("")

            lines.append("\n---\n")

        with open(path, "w") as f:
            f.write("\n".join(lines))
        return path

    def _write_html(self, data):
        """Write HTML report using Jinja2 template."""
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(template_dir, exist_ok=True)
        template_path = os.path.join(template_dir, "report.html")

        if not os.path.exists(template_path):
            self._create_default_template(template_path)

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("report.html")

        html = template.render(
            report=data,
            generated_at=data["generated_at"],
        )

        path = os.path.join(self.output_dir, f"niche_report_{self.timestamp}.html")
        with open(path, "w") as f:
            f.write(html)
        return path

    def _score_bar(self, score):
        """Create a visual score bar for markdown."""
        filled = int(score / 10)
        empty = 10 - filled
        return "[" + "#" * filled + "-" * empty + "]"

    def _create_default_template(self, path):
        """Create HTML template if it doesn't exist."""
        # This is a fallback — the real template is in templates/report.html
        with open(path, "w") as f:
            f.write(DEFAULT_HTML_TEMPLATE)


DEFAULT_HTML_TEMPLATE = """<!-- See report/templates/report.html for the full template -->
<!DOCTYPE html>
<html><head><title>Niche Report</title></head>
<body><h1>Niche Scout Report</h1>
<p>Generated: {{ generated_at }}</p>
{% for niche in report.niches %}
<h2>#{{ niche.rank }}: {{ niche.name }} (Score: {{ niche.super_niche_score }})</h2>
{% endfor %}
</body></html>
"""
