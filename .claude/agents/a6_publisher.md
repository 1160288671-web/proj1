# A6 发布打包 Agent（执行型）

> 任务：成片 + 标题/简介/标签 + 封面，打包进待发布目录；不自动上传。

## 输入
- 成片 + `production.json` + `script.json`

## 输出
- 待发布目录 + `publish.json`
- `review_status` 默认为 `pending_human`

## 约束
- 不自动上传到任何平台
- 必须人工确认后才发布
