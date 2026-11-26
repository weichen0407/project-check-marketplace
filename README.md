# Project Check Marketplace

「项目检查」GitHub 版提供研发降本、TRIZ 创新和 TRIZ 案例库，以及综合项目检查、定时任务和 Markdown／HTML 阶段报告的 Skills。降本和 TRIZ 创新的云端服务提供原生交互页面，定时任务使用 Codex Scheduled。用户无需安装 Python。

## 安装

确认本机已安装 Codex CLI，并已用 Git 登录有此私有仓库访问权限的 GitHub 账号。

```bash
codex plugin marketplace add weichen0407/project-check-marketplace && codex plugin add project-check@project-check-marketplace
```

安装后打开新的 Codex 聊天，选择 **Project Check · GitHub**，输入「用 TRIZ 案例库查询技术功效标准词」测试。

## 更新

```bash
codex plugin marketplace upgrade project-check-marketplace && codex plugin add project-check@project-check-marketplace
```
