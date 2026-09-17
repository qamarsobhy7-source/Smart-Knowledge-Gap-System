# Contributing

Thank you for your interest in the Smart Knowledge Gap &
Personalized Learning System.

## Getting Started

1. Fork the repository.
2. Clone your fork:

       git clone https://github.com/<your-username>/smart-knowledge-gap.git
       cd smart-knowledge-gap

3. Create a virtual environment:

       python -m venv .venv
       source .venv/bin/activate     # Linux / macOS
       .venv\Scripts\activate        # Windows

4. Install dependencies:

       pip install -r requirements.txt

5. Copy the environment template and fill in your values:

       cp .env.example .env

6. Initialize the database:

       python -m app.init_database

7. Run the development server:

       python app/app.py

## Coding Standards

- Follow PEP 8 for Python code.
- Keep functions small and focused.
- Add docstrings to all public functions and modules.
- Never commit secrets, credentials, or .env files.

## Branching

- main — stable, deployable.
- feature/<name> — new features.
- fix/<name> — bug fixes.
- docs/<name> — documentation updates.

## Commit Messages

Use clear, imperative commit messages:

- feat: add dark mode toggle to dashboard
- fix: correct mastery calculation for Transfer questions
- docs: update README with deployment instructions

## Pull Requests

- Link the related issue when applicable.
- Describe what changed and why.
- Ensure all tests pass before requesting review.

## Reporting Issues

Open an issue with:

- A clear title.
- Steps to reproduce.
- Expected vs actual behavior.
- Environment details (OS, Python version, browser).
