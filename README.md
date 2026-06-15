# Daily News Agent

一个每天自动生成中文新闻摘要的小型 agent。它会抓取 RSS 新闻源，去重、排序，并生成 `reports/YYYY-MM-DD.md` Markdown 日报。

默认行为：

- 每天日本时间 07:00 通过 GitHub Actions 自动运行
- 优先使用 OpenAI 生成更自然的中文摘要
- 没有 `OPENAI_API_KEY` 时自动退回到本地规则摘要
- 自动把当天日报提交回仓库

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
daily-news-agent
```

生成结果会保存到：

```text
reports/YYYY-MM-DD.md
```

## 使用 OpenAI 摘要

复制环境变量模板：

```bash
cp .env.example .env
```

然后填写：

```text
OPENAI_API_KEY=你的_key
OPENAI_MODEL=gpt-4.1-mini
```

也可以不填，agent 会使用本地摘要模式。

## 修改新闻源

编辑 [config/feeds.json](config/feeds.json)。每个新闻源支持：

- `name`: 显示名称
- `url`: RSS 地址
- `section`: 分组，例如 `world`、`japan`、`tech`
- `weight`: 排序权重，越高越容易排在前面

## GitHub Actions 设置

仓库上传到 GitHub 后，如需使用 OpenAI 摘要：

1. 打开仓库的 `Settings`
2. 进入 `Secrets and variables` -> `Actions`
3. 新增 secret：`OPENAI_API_KEY`

不设置 secret 也能运行，只是摘要会更简洁。

## 手动触发

在 GitHub 仓库页面：

1. 打开 `Actions`
2. 选择 `Daily News Agent`
3. 点击 `Run workflow`

## 输出示例

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
