"""
每日新闻机器人 - 配置文件
"""
import os

# ========== 邮件配置（二选一） ==========
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
TO_EMAIL = os.environ.get("TO_EMAIL", "yuyanghe738@gmail.com")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "")

# ========== 翻译配置 ==========
TRANSLATE_TO_CN = os.environ.get("TRANSLATE_TO_CN", "true").lower() == "true"

# ========== 日期范围 ==========
DAYS_BACK = int(os.environ.get("DAYS_BACK", "2"))

# ========== RSS 新闻源 ==========
# 精挑细选的可靠源站，按主题分组
RSS_SOURCES = {
    # ---------- 综合新闻（覆盖热点 + 国际局势） ----------
    "bbc_world":        "https://feeds.bbci.co.uk/news/world/rss.xml",
    "guardian_world":   "https://www.theguardian.com/world/rss",

    # ---------- AI / 科技 ----------
    "bbc_tech":         "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "guardian_tech":    "https://www.theguardian.com/technology/rss",
    "techcrunch":       "https://techcrunch.com/feed/",          # AI/Crypto/Startup
    "arstechnica":      "https://feeds.arstechnica.com/arstechnica/index",
    "nvidia_blog":      "https://blogs.nvidia.com/feed/",
    "google_ai":        "https://blog.google/technology/ai/rss/",
    "openai_blog":      "https://openai.com/news/rss.xml",
    "mit_tech_review":  "https://www.technologyreview.com/feed/",
    "ieee_spectrum":    "https://spectrum.ieee.org/feed/rss",   # 硬件/芯片/Robotics

    # ---------- 科研成果（物理 / 材料 / 前沿科学） ----------
    "bbc_science":      "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "phys_org":         "https://phys.org/rss-feed/",
    "nature_comms":     "https://www.nature.com/ncomms.rss",
    "nature_physics":   "https://www.nature.com/nphys.rss",
    "nature_mat":       "https://www.nature.com/nmat.rss",
    "science_daily":    "https://www.sciencedaily.com/rss/all.xml",
}

# ========== 源站 → 默认分类 ==========
# 来自这些源的新闻优先分配到此分类（除非标题明显属于其他分类）
SOURCE_DEFAULT_CATEGORY = {
    "bbc_world":        "hot",
    "guardian_world":   "hot",
    "bbc_tech":         "ai_tech",
    "guardian_tech":    "ai_tech",
    "techcrunch":       "ai_tech",
    "arstechnica":      "ai_tech",
    "nvidia_blog":      "ai_tech",
    "google_ai":        "ai_tech",
    "openai_blog":      "ai_tech",
    "mit_tech_review":  "ai_tech",
    "ieee_spectrum":    "ai_tech",
    "bbc_science":      "science",
    "phys_org":         "science",
    "nature_comms":     "science",
    "nature_physics":   "science",
    "nature_mat":       "science",
    "science_daily":    "science",
}

# ========== 分类关键词体系 ==========
# 每条规则 = include(必须匹配) + exclude(匹配则排除)
# 优先级: hot > international > ai_tech > science
# 如果一篇文章匹配多个分类，只保留优先级最高的一个

CATEGORIES = {
    "hot": {
        "title": "🔥 热点新闻",
        "max_articles": 10,
        "priority": 1,
        "include": [
            # 战争冲突
            "war", "missile", "strike", "ceasefire", "cease-fire",
            "military", "attack", "drone", "sanction", "blockade",
            "Israel", "Iran", "Gaza", "Hamas", "Hezbollah", "Ukraine",
            "Russia", "nuclear weapon", "troop", "army",
            # 重大灾难
            "explosion", "earthquake", "mass shooting", "terrorist",
            # 重大政治
            "election", "president", "Trump says", "White House",
            "vote of no confidence", "government collapse",
            "assassination", "coup",
            # 中文
            "战争", "袭击", "导弹", "爆炸", "冲突", "总统", "大选",
            "停火", "制裁", "政变", "暗杀",
        ],
        "exclude": [
            # 排除非热点用词
            "review", "opinion", "how to", "guide", "best",
            "game", "movie", "album", "book", "TV show",
            "stock", "IPO", "funding", "investor", "startup",
            "sport", "football", "basketball", "tennis", "F1",
            "AI model", "machine learning", "chip design",
        ],
    },
    "international": {
        "title": "🌍 国际局势",
        "max_articles": 8,
        "priority": 2,
        "include": [
            # 外交 / 国际组织
            "United Nations", "UN ", "NATO", "European Union", "EU ",
            "G7", "G20", "WHO", "IMF", "World Bank", "WTO",
            "AUKUS", "IPEF", "ASEAN",
            # 外交动作
            "sanctions on", "diplomat", "ambassador", "embassy",
            "secretary of state", "foreign minister", "summit",
            "trade war", "tariff", "trade deal", "export control",
            # 地缘政治
            "South China Sea", "Taiwan strait", "Arctic",
            "refugee", "migrant", "asylum",
            # 法律 / 人权
            "human rights", "war crime", "ICC", "ICJ",
            # 中文
            "外交", "联合国", "欧盟", "北约", "贸易战", "关税",
            "难民", "人权", "制裁", "峰会",
        ],
        "exclude": [
            "sport", "movie", "game", "review",
            "AI model", "GPT", "quantum", "robot",
            "stellar", "galaxy", "planet", "space",
            "gene", "DNA", "protein", "cancer",
        ],
    },
    "ai_tech": {
        "title": "🤖 AI / 科技前沿",
        "max_articles": 10,
        "priority": 3,
        "include": [
            # AI 大模型
            "GPT-4", "GPT-5", "Claude", "Gemini", "LLM", "large language model",
            "OpenAI", "Anthropic", "DeepMind", "xAI",
            "foundation model", "frontier model", "AI model",
            "AI agent", "agentic", "autonomous AI",
            # AI 应用
            "machine learning", "deep learning", "neural network",
            "transformer", "diffusion model", "reinforcement learning",
            "computer vision", "natural language processing",
            "AI chip", "GPU", "TPU", "AI accelerator",
            # 芯片 / 半导体
            "semiconductor", "chip design", "processor",
            "NVIDIA", "TSMC", "Intel", "AMD",
            # 量子计算
            "quantum computer", "quantum processor", "qubit",
            "quantum supremacy", "quantum error correction",
            # 机器人
            "humanoid robot", "robotaxi", "autonomous driving",
            # 中文
            "人工智能", "大模型", "AI芯片", "量子计算", "量子比特",
            "自动驾驶", "机器人", "芯片", "半导体",
        ],
        "exclude": [
            "sport", "movie", "game review", "album",
            "cooking", "recipe", "fashion",
            "stock price", "IPO", "funding round", "venture capital",
            "bacteria", "virus", "protein", "DNA", "gene therapy",
            "planet", "asteroid", "black hole", "galaxy",
        ],
    },
    "science": {
        "title": "🔬 科研成果（物理 & 材料）",
        "max_articles": 8,
        "priority": 4,
        "include": [
            # 物理
            "quantum physics", "quantum state", "quantum material",
            "superconduct", "topological", "magnon", "phonon",
            "photon", "particle physics", "CERN", "LHC",
            "nuclear fusion", "tokamak", "plasma",
            "graphene", "moiré", "2D material",
            "condensed matter", "spintronics",
            # 材料科学
            "material science", "new material", "nanomaterial",
            "nanoparticle", "nanowire", "perovskite",
            "catalyst", "battery technology", "solid-state battery",
            "MOF", "metamaterial", "high-entropy alloy",
            "ferroelectric", "multiferroic", "piezoelectric",
            # 光学 / 光电子
            "optoelectronic", "photovoltaic", "LED",
            "laser physics", "metasurface",
            # 中文
            "超导", "量子物理", "核聚变", "纳米", "拓扑",
            "材料科学", "催化剂", "电池", "钙钛矿",
            "光子", "凝聚态",
        ],
        "exclude": [
            "AI model", "GPT", "LLM", "machine learning",
            "stock", "IPO", "funding", "startup",
            "sport", "movie", "game", "album",
            "election", "president", "vote",
            "recipe", "fashion", "travel",
            "cancer treatment", "drug", "vaccine", "clinical trial",
            "gene", "DNA", "protein", "cell", "virus", "bacteria",
        ],
    },
}

# ========== 分类优先级顺序（priority 数字越小越优先） ==========
CATEGORY_PRIORITY = sorted(CATEGORIES.keys(), key=lambda c: CATEGORIES[c]["priority"])

# ========== 抓取参数 ==========
MAX_PER_SOURCE = 20
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
