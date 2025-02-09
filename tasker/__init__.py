import os

from flask import Flask, redirect, url_for


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'tasker_data.sqlite3')
    )

    # Register stuff
    from tasker import db
    db.init_app(app)

    from tasker import task
    app.register_blueprint(task.bp)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def hello():
        return redirect(url_for('tasks.tasks'))

    _ = hello  # Supress not used

    return app
