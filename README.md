# Project Check Marketplace

「项目检查」GitHub 版提供研发降本、TRIZ 创新、TRIZ 案例库，以及技术发现 App、趋势看板和 Markdown／HTML／Word 阶段报告。降本和 TRIZ 的交互页面包含 Eureka 导航。插件通过 HTTPS 调用现有云端服务，用户无需安装 Python。

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
