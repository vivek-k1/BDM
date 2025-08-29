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


def filter_by_subject(questions: List[Dict[str, Any]], subject: str) -> List[Dict[str, Any]]:
    if subject == 'all':
        return questions
    
    # Default to BDM if no subject specified
    if not subject or subject == 'bdm':
        # All current questions are BDM-related
        return questions
    
    elif subject == 'mad2':
        # Filter for MAD2 questions (you can add MAD2 questions later)
        mad2_questions = []
        for q in questions:
            topic = (q.get('topic') or '').lower()
            if 'mad2' in topic or 'mobile' in topic or 'app' in topic or 'development' in topic:
                mad2_questions.append(q)
        return mad2_questions
    
    return questions


@bp.route('/')
def index():
    questions = load_questions()
    subject = request.args.get('subject', 'bdm')
    filtered_questions = filter_by_subject(questions, subject)
    return render_template('index.html', questions=filtered_questions, title='All Questions')


@bp.route('/set/<int:set_id>')
def list_set(set_id):
    questions = load_questions()
    if set_id == 1:
        set_questions = questions[:23]
        title = "Set 1: Predicted Question Paper"
    elif set_id == 2:
        set_questions = questions[23:46]
        title = "Set 2: Predicted Question Paper"
    else:
        flash('Invalid set number', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('set_list.html', questions=set_questions, set_id=set_id, title=title)


@bp.route('/solve-set/<int:set_id>', methods=['GET', 'POST'])
def solve_set(set_id):
    questions = load_questions()
    
    if set_id == 1:
        set_questions = questions[:23]
        title = "Set 1: Predicted Question Paper"
        time_limit = 45  # minutes
    elif set_id == 2:
        set_questions = questions[23:46]
        title = "Set 2: Predicted Question Paper"
        time_limit = 45  # minutes
    else:
        flash('Invalid set number', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        score = 0
        results = {}
        
        for idx, q in enumerate(set_questions, start=1):
            selected = request.form.get(f'ans_{idx}')
            correct_answer = q.get('answer')
            is_correct = (selected == correct_answer) if (selected and correct_answer) else False
            
            if is_correct:
                score += 1
            
            results[idx] = {
                'selected': selected,
                'is_correct': is_correct,
                'correct': correct_answer,
            }
        
        return render_template('set_result.html', 
                             questions=set_questions, 
                             results=results, 
                             score=score, 
                             total=len(set_questions), 
                             set_id=set_id,
                             title=title)
    
    return render_template('solve_set.html', 
                         questions=set_questions, 
                         set_id=set_id,
                         title=title,
                         time_limit=time_limit)


@bp.route('/practice-set/<int:set_id>')
def practice_set(set_id):
    questions = load_questions()
    if set_id == 1:
        set_questions = questions[:23]
        title = "Practice Set 1"
    elif set_id == 2:
        set_questions = questions[23:46]
        title = "Practice Set 2"
    else:
        flash('Invalid set number', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('practice.html', 
                         questions=set_questions,
                         title=title,
                         total=len(set_questions))


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
        subject = request.form.get('subject', 'bdm').strip()

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
            'subject': subject,
        }
        questions.append(new_question)
        save_questions(questions)
        flash('Question added.', 'success')
        return redirect(url_for('main.index'))

    return render_template('add.html')


@bp.route('/practice', methods=['GET', 'POST'])
def practice_all():
    questions = load_questions()
    subject = request.args.get('subject', 'bdm')
    
    # Filter questions by subject
    if subject == 'bdm':
        questions = [q for q in questions if (q.get('subject') or 'bdm') == 'bdm']
    elif subject == 'mad2':
        questions = [q for q in questions if q.get('subject') == 'mad2']
    elif subject == 'all':
        pass  # Show all questions
    else:
        questions = [q for q in questions if (q.get('subject') or 'bdm') == 'bdm']
    
    results: Dict[int, Dict[str, Any]] = {}
    current_question = 1
    
    # Get current question from session or request
    if request.method == 'GET':
        current_question = int(request.args.get('q', 1))
    elif request.method == 'POST':
        current_question = int(request.form.get('question_number', 1))
        action = request.form.get('action', 'submit')
        
        if action == 'submit':
            # Handle answer submission
            selected = request.form.get('answer')
            if selected and 1 <= current_question <= len(questions):
                q = questions[current_question - 1]
                correct_answer = q.get('answer')
                is_correct = (selected == correct_answer) if correct_answer else None
                
                results[current_question] = {
                    'selected_answer': selected,
                    'is_correct': is_correct,
                    'correct': correct_answer,
                }
        
        elif action == 'next':
            current_question = min(current_question + 1, len(questions))
        elif action == 'previous':
            current_question = max(current_question - 1, 1)
        elif action == 'finish':
            flash('Practice session completed!', 'success')
            return redirect(url_for('main.index'))
    
    # Calculate statistics
    answered_questions = len([r for r in results.values() if r.get('selected_answer')])
    correct_answers = len([r for r in results.values() if r.get('is_correct')])
    incorrect_answers = answered_questions - correct_answers
    correct_percentage = (correct_answers / answered_questions * 100) if answered_questions > 0 else 0
    
    title = 'Practice All'
    if subject == 'bdm':
        title = 'Practice BDM Questions'
    elif subject == 'mad2':
        title = 'Practice MAD2 Questions'
    elif subject == 'all':
        title = 'Practice All Questions'
    
    return render_template('practice.html', 
                         questions=questions, 
                         results=results, 
                         current_question=current_question,
                         total=len(questions), 
                         title=title,
                         answered_questions=answered_questions,
                         correct_answers=correct_answers,
                         incorrect_answers=incorrect_answers,
                         correct_percentage=correct_percentage)


@bp.route('/practice/<subject>', methods=['GET', 'POST'])
def practice_subject(subject):
    questions = load_questions()
    
    # Filter questions by subject
    if subject == 'bdm':
        questions = [q for q in questions if (q.get('subject') or 'bdm') == 'bdm']
    elif subject == 'mad2':
        questions = [q for q in questions if q.get('subject') == 'mad2']
    elif subject == 'all':
        pass  # Show all questions
    else:
        questions = [q for q in questions if (q.get('subject') or 'bdm') == 'bdm']
    
    results: Dict[int, Dict[str, Any]] = {}
    current_question = 1
    
    # Get current question from session or request
    if request.method == 'GET':
        current_question = int(request.args.get('q', 1))
    elif request.method == 'POST':
        current_question = int(request.form.get('question_number', 1))
        action = request.form.get('action', 'submit')
        
        if action == 'submit':
            # Handle answer submission
            selected = request.form.get('answer')
            if selected and 1 <= current_question <= len(questions):
                q = questions[current_question - 1]
                correct_answer = q.get('answer')
                is_correct = (selected == correct_answer) if correct_answer else None
                
                results[current_question] = {
                    'selected_answer': selected,
                    'is_correct': is_correct,
                    'correct': correct_answer,
                }
        
        elif action == 'next':
            current_question = min(current_question + 1, len(questions))
        elif action == 'previous':
            current_question = max(current_question - 1, 1)
        elif action == 'finish':
            flash('Practice session completed!', 'success')
            return redirect(url_for('main.index'))
    
    # Calculate statistics
    answered_questions = len([r for r in results.values() if r.get('selected_answer')])
    correct_answers = len([r for r in results.values() if r.get('is_correct')])
    incorrect_answers = answered_questions - correct_answers
    correct_percentage = (correct_answers / answered_questions * 100) if answered_questions > 0 else 0
    
    title = 'Practice All'
    if subject == 'bdm':
        title = 'Practice BDM Questions'
    elif subject == 'mad2':
        title = 'Practice MAD2 Questions'
    elif subject == 'all':
        title = 'Practice All Questions'
    
    return render_template('practice.html', 
                         questions=questions, 
                         results=results, 
                         current_question=current_question,
                         total=len(questions), 
                         title=title,
                         answered_questions=answered_questions,
                         correct_answers=correct_answers,
                         incorrect_answers=incorrect_answers,
                         correct_percentage=correct_percentage)


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
            subject = str(item.get('subject', 'bdm') or 'bdm').strip()
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
            normalized.append({'text': text, 'options': fixed_options, 'answer': answer, 'topic': topic, 'subject': subject})

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


