# Daily Intelligence Brief / デイリー・インテリジェンス・ブリーフ

## English

A scheduled news-intelligence service that collects public news sources, removes duplicates, ranks stories, and produces Japanese and English daily briefings. It also generates a Gmail-friendly HTML email brief with concise article cards and links to the complete reports.

### Outputs

```text
reports/ja/YYYY-MM-DD.md
reports/en/YYYY-MM-DD.md
reports/email/YYYY-MM-DD.html
reports/email/YYYY-MM-DD.txt
```

### What it does

- Runs daily in Japan Standard Time through GitHub Actions
- Uses OpenAI to produce Japanese and English summaries from the collected source material
- Falls back to source-language excerpts when `OPENAI_API_KEY` is unavailable
- Ranks and deduplicates stories, then commits the generated reports back to the repository
- Creates a responsive HTML briefing: 10 article cards per language, each with a title, summary, source, date, and source link

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
daily-news-agent
```

### Enable OpenAI summaries

Copy the environment template:

```bash
cp .env.example .env
```

Then configure:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
NEWS_AGENT_LANGUAGES=ja,en
```

For GitHub Actions, add `OPENAI_API_KEY` under **Settings → Secrets and variables → Actions**. Do not commit API keys to the repository.

### News sources

Edit [config/feeds.json](config/feeds.json) to change the source mix. Each source supports:

- `name`: display name
- `url`: RSS endpoint or API base URL
- `kind`: `rss` (default) or `hacker_news`
- `section`: grouping such as `japan`, `world`, or `tech`
- `weight`: ranking preference; a higher value ranks earlier

The default mix includes Japanese, world, and technology sources, plus the official Hacker News API.

### Run manually on GitHub

1. Open **Actions** in this repository.
2. Select **Daily News Agent**.
3. Choose **Run workflow**.

---

## 中文

这是一个定时运行的新闻情报服务：它抓取公开新闻来源、去重并排序，生成日文和英文日报，同时输出一份适合 Gmail 阅读的 HTML 邮件简报。邮件中每种语言展示 10 条新闻卡片，并保留完整日报与原文链接。

### 输出文件

```text
reports/ja/YYYY-MM-DD.md
reports/en/YYYY-MM-DD.md
reports/email/YYYY-MM-DD.html
reports/email/YYYY-MM-DD.txt
```

### 功能

- 通过 GitHub Actions 按日本时间每日运行
- 使用 OpenAI 基于抓取内容生成日文与英文摘要
- 未配置 `OPENAI_API_KEY` 时，回退到新闻源原文摘录
- 对新闻进行去重、排序，并把生成结果提交回仓库
- 生成响应式 HTML 邮件简报：每种语言 10 条新闻卡片，包含标题、摘要、来源、日期与原文链接

### 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
daily-news-agent
```

### 启用 OpenAI 摘要

复制环境变量模板：

```bash
cp .env.example .env
```

然后填写：

```text
OPENAI_API_KEY=你的_key
OPENAI_MODEL=gpt-4.1-mini
NEWS_AGENT_LANGUAGES=ja,en
```

如需在 GitHub Actions 中启用摘要，请在仓库 **Settings → Secrets and variables → Actions** 中添加 `OPENAI_API_KEY`。不要把密钥提交到仓库。

### 新闻来源

编辑 [config/feeds.json](config/feeds.json) 即可调整来源。每个来源支持：

- `name`：显示名称
- `url`：RSS 地址或 API 基础地址
- `kind`：`rss`（默认）或 `hacker_news`
- `section`：分类，例如 `japan`、`world`、`tech`
- `weight`：排序权重，数值越高越优先

默认来源覆盖日本、国际与科技新闻，并接入 Hacker News 官方 API。

### 在 GitHub 手动运行

1. 打开仓库的 **Actions** 页面。
2. 选择 **Daily News Agent**。
3. 点击 **Run workflow**。
