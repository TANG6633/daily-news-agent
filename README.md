# Daily News Agent / 每日新闻 Agent

## 中文

一个每天自动生成新闻摘要的小型 agent。它会抓取 RSS 新闻源，去重、排序，并同时生成中文版和英文版 Markdown 日报。

默认输出：

```text
reports/zh/YYYY-MM-DD.md
reports/en/YYYY-MM-DD.md
```

默认行为：

- 每天日本时间 07:00 通过 GitHub Actions 自动运行
- 优先使用 OpenAI 生成更自然的中英双语摘要
- 没有 `OPENAI_API_KEY` 时自动退回到本地规则摘要
- 自动把当天日报提交回仓库

### 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
daily-news-agent
```

### 使用 OpenAI 摘要

复制环境变量模板：

```bash
cp .env.example .env
```

然后填写：

```text
OPENAI_API_KEY=你的_key
OPENAI_MODEL=gpt-4.1-mini
NEWS_AGENT_LANGUAGES=zh,en
```

也可以不填 API key，agent 会使用本地摘要模式。本地模式会保留新闻源原文；配置 API key 后会生成更完整的中英双语摘要。

### 修改新闻源

编辑 [config/feeds.json](config/feeds.json)。每个新闻源支持：

- `name`: 显示名称
- `url`: RSS 地址
- `section`: 分组，例如 `world`、`japan`、`tech`
- `weight`: 排序权重，越高越容易排在前面

### GitHub Actions 设置

仓库上传到 GitHub 后，如需使用 OpenAI 摘要：

1. 打开仓库的 `Settings`
2. 进入 `Secrets and variables` -> `Actions`
3. 新增 secret：`OPENAI_API_KEY`

不设置 secret 也能运行，只是摘要会更简洁。

### 手动触发

在 GitHub 仓库页面：

1. 打开 `Actions`
2. 选择 `Daily News Agent`
3. 点击 `Run workflow`

## English

A small daily news agent that collects RSS feeds, deduplicates and ranks articles, then generates both Chinese and English Markdown digests.

Default output:

```text
reports/zh/YYYY-MM-DD.md
reports/en/YYYY-MM-DD.md
```

Default behavior:

- Runs automatically at 07:00 Japan Standard Time via GitHub Actions
- Uses OpenAI first for richer bilingual summaries
- Falls back to local rule-based summaries when `OPENAI_API_KEY` is not configured
- Commits the generated daily reports back to the repository

### Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
daily-news-agent
```

### OpenAI Summaries

Copy the environment template:

```bash
cp .env.example .env
```

Then fill in:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
NEWS_AGENT_LANGUAGES=zh,en
```

The agent can run without an API key, but local fallback summaries keep the original source language. Configure `OPENAI_API_KEY` for fuller Chinese and English summaries.

### Edit News Sources

Edit [config/feeds.json](config/feeds.json). Each source supports:

- `name`: display name
- `url`: RSS feed URL
- `section`: grouping, such as `world`, `japan`, or `tech`
- `weight`: ranking weight; higher values rank earlier

### GitHub Actions Setup

To enable OpenAI summaries on GitHub:

1. Open repository `Settings`
2. Go to `Secrets and variables` -> `Actions`
3. Add a secret named `OPENAI_API_KEY`

The workflow still runs without the secret, using local fallback summaries.

### Manual Run

On GitHub:

1. Open `Actions`
2. Select `Daily News Agent`
3. Click `Run workflow`

### Output Example

```markdown
# 每日新闻总结 - 2026-06-15

## 今日重点

- ...

## Japan

### 新闻标题

摘要内容

来源: NHK News
链接: https://...
```

```markdown
# Daily News Digest - 2026-06-15

## Highlights

- ...

## Japan

### News Title

Summary text.

Source: NHK News
Link: https://...
```
