# Project Check Marketplace

Project Check includes R&D cost optimization, TRIZ innovation and case search, Eureka navigation, the Technology Discovery App, trends boards, and Markdown, HTML, and Word export.

## Install

Use a Codex version with plugin support and a GitHub account with access to this repository. For the complete plugin, install Python 3.11 or newer if it is missing. After installation, `python3 --version` should show an available Python command. The plugin prepares its own dependencies on first startup.

Paste this into a Codex chat to let Codex perform installation:

> Install Project Check from GitHub. Run `codex plugin marketplace add weichen0407/project-check-marketplace` and `codex plugin add project-check@project-check-marketplace`. Check that Python 3.11 or newer is installed. Tell me if I need to install it, then verify the Technology Discovery App in a new chat.

The installation commands are:

```bash
codex plugin marketplace add weichen0407/project-check-marketplace && codex plugin add project-check@project-check-marketplace
```

Restart Codex after installing Python. Open a new chat, select **Project Check · GitHub**, and ask it to open Technology Discovery with fictional demo data.

## Update

```bash
codex plugin marketplace upgrade project-check-marketplace && codex plugin add project-check@project-check-marketplace
```

Open a new chat after updating. Existing product profiles stay in the user data directory and are shared with earlier local Project Check versions.
