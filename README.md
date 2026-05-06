# 📰 每日国际新闻机器人

自动抓取国际新闻（热点、国际局势、AI/科技、科研成果），每天早上 7:30 发送邮件摘要。

## 技术栈

- **Python 3.11+** — 异步抓取（aiohttp）+ RSS 解析（feedparser）
- **GitHub Actions** — 定时触发，每天 UTC 23:30（北京时间 07:30）
- **SendGrid / SMTP** — 邮件发送

## 快速开始

### 1. Fork / Clone 本仓库

```bash
git clone https://github.com/yuyanghe738/daily-news-bot.git
cd daily-news-bot
```

### 2. GitHub 仓库配置 Secrets

进入仓库 Settings → Secrets and variables → Actions → New repository secret，添加以下之一：

**方式一：SendGrid（推荐）**
1. 注册 [SendGrid](https://sendgrid.com/free/) 免费账号（100封/天）
2. 创建 API Key（Settings → API Keys）
3. 添加 Secret：`SENDGRID_API_KEY`

**方式二：Gmail SMTP**
1. 开启 Gmail 两步验证 → 生成[应用专用密码](https://myaccount.google.com/apppasswords)
2. 添加 Secrets：`SMTP_USER`（Gmail地址）、`SMTP_PASS`（应用专用密码）、`SMTP_SERVER`（smtp.gmail.com）、`SMTP_PORT`（587）

**通用配置（可选）**：
- `TO_EMAIL` — 收件邮箱（默认 yuyanghe738@gmail.com）
- `FROM_EMAIL` — 发件人地址

### 3. 启用 GitHub Actions

Actions 页面会看到 `每日新闻抓取与邮件发送` 工作流，默认每天北京时间 07:30 自动运行。

也可以点 **Run workflow** 手动触发测试。

## 本地运行

```bash
pip install -r requirements.txt

# 设置环境变量后运行
export SENDGRID_API_KEY=SG.xxxxx
export TO_EMAIL=yuyanghe738@gmail.com
python news_bot.py
```

## 数据来源

| 分类 | 来源 |
|------|------|
| 🌍 综合新闻 | BBC, CNN, Reuters, Al Jazeera |
| 🤖 AI/科技 | TechCrunch, ArsTechnica, NVIDIA, Google AI, OpenAI, Anthropic, DeepMind |
| 🔬 科研 | Nature, Science, Phys.org, MIT News |
| 📡 Hacker News | HN 热门 |

## 新闻分类

- 🔥 **热点新闻** — 战争冲突、政治事件、重大事故
- 🌍 **国际局势** — 外交、贸易、联合国、人权
- 🤖 **科技/AI** — 大模型、量子计算、芯片、机器人
- 🔬 **科研成果** — 物理、材料、超导、纳米、能源
