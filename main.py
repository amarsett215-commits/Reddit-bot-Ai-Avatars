#!/usr/bin/env python3
"""
Niche Scout - AI-Powered Niche Discovery Engine
================================================
Scrapes Reddit & Quora to find high-profit niches for AI avatar
Instagram pages. Scores each niche on pain, demand, virality,
monetization, and psychology. Outputs a full report with viral
hooks and content strategies.

Usage:
    python main.py              # Full run (Reddit + Quora + AI hooks)
    python main.py --no-quora   # Skip Quora scraping
    python main.py --no-ai      # Skip AI hook generation (use templates)
    python main.py --fast        # Fewer subreddits, faster run
"""

import argparse
import os
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from scraper.reddit_scraper import RedditScraper
from scraper.quora_scraper import QuoraScraper
from analyzer.nlp_engine import NLPEngine
from analyzer.demand_analyzer import DemandAnalyzer
from scorer.super_niche_scorer import SuperNicheScorer
from report.hook_generator import HookGenerator
from report.report_generator import ReportGenerator


def print_banner():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║          NICHE SCOUT v1.0                        ║
    ║   AI-Powered Niche Discovery for IG Avatars      ║
    ╚══════════════════════════════════════════════════╝
    """)


def validate_config():
    """Check configuration. Reddit no longer needs API keys (uses web scraping)."""
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_key":
        print(
            "\n  NOTE: ANTHROPIC_API_KEY not set. "
            "Hook generation will use templates instead of AI.\n"
            "  For 10x better hooks, add your Anthropic API key to .env\n"
        )

    return True


def run(args):
    """Main execution flow."""
    start_time = time.time()
    print_banner()

    if not validate_config():
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 1: SCRAPE
    # ------------------------------------------------------------------
    print("=" * 55)
    print("  PHASE 1: SCRAPING DATA")
    print("=" * 55)

    # Reddit
    print("\n  [Reddit]")
    reddit_scraper = RedditScraper()

    if args.fast:
        # Override to scan fewer subreddits
        original_pick = reddit_scraper._pick_subreddits
        reddit_scraper._pick_subreddits = lambda num_categories=2, subs_per_category=2: original_pick(
            num_categories=2, subs_per_category=2
        )

    reddit_data = reddit_scraper.scrape()

    total_reddit_posts = sum(
        len(sub.posts)
        for subs in reddit_data.values()
        for sub in subs
    )
    print(f"\n  Reddit total: {total_reddit_posts} qualifying posts scraped")

    # Quora
    quora_data = {}
    if not args.no_quora:
        print("\n  [Quora]")
        quora_scraper = QuoraScraper()
        quora_categories = list(reddit_data.keys())
        quora_data = quora_scraper.scrape(categories=quora_categories)
        total_quora = sum(len(qs) for qs in quora_data.values())
        print(f"\n  Quora total: {total_quora} questions found")
    else:
        print("\n  Skipping Quora (--no-quora flag)")

    # ------------------------------------------------------------------
    # Phase 2: ANALYZE
    # ------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  PHASE 2: ANALYZING DATA")
    print("=" * 55)

    nlp_engine = NLPEngine()
    demand_analyzer = DemandAnalyzer(nlp_engine)
    niche_candidates = demand_analyzer.analyze(reddit_data, quora_data)

    # ------------------------------------------------------------------
    # Phase 3: SCORE
    # ------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  PHASE 3: SCORING NICHES")
    print("=" * 55)

    scorer = SuperNicheScorer()
    scored_niches = scorer.score_all(niche_candidates)

    print(f"\n  Scored {len(scored_niches)} niche candidates\n")
    print("  Top candidates:")
    for i, niche in enumerate(scored_niches[:config.TOP_NICHES_TO_REPORT], 1):
        print(
            f"    #{i} {niche.name:<35} "
            f"Score: {niche.super_niche_score:>5.1f}/100"
        )

    # ------------------------------------------------------------------
    # Phase 4: GENERATE HOOKS & STRATEGIES
    # ------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  PHASE 4: GENERATING HOOKS & STRATEGIES")
    print("=" * 55)

    hook_generator = HookGenerator()

    if args.no_ai:
        hook_generator.use_ai = False
        print("\n  Using template-based hooks (--no-ai flag)")
    elif hook_generator.use_ai:
        print("\n  Using Claude AI for hook generation (better quality)")
    else:
        print("\n  Using template-based hooks (no API key)")

    hooks_by_niche = {}
    strategies_by_niche = {}

    top_niches = scored_niches[:config.TOP_NICHES_TO_REPORT]
    for i, niche in enumerate(top_niches, 1):
        print(f"\n  [{i}/{len(top_niches)}] Generating for: {niche.name}")

        print("    Hooks...", end=" ", flush=True)
        hooks = hook_generator.generate_hooks(niche)
        hooks_by_niche[niche.name] = hooks
        print(f"{len(hooks)} hooks")

        print("    Strategy...", end=" ", flush=True)
        strategy = hook_generator.generate_content_strategy(niche)
        strategies_by_niche[niche.name] = strategy
        print("done")

    # ------------------------------------------------------------------
    # Phase 5: GENERATE REPORTS
    # ------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  PHASE 5: GENERATING REPORTS")
    print("=" * 55)

    report_gen = ReportGenerator()
    paths = report_gen.generate(scored_niches, hooks_by_niche, strategies_by_niche)

    elapsed = time.time() - start_time

    print(f"\n  Reports generated in {elapsed:.0f} seconds:\n")
    for fmt, path in paths.items():
        abs_path = os.path.abspath(path)
        print(f"    {fmt.upper():>10}: {abs_path}")

    print("\n" + "=" * 55)
    print("  DONE! Open the HTML report for the best experience.")
    print("=" * 55)
    print()

    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Niche Scout - Find profitable niches for AI avatar IG pages"
    )
    parser.add_argument(
        "--no-quora",
        action="store_true",
        help="Skip Quora scraping",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI-powered hook generation (use templates)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Faster run with fewer subreddits",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
