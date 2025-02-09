import sqlite3
import click
import flask

from datetime import datetime
from flask import current_app, g


def init_app(app: flask.Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # g.db.row_factory = sqlite3.Row

    return g.db


def close_db(err=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))


@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Database initialized.')


sqlite3.register_converter(
    'timestamp', lambda v: datetime.fromisoformat(v.decode())
)
