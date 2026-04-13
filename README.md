# Folder 2 — yosi

## Jira Tasks
- **Homepage** — clear and welcoming landing page so students understand the platform
- **User Initialization / Basic Identification** — register and login so progress can be tracked
- **Git Repository Setup** — shared Git repository for team collaboration

## Files in this folder

| File | Description |
|------|-------------|
| `app/templates/home.html` | Homepage / landing page |
| `app/templates/login.html` | Login page |
| `app/templates/register.html` | Registration page |
| `app/routes/main.py` | Route for homepage and start button |
| `app/routes/auth.py` | Routes for login, register, logout |
| `app/models.py` | All database models (User, StudentProfile, etc.) |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Files to exclude from Git |

## Where to place these files in the main project

```
ANTE/
├── app/
│   ├── templates/
│   │   ├── home.html        ← your file
│   │   ├── login.html       ← your file
│   │   └── register.html    ← your file
│   ├── routes/
│   │   ├── main.py          ← your file
│   │   └── auth.py          ← your file
│   └── models.py            ← your file
├── requirements.txt         ← your file
└── .gitignore               ← your file
```

## How to run the full project

```bash
git clone <main-repo-url>
cd ANTE
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
