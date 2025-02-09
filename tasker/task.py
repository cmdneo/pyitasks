from dataclasses import dataclass
from datetime import datetime

from flask import (Blueprint, flash, g, redirect, abort,
                   render_template, request, session, url_for)
from tasker.db import get_db


bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@dataclass
class Task:
    id_: int
    description: str
    creation_date: str
    due_date: str
    html_state: str

    def __init__(self, row):
        self.id_ = row[0]
        self.description = row[1]
        self.creation_date = row[2].strftime('%Y-%m-%d')
        self.due_date = row[3].strftime('%Y-%m-%d')
        self.html_state = "" if row[4] == 0 else "checked"


@bp.route('/')
def tasks():
    cur = get_db().cursor()
    res = cur.execute(
        'SELECT * FROM tasks ORDER BY created_at')
    rows = list(map(lambda x: Task(x), res.fetchall()))
    print(rows)

    return render_template('task.html', tasks=rows)


@bp.route('/create', methods=('GET', 'POST'))
def create_task():
    if request.method == 'GET':
        return render_template('create.html')

    desc = request.form.get('description')
    due = request.form.get('due_date')
    if desc is None or due is None:
        abort(400)

    try:
        date = tuple(map(int, due.split('/')))
        date = datetime(date[0], date[1], date[2])
    except (ValueError, IndexError):
        abort(400)

    cur = get_db().cursor()
    cur.execute(
        'INSERT INTO tasks (task_text, due_at) VALUES (?, ?)',
        (desc, date.strftime('%Y-%m-%d %H:%M:%S:%s')),
    )
    get_db().commit()

    return redirect(url_for('tasks.tasks'))


@bp.route('/delete', methods=('POST',))
def delete_task():
    id_ = request.form.get('task_id')
    if id_ is None:
        abort(400)

    cur = get_db().cursor()
    cur.execute('DELETE FROM tasks WHERE id = ?', (id_,))
    get_db().commit()

    return redirect(url_for('tasks.tasks'))


@bp.route('/toggle', methods=('POST',))
def toggle_task():
    id_ = request.form.get('task_id', None)
    if id_ is None:
        abort(400)

    cur = get_db().cursor()
    cur.execute(
        'UPDATE tasks SET progress = 1 - progress WHERE id = ?', (id_,))
    get_db().commit()

    return redirect(url_for('tasks.tasks'))
