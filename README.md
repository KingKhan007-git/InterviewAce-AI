# ⚡ InterviewAce AI - Mock Interview Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.org/)
[![Google Gemini API](https://img.shields.io/badge/Google%20Gemini-API-orange.svg)](https://aistudio.google.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](#)

**InterviewAce AI** is a production-ready, full-stack AI-powered Mock Interview Platform built with Python, Flask, SQLite, HTML5, CSS3, JavaScript, PyPDF, and the Google Gemini API (`google-genai`).

It empowers software developers and job applicants to practice technical and HR interviews with dynamic AI questions, speech-to-text dictation, resume PDF parsing, real-time feedback out of 100, strengths/weaknesses breakdown, and performance analytics.

---

## ✨ Features & Highlights

- **🔒 Authentication & Security**:
  - User Registration, Password Hashing (`Werkzeug`), Login, Logout, Session Persistence.
- **📊 Candidate Performance Dashboard**:
  - Overall average score KPI, practice streak, readiness status.
  - Interactive **Chart.js** analytics (Score history progression & Average score breakdown by role).
- **🎯 Dynamic AI Interview Module**:
  - Target Role Selection (Java Developer, Python Developer, Web Developer, HR & Behavioral).
  - Difficulty Levels (Easy, Medium, Hard).
  - Dynamic AI Question Generation powered by **Google Gemini API**.
- **📄 Resume PDF Parsing**:
  - Drag-and-Drop PDF resume upload zone.
  - `pypdf` text extraction engine.
  - Gemini AI extracts key candidate skills and projects to build custom targeted interview questions.
- **🎙️ Voice Speech-to-Text Dictation**:
  - Web Speech API integration allows candidates to dictate technical answers aloud via microphone.
- **🏆 Comprehensive AI Evaluation Report**:
  - Score out of 100 with radial gauge visualization.
  - Bulleted Strengths and Areas for Growth (Weaknesses).
  - Question-by-question breakdown, candidate answers, individual scores, actionable tips, and benchmark ideal answers.
- **🎨 Glassmorphism & Responsive UI**:
  - Modern dark/light theme toggle with `localStorage` persistence.
  - Ambient glowing gradients, glass cards, loading spinners, and toast popups.
- **🔑 Out-of-the-box Fallback Mode**:
  - Includes a fallback mock engine so the app is 100% testable out-of-the-box even before adding a Gemini API key.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-SQLAlchemy, Werkzeug
- **Frontend**: HTML5, CSS3 (Vanilla CSS Glassmorphism Design System), JavaScript (ES6+), Chart.js
- **Database**: SQLite
- **AI & ML Service**: Google Gemini API (`google-genai` / `google-generativeai`)
- **PDF Extraction**: `pypdf` / `PyPDF2`

---

## 📁 Folder Structure

```text
c:\INTERVIEWACEAI\
├── app.py                      # Flask main app factory & API routes
├── models.py                   # SQLAlchemy database schemas (User, Interview, Question)
├── test_app.py                 # Automated unit tests for authentication & interview flow
├── services/
│   ├── __init__.py
│   ├── gemini_service.py       # Gemini API integration & simulated fallback evaluator
│   └── pdf_service.py          # PDF resume text extraction service
├── templates/
│   ├── base.html               # Base Jinja layout, navbar, dark/light theme, toast alerts
│   ├── index.html              # Landing page
│   ├── auth/
│   │   ├── login.html          # Login view
│   │   └── register.html       # Candidate registration view
│   ├── dashboard.html          # Dashboard with Chart.js analytics
│   ├── interview/
│   │   ├── setup.html          # Role selection & drag-and-drop PDF resume upload
│   │   ├── session.html        # Interactive interview room with timer & speech-to-text
│   │   └── report.html         # Score breakdown, strengths/weaknesses & model answers
│   └── history.html            # Complete interview history table
├── static/
│   ├── css/
│   │   └── styles.css          # Glassmorphism design system & CSS variables
│   └── js/
│       ├── theme.js            # Light/Dark mode switcher
│       ├── dashboard.js        # Chart.js analytics charts
│       └── interview.js        # Question navigation wizard, timer & voice input
├── uploads/                    # Temporary PDF resume uploads directory
├── instance/                   # SQLite database storage (interviewace.db)
├── .env.example                # Sample environment variables file
├── requirements.txt            # Python dependencies
└── README.md                   # Setup guide & platform documentation
```

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Clone / Open Directory
```bash
cd c:\INTERVIEWACEAI
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your `SECRET_KEY` and optional `GEMINI_API_KEY`:
```env
SECRET_KEY=interviewace_super_secret_key_2026
GEMINI_API_KEY=your_google_gemini_api_key
```

> 💡 **Note**: If `GEMINI_API_KEY` is left blank, the application will automatically run in **Simulated AI Fallback Mode**, allowing full testing! You can also set your API key anytime via the 🔑 button in the navbar.

### 5. Run Automated Unit Tests
```bash
python test_app.py
```

### 6. Start the Flask Development Server
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🎯 Usage Guide

1. **Register & Login**:
   - Create a candidate account on `/register` and login to access your personal dashboard.
2. **Start a Role-Based Mock Interview**:
   - Navigate to **New Interview**, select your target role (Java Developer, Python Developer, Web Developer, HR) and difficulty (Easy, Medium, Hard).
3. **Start a Resume-Based Mock Interview**:
   - Click the **Resume-Based Setup** tab, upload your PDF resume, and click **Analyze Resume**.
4. **Take the Interview**:
   - Use text input or click 🎙️ **Dictate Answer** to speak your response aloud.
   - Navigate questions and click **Submit & Evaluate Interview**.
5. **Review AI Scorecard**:
   - View your overall score out of 100, bulleted strengths/weaknesses, AI feedback, and ideal model answers.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
