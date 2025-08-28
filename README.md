# MCQ Practice (Flask)

Minimal Flask app to practice multiple-choice questions with Bootstrap styling.

## Features
- Home page lists all questions
- Each question has 4 options (A–D)
- Submit an answer and see correctness
- Questions stored in `questions.json`
- Optional route to add new questions

## Setup
1. Create a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python run.py
   ```
4. Open `http://127.0.0.1:5000` in your browser.

## Structure
- `app/__init__.py`: Flask app factory
- `app/routes.py`: Routes and data access helpers
- `app/templates/`: Jinja2 templates
- `app/static/css/styles.css`: Basic styles
- `questions.json`: Question bank
- `run.py`: Entrypoint

## Adding Questions
- Use the UI at `/add`, or
- Edit `questions.json` directly. Format:
```json
{
  "questions": [
    {
      "text": "Question text?",
      "options": {"A": "..", "B": "..", "C": "..", "D": ".."},
      "answer": "A",
      "topic": "Optional tag"
    }
  ]
}
```

## Notes
- This app is for learning/demo purposes and uses a simple JSON file for storage.
- For concurrent edits or multi-user scenarios, use a database.


