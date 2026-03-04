# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core Claude AI agent (`agent.py`) — agentic loop with `claude-sonnet-4-6` + `web_search` tool
- Telegram sender (`telegram_sender.py`) — HTML formatting, message splitting, connection test
- Local scheduler (`scheduler.py`) — 15-minute interval for dev testing
- GitHub Actions workflow (`gld_agent.yml`) — cron every 15 min, Mon–Fri 8:30am–3:00pm CST
- Trading-hours time-check step in workflow (skips outside market hours)
- Manual workflow_dispatch trigger for on-demand testing
- `.env.example` with all 3 required secrets documented
- `requirements.txt` with pinned dependencies (anthropic, requests, python-dotenv)
- GitHub community health files (README, CONTRIBUTING, CODE_OF_CONDUCT, LICENSE, SECURITY)
- Issue and pull request templates, Dependabot config
