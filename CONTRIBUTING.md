# Contributing to Smart Knowledge Gap System

Thank you for your interest in contributing! This document explains how to get involved.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)

---

## Code of Conduct

By participating, you agree to:

- Be respectful and inclusive
- Welcome newcomers and beginners
- Give and accept constructive feedback gracefully
- Focus on what's best for the project and community

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report:

1. **Search existing issues** to avoid duplicates
2. **Check the latest version** — it may already be fixed
3. **Reproduce the bug** to confirm it exists

When creating an issue, include:

- **Title:** Clear and descriptive
- **Steps to reproduce:** Numbered, minimal
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happens
- **Environment:** OS, Python version, browser
- **Screenshots:** If applicable

### 💡 Suggesting Features

Feature requests are welcome! Please:

1. Check existing issues first
2. Explain **why** this feature matters
3. Describe expected behavior
4. Provide examples if helpful

### 🔧 Code Contributions

We welcome:

- Bug fixes
- New ML models or improvements
- UI/UX enhancements
- Documentation improvements
- Test coverage expansion
- Performance optimizations

---

## Development Setup

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/Smart-Knowledge-Gap-System.git
cd Smart-Knowledge-Gap-System
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black isort
```

### 4. Configure Environment

```bash
cp .env.example .env
```

### 5. Initialize Database

```bash
python -m app.init_database
```

### 6. Run the App

```bash
python -m app.app
```

### 7. Run Tests

```bash
pytest tests/test_complete.py -v
```

---

## Coding Guidelines

### Python Style

- **PEP 8** compliant
- **Max line length:** 100 characters
- **Type hints** for function signatures
- **Docstrings** for public functions
- **f-strings** for formatting

### Formatting

```bash
black app/ ml/ tests/
isort app/ ml/ tests/
flake8 app/ ml/ tests/ --max-line-length=100
```

---

## Commit Conventions

We follow **Conventional Commits**:

```
<type>(<scope>): <subject>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting |
| `refactor` | Restructuring |
| `perf` | Performance |
| `test` | Tests |
| `chore` | Build, CI |
| `ml` | ML model changes |

### Examples

```bash
git commit -m "feat(auth): add password reset via email"
git commit -m "fix(assessment): handle empty question bank"
git commit -m "ml(risk): improve F1 from 87% to 89.63%"
```

---

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### 2. Make Changes

- Write clean, tested code
- Update documentation
- Add tests for new features

### 3. Test Locally

```bash
pytest tests/ -v
black --check app/ ml/
```

### 4. Commit & Push

```bash
git add .
git commit -m "feat(scope): description"
git push origin feature/amazing-feature
```

### 5. Open Pull Request

- **Base branch:** `main`
- **Title:** Clear and descriptive
- **Link related issues:** `Closes #123`

---

## Testing

### Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov=ml --cov-report=html
```

### Writing Tests

- Place tests in `tests/`
- Use descriptive names: `test_<action>_<outcome>`
- Follow **Arrange-Act-Assert** pattern
- Mock external services (Supabase, Qdrant, Groq)

---

## Project Structure

```
app/          → Flask app + business logic
ml/           → Machine learning models
templates/    → Jinja2 HTML templates
static/       → CSS, JS, images
data/         → Question bank
docs/         → Documentation, screenshots, video
tests/        → Test suite
```

---

## Questions?

- Open a [Discussion](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/discussions)
- Open an [Issue](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/issues)

---

**Thank you for contributing! ⭐**
