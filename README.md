# 🚀 CI/CD Academic Learning Platform

An interactive platform for teaching **CI/CD & DevOps** to students — built with Flask, featuring a secure Python sandbox, an embedded VS Code editor, and role-based panels for students, lecturers, and admins .

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/tests-370%20passing-success)

---

## 📖 About

CI/CD and DevOps are usually learned from theory and slides, which makes the actual pipeline feel abstract. **ANTE** turns it into a hands-on experience: instead of just reading about *Code → Build → Test → Deploy*, learners walk through each stage, write and run real Python code in the browser, see a live pipeline simulation, and earn a certificate on completion.

**What it does:** guides students through interactive learning modules, lets them solve quiz and coding exercises in a real VS Code editor (with their code running in a secure sandbox), write their own unit tests, and track progress. Lecturers manage questions and theory content and review student submissions, while admins manage users, settings, and the system.

**Who it's for:**
- **Students** — learning CI/CD & DevOps through practice rather than passive reading.
- **Lecturers** — managing course content and reviewing student work.
- **Admins** — running and overseeing the platform.

---

## ✨ Features

- **Embedded Monaco Editor** — the real VS Code editor in the browser, with Python syntax highlighting and IntelliSense.
- **Animated CI/CD pipeline** — a live *Code → Build → Test → Deploy* simulation with terminal output.
- **Secure Python sandbox** — thread-isolated execution, 2s timeout, memory limits, and blocked dangerous imports.
- **Student unit tests** — students write and run their own tests after solving a challenge.
- **Lecturer code review** — review student submissions and leave feedback.
- **Security hardening** — CSRF tokens, login throttling, session timeout, and an audit log.
- **Completion certificate** — auto-generated PDF for students who pass the threshold.

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + Flask 3.0 |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (default) / MS SQL Server (optional) |
| Frontend | Jinja2 + custom CSS + Monaco Editor |
| Testing | pytest (370 tests) |

---

## ⚙️ Installation & Usage

```bash
git clone <repo-url>
cd ANTE
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt

python run.py                  # then open http://127.0.0.1:5000
```

Seed demo data (optional):
```bash
python scripts/seed_demo.py
```

---

## 🧪 Testing

```bash
python -m pytest -v                          # all 370 tests
python -m pytest --cov=app --cov-report=html # with coverage
```

