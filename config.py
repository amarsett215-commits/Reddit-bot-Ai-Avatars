import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API (optional — web scraping works without keys)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "NicheScout/1.0")

# Anthropic API (used only in Phase 2 for hook generation)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# =====================================================================
# HUNT SETTINGS — controls the niche discovery loop
# =====================================================================
MIN_NICHE_SCORE = 70             # Keep scanning until niches hit this score
TARGET_NICHES = 3                # Stop when this many niches pass the threshold
MAX_SCAN_ROUNDS = 5              # Maximum scan rounds before giving best results
SUBS_PER_ROUND = 16              # Subreddits to scan per round (4 categories x 4 subs)

# Scraping settings
REDDIT_POST_LIMIT = 100          # Posts to scan per subreddit (keeps requests low)
MIN_UPVOTES = 50                 # Minimum upvotes to consider a post relevant
MIN_COMMENTS = 20                # Minimum comments to consider
COMMENT_DEPTH = 20               # Top comments to analyze per post

# Analysis settings
MIN_DEMAND_THRESHOLD = 1000      # Minimum total engagement to consider a niche
CROSS_SUB_BONUS = 15             # Bonus points for appearing in 3+ subreddits
TOP_NICHES_TO_REPORT = 7         # Max niches in report (always shows best)
HOOKS_PER_NICHE = 15             # Viral hooks to generate per niche

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "pain_point_intensity": 0.20,
    "demand_volume": 0.12,
    "willingness_to_pay": 0.22,
    "viral_potential": 0.15,
    "content_potential": 0.10,
    "monetization_readiness": 0.10,
    "low_competition": 0.06,
    "scalability": 0.05,
}

# =====================================================================
# SUBREDDIT POOLS — the bot picks randomly from these each round
# Organized by CROSS-CUTTING THEMES, not just basic categories
# The bot thinks outside the box by mixing problem-based + identity-based pools
# =====================================================================
SUBREDDIT_POOLS = {
    # --- MONEY & WEALTH ---
    "money_and_career": [
        "personalfinance", "financialindependence", "povertyfinance",
        "careerguidance", "cscareerquestions", "antiwork", "overemployed",
        "sidehustle", "entrepreneurridealong", "smallbusiness",
        "freelance", "digitalnomad", "investing", "wallstreetbets",
        "realestateinvesting", "creditcards", "debt", "frugal",
        "sales", "resumes", "jobs", "workreform",
    ],

    # --- RELATIONSHIPS & DATING ---
    "relationships_and_dating": [
        "relationship_advice", "dating_advice", "datingoverthirty",
        "breakups", "divorce", "survivinginfidelity", "deadbedrooms",
        "attachment_theory", "socialskills", "loneliness",
        "foreveralone", "hingeapp", "tinder", "bumble",
        "exnocontact", "marriage",
    ],

    # --- PHYSICAL HEALTH & BODY ---
    "health_and_fitness": [
        "loseit", "fitness", "bodyweightfitness", "running",
        "nutrition", "supplements", "sleep", "insomnia",
        "chronicpain", "ibs", "intermittentfasting",
        "keto", "plantbaseddiet", "skincare", "hairloss",
        "PCOS", "backpain", "posture", "weightroom",
        "progresspics", "1200isplenty",
    ],

    # --- MENTAL HEALTH & INNER DEMONS ---
    "mental_health": [
        "anxiety", "depression", "mentalhealth", "adhd",
        "ptsd", "cptsd", "bipolar", "OCD",
        "socialanxiety", "dpdr", "BPD",
        "adhdwomen", "anxietyhelp",
    ],

    # --- SELF IMPROVEMENT & DISCIPLINE ---
    "self_improvement": [
        "selfimprovement", "getdisciplined", "decidingtobebetter",
        "productivity", "getmotivated", "stoicism", "meditation",
        "journaling", "theXeffect", "nofap", "leaves",
        "stopdrinking", "stopsmoking", "nosurf", "pornfree",
    ],

    # --- PARENTING & FAMILY ---
    "parenting_and_family": [
        "parenting", "daddit", "mommit", "newparents",
        "beyondthebump", "toddlers", "homeschool",
        "stepparents", "custody", "workingmoms",
        "sahp", "breakingmom",
    ],

    # --- TECH, SKILLS & CAREER PIVOTS ---
    "tech_and_skills": [
        "learnprogramming", "webdev", "datascience",
        "machinelearning", "photography",
        "videography", "graphic_design", "writing",
        "languagelearning", "excel", "ITcareerquestions",
        "copywriting", "UXDesign",
    ],

    # --- HOUSING & FINANCIAL SURVIVAL ---
    "housing_and_living": [
        "firsttimehomebuyer", "realestate", "landlord",
        "homeimprovement", "minimalism",
        "vanlife", "expats", "almosthomeless",
        "povertyfinance", "EatCheapAndHealthy",
    ],

    # --- LEGAL & LIFE CRISES ---
    "legal_and_life_crises": [
        "legaladvice", "insurance", "scams",
        "raisedbynarcissists", "justnomil", "abusiverelationships",
        "NarcissisticAbuse", "LifeAfterNarcissism",
    ],

    # --- CREATIVE CROSS-CUTTING: IDENTITY CRISES ---
    # People questioning who they are, stuck between lives
    "identity_and_purpose": [
        "findapath", "quarterlifecrisis", "midlifecrisis",
        "careerguidance", "decidingtobebetter",
        "ExperiencedDevs", "30PlusSkinCare",
        "AskMenOver30", "AskWomenOver30",
        "Adulting", "internetparents",
    ],

    # --- CREATIVE CROSS-CUTTING: MONEY ANXIETY ---
    # People stressed about money regardless of income level
    "money_stress": [
        "povertyfinance", "debt", "personalfinance",
        "studentloans", "ynab", "leanfire",
        "overemployed", "antiwork", "teacherreality",
        "nursing", "pharmacy",
    ],

    # --- CREATIVE CROSS-CUTTING: BODY IMAGE & CONFIDENCE ---
    "body_confidence": [
        "loseit", "progresspics", "fitness",
        "skincare", "hairloss", "PlasticSurgery",
        "amiugly", "selfimprovement",
        "malefashionadvice", "femalefashionadvice",
    ],

    # --- CREATIVE CROSS-CUTTING: STARTING OVER ---
    # People rebuilding from scratch (divorce, job loss, addiction)
    "starting_over": [
        "divorce", "stopdrinking", "leaves",
        "ExNoContact", "LifeAfterNarcissism",
        "careerguidance", "almosthomeless",
        "povertyfinance", "decidingtobebetter",
        "NewDads", "singlemoms",
    ],

    # --- CREATIVE CROSS-CUTTING: YOUNG ADULTS STRUGGLING ---
    "young_adults": [
        "GenZ", "college", "findapath",
        "cscareerquestions", "learnprogramming",
        "personalfinance", "Adulting",
        "socialskills", "dating_advice",
        "internetparents", "needadvice",
    ],
}

# Desperation / high-pain language patterns
DESPERATION_KEYWORDS = [
    "please help", "desperate", "at my wit's end", "don't know what to do",
    "ruining my life", "can't take it anymore", "breaking point", "hopeless",
    "need advice urgently", "last resort", "i'm stuck", "i'm lost",
    "anyone else deal with", "is this normal", "i'm struggling",
    "destroying my", "i've tried everything", "nothing works",
    "scared", "terrified", "overwhelmed", "drowning in",
    "can't afford", "going broke", "behind on", "falling apart",
    "wasted years", "biggest mistake", "regret", "trapped",
    "no one understands", "feeling alone", "rock bottom",
]

# Willingness-to-pay signals
PAYMENT_SIGNALS = [
    "worth paying for", "shut up and take my money", "i'd pay for",
    "any course", "any book", "recommendation", "what tool",
    "what app", "what service", "how much does", "is it worth",
    "invested in", "bought a course", "hired a coach", "paid for",
    "subscription", "premium", "membership", "consulting",
    "where can i learn", "best resource", "best book",
    "changed my life", "game changer", "wish i knew sooner",
    "worth every penny", "best investment",
]

# Viral content signals
VIRAL_SIGNALS = [
    "i didn't know", "nobody tells you", "the truth about",
    "wish someone told me", "unpopular opinion", "hot take",
    "controversial", "secret", "hack", "cheat code",
    "mind blown", "this changed everything", "before and after",
    "transformation", "story time", "i was today years old",
    "the real reason", "what they don't teach you",
    "stop doing this", "biggest mistake people make",
]

# Psychology hooks for content
PSYCHOLOGY_FRAMEWORKS = [
    "loss_aversion",        # People fear losing more than gaining
    "curiosity_gap",        # Open a loop, close it later
    "social_proof",         # Everyone else is doing it
    "authority_bias",       # Expert says so
    "scarcity",            # Limited time/spots
    "identity_shift",       # Become the person who...
    "pattern_interrupt",    # Break expectations
    "enemy_framing",        # Us vs them / the system is rigged
    "transformation_arc",   # Before/after story
    "contrarian_take",      # Opposite of what you'd expect
]
