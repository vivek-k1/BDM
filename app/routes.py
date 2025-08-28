from __future__ import annotations

import json
import os
from typing import Dict, List, Any

from flask import Blueprint, render_template, request, redirect, url_for, flash


bp = Blueprint('main', __name__)


DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions.json')


def load_questions() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict) and 'questions' in data:
        return data['questions']
    if isinstance(data, list):
        return data
    return []


def save_questions(questions: List[Dict[str, Any]]) -> None:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({'questions': questions}, f, ensure_ascii=False, indent=2)


def filter_by_set(questions: List[Dict[str, Any]], set_id: int) -> List[Dict[str, Any]]:
    label = f"Set {set_id}"
    filtered: List[Dict[str, Any]] = []
    for q in questions:
        topic = (q.get('topic') or '').strip()
        if topic.startswith(label):
            filtered.append(q)
    return filtered


@bp.route('/')
def index():
    questions = load_questions()
    return render_template('index.html', questions=questions, title='All Questions')


@bp.route('/set/<int:set_id>')
def list_set(set_id: int):
    questions = load_questions()
    qset = filter_by_set(questions, set_id)
    return render_template('index.html', questions=qset, title=f'Set {set_id} Questions')


@bp.route('/question/<int:q_id>', methods=['GET', 'POST'])
def question(q_id: int):
    questions = load_questions()
    if q_id < 1 or q_id > len(questions):
        flash('Question not found.', 'warning')
        return redirect(url_for('main.index'))
    q = questions[q_id - 1]

    if request.method == 'POST':
        selected = request.form.get('answer')
        correct_answer = q.get('answer')
        is_correct = (selected == correct_answer) if correct_answer else None
        return render_template('result.html', question=q, q_id=q_id, selected=selected, is_correct=is_correct, total_questions=len(questions))

    return render_template('question.html', question=q, q_id=q_id)


@bp.route('/add', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        option_a = request.form.get('option_a', '').strip()
        option_b = request.form.get('option_b', '').strip()
        option_c = request.form.get('option_c', '').strip()
        option_d = request.form.get('option_d', '').strip()
        answer = request.form.get('answer', '').strip().upper()
        topic = request.form.get('topic', '').strip()

        if not text or not option_a or not option_b or not option_c or not option_d or answer not in {'A', 'B', 'C', 'D'}:
            flash('Please fill all fields and choose a valid answer (A/B/C/D).', 'danger')
            return render_template('add.html', form=request.form)

        questions = load_questions()
        new_question = {
            'text': text,
            'options': {
                'A': option_a,
                'B': option_b,
                'C': option_c,
                'D': option_d,
            },
            'answer': answer,
            'topic': topic,
        }
        questions.append(new_question)
        save_questions(questions)
        flash('Question added.', 'success')
        return redirect(url_for('main.index'))

    return render_template('add.html')


@bp.route('/practice', methods=['GET', 'POST'])
def practice_all():
    questions = load_questions()
    results: Dict[int, Dict[str, Any]] = {}
    score = 0
    if request.method == 'POST':
        for idx, q in enumerate(questions, start=1):
            selected = request.form.get(f'ans_{idx}')
            correct_answer = q.get('answer')
            is_correct = (selected == correct_answer) if (selected and correct_answer) else None
            if is_correct is True:
                score += 1
            results[idx] = {
                'selected': selected,
                'is_correct': is_correct,
                'correct': correct_answer,
            }
        return render_template('practice.html', questions=questions, results=results, score=score, total=len(questions), title='Practice All')

    return render_template('practice.html', questions=questions, results=results, score=None, total=len(questions), title='Practice All')


@bp.route('/practice/<int:set_id>', methods=['GET', 'POST'])
def practice_set(set_id: int):
    all_questions = load_questions()
    questions = filter_by_set(all_questions, set_id)
    results: Dict[int, Dict[str, Any]] = {}
    score = 0
    if request.method == 'POST':
        for idx, q in enumerate(questions, start=1):
            selected = request.form.get(f'ans_{idx}')
            correct_answer = q.get('answer')
            is_correct = (selected == correct_answer) if (selected and correct_answer) else None
            if is_correct is True:
                score += 1
            results[idx] = {
                'selected': selected,
                'is_correct': is_correct,
                'correct': correct_answer,
            }
        return render_template('practice.html', questions=questions, results=results, score=score, total=len(questions), title=f'Practice Set {set_id}')

    return render_template('practice.html', questions=questions, results=results, score=None, total=len(questions), title=f'Practice Set {set_id}')


@bp.route('/import', methods=['GET', 'POST'])
def import_questions():
    if request.method == 'POST':
        raw = request.form.get('payload', '').strip()
        if not raw:
            flash('Paste JSON payload.', 'warning')
            return render_template('import.html')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON: {e}', 'danger')
            return render_template('import.html', payload=raw)

        incoming = []
        if isinstance(data, dict) and 'questions' in data and isinstance(data['questions'], list):
            incoming = data['questions']
        elif isinstance(data, list):
            incoming = data
        else:
            flash('JSON must be a list of questions or an object with a questions array.', 'danger')
            return render_template('import.html', payload=raw)

        
        normalized: List[Dict[str, Any]] = []
        for item in incoming:
            if not isinstance(item, dict):
                continue
            text = str(item.get('text', '')).strip()
            options = item.get('options')
            answer = (item.get('answer') or '').strip().upper() or None
            topic = str(item.get('topic', '') or item.get('set', '') or '').strip()
            if not text or not isinstance(options, dict):
                continue
            
            fixed_options: Dict[str, str] = {}
            for key in ['A', 'B', 'C', 'D']:
                val = options.get(key)
                if val is not None:
                    fixed_options[key] = str(val)
            if len(fixed_options) < 2:
                continue
            if answer and answer not in fixed_options:
                # ignore invalid answer
                answer = None
            normalized.append({'text': text, 'options': fixed_options, 'answer': answer, 'topic': topic})

        if not normalized:
            flash('No valid questions found to import.', 'warning')
            return render_template('import.html', payload=raw)

        existing = load_questions()
        total_before = len(existing)
        existing.extend(normalized)
        save_questions(existing)
        flash(f'Imported {len(normalized)} questions. Total is now {len(existing)} (was {total_before}).', 'success')
        return redirect(url_for('main.index'))

    return render_template('import.html')


