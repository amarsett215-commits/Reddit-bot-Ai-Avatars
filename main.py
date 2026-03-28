#!/usr/bin/env python3
"""
Niche Scout v2.0 - AI-Powered Niche Discovery Engine
=====================================================

Two-phase system to save API credits and find the best niches:

  Phase 1 — HUNT (no API credits used):
    python main.py
    Scrapes Reddit + Quora, scores niches, keeps scanning until it finds
    3 niches scoring 70+ (configurable). Outputs a scorecard report.

  Phase 2 — GENERATE (uses Claude API for brilliant hooks):
    python main.py --generate 1
    Generates AI hooks + full strategy for niche #1 from last hunt.

Options:
    python main.py                    # Hunt for niches (Phase 1)
    python main.py --generate 1       # Generate hooks for niche #1
    python main.py --generate 1 2 3   # Generate hooks for niches 1, 2, 3
    python main.py --threshold 80     # Set minimum score to 80
    python main.py --rounds 8         # Allow up to 8 scan rounds
"""

import argparse
import json
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
    ╔══════════════════════════════════════════════════════╗
    ║          NICHE SCOUT v2.0                            ║
    ║   AI-Powered Niche Discovery for IG Avatars          ║
    ║                                                      ║
    ║   Phase 1: Hunt (find niches)                        ║
    ║   Phase 2: Generate (hooks for your pick)            ║
    ╚══════════════════════════════════════════════════════════╝
    """)


def hunt(args):
    """
    Phase 1: HUNT — Scrape, analyze, score.
    Keeps scanning new subreddit batches until it finds enough
    high-scoring niches or hits the max round limit.
    No API credits used.
    """
    start_time = time.time()
    threshold = args.threshold
    max_rounds = args.rounds
    target = config.TARGET_NICHES

    print(f"\n  Target: {target} niches scoring {threshold}+")
    print(f"  Max scan rounds: {max_rounds}")

    reddit_scraper = RedditScraper()
    quora_scraper = QuoraScraper()
    nlp_engine = NLPEngine()
    demand_analyzer = DemandAnalyzer(nlp_engine)
    scorer = SuperNicheScorer()

    # Track which subreddits we've already scanned
    scanned_subs = set()
    all_reddit_data = {}
    all_quora_data = {}
    best_niches = []

    for round_num in range(1, max_rounds + 1):
        print(f"\n{'=' * 60}")
        print(f"  ROUND {round_num}/{max_rounds}")
        print(f"{'=' * 60}")

        # ----- SCRAPE -----
        print(f"\n  [Reddit - Round {round_num}]")
        reddit_data = reddit_scraper.scrape(exclude_subs=scanned_subs)

        # Track what we scanned
        for cat, subs in reddit_data.items():
            for sub_data in subs:
                scanned_subs.add(sub_data.name)

        # Merge into cumulative data
        for cat, subs in reddit_data.items():
            if cat not in all_reddit_data:
                all_reddit_data[cat] = []
            all_reddit_data[cat].extend(subs)

        total_posts = sum(
            len(sub.posts)
            for subs in reddit_data.values()
            for sub in subs
        )
        print(f"\n  Round {round_num} Reddit: {total_posts} qualifying posts")

        # Quora
        if not args.no_quora:
            print(f"\n  [Quora - Round {round_num}]")
            quora_categories = list(reddit_data.keys())
            quora_data = quora_scraper.scrape(categories=quora_categories)
            for cat, qs in quora_data.items():
                if cat not in all_quora_data:
                    all_quora_data[cat] = []
                all_quora_data[cat].extend(qs)
            total_quora = sum(len(qs) for qs in quora_data.values())
            print(f"  Round {round_num} Quora: {total_quora} questions")

        # ----- ANALYZE + SCORE (on ALL cumulative data) -----
        print(f"\n  Analyzing all cumulative data...")
        niche_candidates = demand_analyzer.analyze(all_reddit_data, all_quora_data)

        scored_niches = scorer.score_all(niche_candidates)

        # How many pass the threshold?
        passing = [n for n in scored_niches if n.super_niche_score >= threshold]

        print(f"\n  Round {round_num} results:")
        print(f"  Total niches found: {len(scored_niches)}")
        print(f"  Passing {threshold}+ threshold: {len(passing)}/{target}")
        print()
        for i, niche in enumerate(scored_niches[:8], 1):
            marker = " <<<" if niche.super_niche_score >= threshold else ""
            print(
                f"    #{i} {niche.name:<40} "
                f"Score: {niche.super_niche_score:>5.1f}/100{marker}"
            )

        best_niches = scored_niches

        if len(passing) >= target:
            print(f"\n  TARGET HIT! Found {len(passing)} niches scoring {threshold}+")
            break
        elif round_num < max_rounds:
            print(f"\n  Need {target - len(passing)} more. Scanning again...")
        else:
            print(f"\n  Max rounds reached. Showing best results found.")

    # ----- SAVE RESULTS -----
    elapsed = time.time() - start_time

    # Save the niche data so Phase 2 can load it
    report_gen = ReportGenerator()
    paths = report_gen.generate(
        best_niches,
        hooks_by_niche={},        # No hooks in Phase 1
        strategies_by_niche={},   # No strategies in Phase 1
    )

    # Also save machine-readable data for Phase 2
    _save_hunt_data(best_niches, report_gen.timestamp)

    passing_final = [n for n in best_niches if n.super_niche_score >= threshold]

    print(f"\n{'=' * 60}")
    print(f"  HUNT COMPLETE — {elapsed:.0f} seconds")
    print(f"  {len(scanned_subs)} subreddits scanned across {round_num} round(s)")
    print(f"  {len(passing_final)} niches scoring {threshold}+")
    print(f"{'=' * 60}")

    print(f"\n  Reports saved:\n")
    for fmt, path in paths.items():
        print(f"    {fmt.upper():>10}: {os.path.abspath(path)}")

    print(f"\n  NEXT STEP: Review the report, then generate hooks for your picks:")
    print(f"    python main.py --generate 1        # hooks for niche #1")
    print(f"    python main.py --generate 1 2 3    # hooks for top 3")
    print()

    return paths


def generate(args):
    """
    Phase 2: GENERATE — Load last hunt results, generate AI hooks
    and strategies for the user's chosen niches. This is where
    API credits are spent.
    """
    picks = args.generate  # list of niche numbers like [1, 2, 3]

    # Load the last hunt data
    hunt_data = _load_latest_hunt_data()
    if not hunt_data:
        print("\n  ERROR: No hunt data found. Run 'python main.py' first to hunt for niches.")
        sys.exit(1)

    niches = hunt_data["niches"]
    print(f"\n  Loaded {len(niches)} niches from last hunt ({hunt_data['timestamp']})")
    print()

    # Validate picks
    for pick in picks:
        if pick < 1 or pick > len(niches):
            print(f"  ERROR: Niche #{pick} doesn't exist. Max is #{len(niches)}")
            sys.exit(1)

    selected = [niches[p - 1] for p in picks]

    # Show what we're generating for
    for niche_data in selected:
        print(f"  Generating for: #{niche_data['rank']} {niche_data['name']} "
              f"(Score: {niche_data['score']})")

    # Reconstruct minimal niche objects for the hook generator
    from analyzer.demand_analyzer import NicheCandidate
    hook_generator = HookGenerator()

    if not hook_generator.use_ai:
        print("\n  WARNING: No Anthropic API key. Using template hooks.")
        print("  For 10x better hooks, add ANTHROPIC_API_KEY to .env\n")

    hooks_by_niche = {}
    strategies_by_niche = {}
    scripts_by_niche = {}

    for niche_data in selected:
        niche = _reconstruct_niche(niche_data)

        print(f"\n  Generating for: {niche.name}")

        # Generate strategy FIRST so hooks can use the avatar persona
        print("    Strategy...", end=" ", flush=True)
        strategy = hook_generator.generate_content_strategy(niche)
        strategies_by_niche[niche.name] = strategy
        print("done")

        print("    Hooks (from avatar POV)...", end=" ", flush=True)
        hooks = hook_generator.generate_hooks(niche, strategy_text=strategy)
        hooks_by_niche[niche.name] = hooks
        print(f"{len(hooks)} hooks")

        print("    Full scripts...", end=" ", flush=True)
        scripts = hook_generator.generate_scripts(niche, strategy_text=strategy, hooks=hooks)
        scripts_by_niche[niche.name] = scripts
        print(f"{len(scripts)} scripts")

    # Generate report with hooks
    # Reconstruct all niches (to keep the full scorecard) but only with hooks for picked ones
    all_niches_reconstructed = [_reconstruct_niche(nd) for nd in niches]

    report_gen = ReportGenerator()
    paths = report_gen.generate(
        all_niches_reconstructed, hooks_by_niche, strategies_by_niche,
        scripts_by_niche=scripts_by_niche,
    )

    print(f"\n{'=' * 60}")
    print(f"  GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"\n  Reports with hooks saved:\n")
    for fmt, path in paths.items():
        print(f"    {fmt.upper():>10}: {os.path.abspath(path)}")
    print()

    return paths


# =====================================================================
# Hunt data persistence (saves/loads between Phase 1 and Phase 2)
# =====================================================================

def _save_hunt_data(scored_niches, timestamp):
    """Save niche data so Phase 2 can load it without re-scraping."""
    os.makedirs("output", exist_ok=True)
    data = {
        "timestamp": timestamp,
        "niches": [],
    }
    for rank, niche in enumerate(scored_niches[:config.TOP_NICHES_TO_REPORT], 1):
        data["niches"].append({
            "rank": rank,
            "name": niche.name,
            "category": niche.category,
            "score": niche.super_niche_score,
            "scores": getattr(niche, "scores", {}),
            "nlp_scores": niche.nlp_scores,
            "total_posts": niche.total_posts,
            "total_engagement": niche.total_engagement,
            "avg_post_score": niche.avg_post_score,
            "subscriber_reach": niche.subscriber_reach,
            "subreddits": niche.subreddits,
            "cross_subreddit_count": niche.cross_subreddit_count,
            "content_velocity": niche.content_velocity,
            "quora_questions": niche.quora_questions[:20],
            "quora_question_count": niche.quora_question_count,
            "themes": niche.themes,
            "top_posts": [
                {
                    "post_title": p.get("post_title", ""),
                    "post_url": p.get("post_url", ""),
                    "raw_engagement": p.get("raw_engagement", 0),
                    "subreddit": p.get("subreddit", ""),
                }
                for p in niche.top_posts[:15]
            ],
        })

    path = os.path.join("output", "latest_hunt.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _load_latest_hunt_data():
    """Load the most recent hunt data."""
    path = os.path.join("output", "latest_hunt.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _reconstruct_niche(niche_data):
    """Reconstruct a NicheCandidate from saved hunt data."""
    from analyzer.demand_analyzer import NicheCandidate
    niche = NicheCandidate(
        name=niche_data["name"],
        category=niche_data["category"],
    )
    niche.super_niche_score = niche_data.get("score", 0)
    niche.scores = niche_data.get("scores", {})
    niche.nlp_scores = niche_data.get("nlp_scores", {})
    niche.total_posts = niche_data.get("total_posts", 0)
    niche.total_engagement = niche_data.get("total_engagement", 0)
    niche.avg_post_score = niche_data.get("avg_post_score", 0)
    niche.subscriber_reach = niche_data.get("subscriber_reach", 0)
    niche.subreddits = niche_data.get("subreddits", [])
    niche.cross_subreddit_count = niche_data.get("cross_subreddit_count", 0)
    niche.content_velocity = niche_data.get("content_velocity", 0)
    niche.quora_questions = niche_data.get("quora_questions", [])
    niche.quora_question_count = niche_data.get("quora_question_count", 0)
    niche.themes = niche_data.get("themes", {})
    niche.top_posts = niche_data.get("top_posts", [])
    return niche


# =====================================================================
# CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Niche Scout v2.0 — Find profitable niches for AI avatar IG pages"
    )
    parser.add_argument(
        "--generate",
        nargs="+",
        type=int,
        help="Phase 2: Generate hooks for specific niche numbers (e.g. --generate 1 2 3)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=config.MIN_NICHE_SCORE,
        help=f"Minimum niche score to accept (default: {config.MIN_NICHE_SCORE})",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=config.MAX_SCAN_ROUNDS,
        help=f"Max scan rounds (default: {config.MAX_SCAN_ROUNDS})",
    )
    parser.add_argument(
        "--no-quora",
        action="store_true",
        help="Skip Quora scraping",
    )

    args = parser.parse_args()

    print_banner()

    if args.generate:
        # Phase 2: Generate hooks for selected niches
        generate(args)
    else:
        # Phase 1: Hunt for niches
        hunt(args)


if __name__ == "__main__":
    main()
