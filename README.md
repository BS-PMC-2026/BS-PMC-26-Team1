# CI/CD Learning Platform

## Project Name
Interactive Software Development Learning Platform in a Continuous Environment

## Project Overview
This project is an interactive educational web platform designed to help software engineering students learn and practice core CI/CD and DevOps concepts in a simple and practical way.

The system introduces students to topics such as:
- DevOps fundamentals
- Continuous Integration (CI)
- Continuous Delivery / Continuous Deployment (CD)
- Pipelines
- Testing
- Progress tracking

The project is being developed as part of a team project course.

---

## Project Goal
The main goal of this platform is to provide students with a guided environment where they can:
- learn theoretical CI/CD concepts
- explore pipeline stages
- practice exercises
- track their learning progress

---

## Current Sprint Status
This repository currently contains the implementation for **Sprint 1**.

At this stage, the project includes:
- basic Flask project structure
- application routes
- templates and static files
- database models
- seed file
- service layer
- automated tests
- GitHub Actions CI workflow

---

## Main Features Implemented
- User roles support
- Intro and pipeline learning pages
- Exercise-related logic
- Feedback services
- Progress-related services
- Test structure with pytest
- CI validation using GitHub Actions

---

## Technologies Used
- Python
- Flask
- SQLAlchemy
- HTML
- CSS
- Pytest
- GitHub Actions

---

## Repository Structure
```text
.github/workflows/   # GitHub Actions workflow
app/                 # Main application package
app/routes/          # Application routes
app/services/        # Service layer
app/static/          # CSS and static files
app/templates/       # HTML templates
tests/               # Automated tests
requirements.txt     # Project dependencies
app.py               # Application entry point
