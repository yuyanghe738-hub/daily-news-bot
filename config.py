"""
每日新闻机器人 - 配置文件
"""
import os

# ========== 邮件配置（二选一） ==========
# 方式一：SendGrid API（推荐）
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")

# 方式二：SMTP（Outlook / Gmail 等）
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")      # 邮箱地址
SMTP_PASS = os.environ.get("SMTP_PASS", "")       # 邮箱密码或应用专用密码

# 收件人
TO_EMAIL = os.environ.get("TO_EMAIL", "yuyanghe738@gmail.com")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "")

# ========== 日期范围 ==========
# 默认抓取昨天+今天，也可以通过环境变量覆盖
DAYS_BACK = int(os.environ.get("DAYS_BACK", "2"))

# ========== RSS 新闻源 ==========
RSS_SOURCES = {
    # 综合新闻
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc_tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "bbc_science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "guardian_world": "https://www.theguardian.com/world/rss",
    "guardian_tech": "https://www.theguardian.com/technology/rss",
    "npr_world": "https://feeds.npr.org/1004/rss.xml",
    "ap_world": "https://rsshub.app/apnews/topics/apf-worldnews",
    "cnn_top": "https://rsshub.app/cnn/top",

    # 科技
    "techcrunch": "https://techcrunch.com/feed/",
    "arstechnica": "https://feeds.arstechnica.com/arstechnica/index",
    "hacker_news": "https://hnrss.org/frontpage",
    "wired": "https://www.wired.com/feed/rss",
    "theverge": "https://www.theverge.com/rss/index.xml",

    # AI 厂商博客
    "nvidia_blog": "https://blogs.nvidia.com/feed/",
    "google_ai": "https://blog.google/technology/ai/rss/",
    "openai_blog": "https://openai.com/news/rss.xml",
    "deepmind_blog": "https://blog.deepmind.com/feed.xml",

    # 科研
    "phys_org": "https://phys.org/rss-feed/",
    "nature_comms": "https://www.nature.com/ncomms.rss",
    "nature_physics": "https://www.nature.com/nphys.rss",
    "nature_mat": "https://www.nature.com/nmat.rss",
    "science_adv": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
    "science_daily": "https://www.sciencedaily.com/rss/all.xml",
    "mit_tech_review": "https://www.technologyreview.com/feed/",
    "ieee_spectrum": "https://spectrum.ieee.org/feed/rss",
}

# ========== 分类关键词 ==========
CATEGORIES = {
    "hot": {
        "keywords": ["伊朗", "Israel", "Iran", "Gaza", "Hamas", "中东", "制裁",
                     "Trump", "总统", "大选", "election", "爆炸", "attack",
                     "冲突", "乌克兰", "Ukraine", "Russia", "俄罗斯", "战争",
                     "台湾", "China", "中国", "南海", "South China", "朝鲜",
                     "核武器", "nuclear", "climate", "气候"],
        "title": "🔥 热点新闻",
        "max_articles": 15,
    },
    "international": {
        "keywords": ["外交", "联合国", "UN", "欧盟", "EU", "NATO", "北约",
                     "东盟", "ASEAN", "G7", "G20", "IMF", "World Bank",
                     "贸易", "tariff", "关税", "制裁", "sanction",
                     "难民", "refugee", "移民", "migrant",
                     "人权", "human rights", "democracy", "民主"],
        "title": "🌍 国际局势",
        "max_articles": 12,
    },
    "ai_tech": {
        "keywords": ["AI", "人工智能", "machine learning", "深度学习",
                     "GPT", "Claude", "Gemini", "LLM", "大模型",
                     "OpenAI", "Anthropic", "Google", "DeepMind",
                     "NVIDIA", "芯片", "quantum computing", "量子计算",
                     "robot", "机器人", "autonomous", "自动驾驶",
                     "neural", "神经网络", "transformer",
                     "agent", "agentic", "robotics"],
        "title": "🤖 科技前沿（AI）",
        "max_articles": 12,
    },
    "science": {
        "keywords": ["物理", "physics", "quantum", "量子", "超导",
                     "superconduct", "材料", "material", "纳米",
                     "nano", "graphene", "石墨烯", "电池", "battery",
                     "光伏", "solar", "fusion", "聚变", "核聚变",
                     "catalyst", "催化", "magnon", "磁子",
                     "Nature", "Science", "光子", "photon",
                     "半导体", "semiconductor", "拓扑"],
        "title": "🔬 科研成果",
        "max_articles": 10,
    },
}

# 最大抓取条数（每个源）
MAX_PER_SOURCE = 25
# 请求超时（秒）
TIMEOUT = 20
# User-Agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
