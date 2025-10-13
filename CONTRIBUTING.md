# Contributing to Crypto Trading Signal System

First off, thank you for considering contributing to Crypto Trading Signal System! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

---

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

---

## 🤝 How Can I Contribute?

### 1. Report Bugs
Found a bug? Please create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- System information

### 2. Suggest Features
Have an idea? Create a feature request with:
- Clear use case
- Proposed solution
- Alternative solutions considered
- Additional context

### 3. Submit Code
- Fix bugs
- Implement features
- Improve documentation
- Add tests
- Optimize performance

### 4. Improve Documentation
- Fix typos
- Add examples
- Clarify explanations
- Translate content

---

## 🛠️ Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### Setup Steps
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/crypto-signal-system.git
cd crypto-signal-system

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Install dependencies
cd frontend && npm install
cd ../backend/api-gateway && npm install
cd ../bots && pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Start development environment
docker-compose -f docker-compose.dev.yml up

# Keep your fork updated
git remote add upstream https://github.com/original/crypto-signal-system.git
git fetch upstream
git merge upstream/main

# Create descriptive branch names
git checkout -b feat/add-bollinger-bands-indicator
git checkout -b fix/signal-rr-calculation
git checkout -b docs/update-api-examples

# Make atomic commits
git add specific-file.py
git commit -m "feat(signal-bot): add bollinger bands calculation"

# Push your branch
git push origin feat/add-bollinger-bands-indicator