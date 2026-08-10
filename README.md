# TANTR

An AI-powered GitHub-like platform that automatically evaluates student code commits and provides professor-style grading and feedback.

The platform allows students to push code, track commit history, and receive automated evaluations based on code quality, algorithm efficiency, documentation, and best practices.

---

## 🚀 Overview

TANTR is a learning platform designed to help students improve their coding skills through continuous commit-based evaluation.

Instead of manually reviewing assignments, the system automatically analyzes code and generates feedback using an AI evaluation engine.

Students receive:

- Commit scores
- Code quality analysis
- Algorithm feedback
- Improvement suggestions
- Progress tracking

This creates an experience similar to having a **personal programming professor reviewing every commit.**

---

## 🧠 Key Features

### Repository Management
- Create repositories
- Upload code
- Track commit history
- View commit diffs

### AI Commit Evaluation
Each commit is automatically evaluated by an AI engine.

The evaluation considers:

- Code correctness
- Algorithm efficiency
- Code readability
- Documentation quality
- Best practices

### Static Code Analysis
Before AI evaluation, the system runs static code analysis tools to extract metrics such as:

- Cyclomatic complexity
- Code style
- Documentation presence
- Error count
- Code duplication

### Student Dashboard
Students can view:

- Repository list
- Commit scores
- AI feedback
- Performance graphs
- Weekly coding progress

### Professor/Admin Dashboard
Admins can:

- Monitor student repositories
- View grading analytics
- Detect plagiarism
- Review evaluation logs

---

## 🏗 System Architecture

```

User
↓
Frontend (Next.js + Tailwind)
↓
Backend API (FastAPI)
↓
Git Repository Service
↓
Static Code Analyzer
↓
AI Professor Engine
↓
Database (PostgreSQL)
↓
Task Queue (Redis + Celery)

```

---

## ⚙️ Tech Stack

### Frontend
- Next.js
- React
- Tailwind CSS
- Monaco Editor

### Backend
- Python FastAPI

### Database
- PostgreSQL

### AI Engine
- LLM (OpenAI / Gemini / Llama)

### Static Analysis
- pylint
- flake8
- radon
- eslint (for JavaScript)

### Task Queue
- Redis
- Celery

### Version Control
- Git

---

## 📂 Project Structure

```

ai-commit-professor/

backend/
main.py
api/
models/
services/
ai_engine/
analyzer/

frontend/
pages/
components/
styles/

database/
schema.sql

docs/
architecture.md

```

---

## 🔄 Commit Evaluation Pipeline

When a student commits code:

1. The commit is stored in the Git repository.
2. A commit diff is generated.
3. Static code analysis tools run.
4. Analysis metrics are collected.
5. The AI professor evaluates the commit.
6. A final score and feedback are generated.
7. Results are stored in the database.
8. The student dashboard displays the results.

---

## 📊 Example Commit Evaluation

Example commit:

```

Added binary search algorithm

```

Evaluation:

```

Code Quality: 8/10
Algorithm Efficiency: 9/10
Documentation: 5/10
Testing: 6/10
Commit Consistency: 7/10

Final Score: 7.6 / 10

```

AI Feedback:

```

Good implementation of binary search with optimal O(log n) complexity.
However, variable naming could be improved and additional comments explaining
the algorithm logic would increase readability.

```

---

## 📈 Grading Formula

Final Score Calculation:

```

Final Score =
30% Code Quality
25% Algorithm Efficiency
20% Documentation
15% Testing
10% Commit Consistency

```

---

## 🛠 Installation

### Clone the repository

```

git clone [https://github.com/yourusername/ai-commit-professor.git](https://github.com/yourusername/ai-commit-professor.git)
cd ai-commit-professor

```

### Backend setup

```

cd backend
pip install -r requirements.txt
uvicorn main:app --reload

```

### Frontend setup

```

cd frontend
npm install
npm run dev

```

### Database setup

Install PostgreSQL and run:

```

psql -U postgres -d ai_commit_professor -f database/schema.sql

```

### Start Redis

```

redis-server

```

### Start Celery worker

```

celery -A worker worker --loglevel=info

```

---

## 🔮 Future Improvements

- AI viva system that questions students about their commits
- Code plagiarism detection
- Difficulty-based grading
- Leaderboards
- Multi-language code support
- Real-time code collaboration

---

## 🎓 Use Cases

- Universities
- Coding bootcamps
- Programming courses
- Self-learning developers

---

## 📜 License

MIT License

---

## 👨‍💻 Author

Sreehari Harshan  
BE Computer Science Engineering  
T John Institute of Technology
```