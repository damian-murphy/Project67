# The Project File
# (C) Damian Murphy. Original Projects.txt, 1995/1996-2003, previous organisers 1989-1993
#
import database

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import os

""" Data
    Project:
        Number: n
        Idea: String
        Added: Date
        Done: Date
        Started On: Date # Implies in progress
        Stopped On: Date
        Continuous: Neverending idea
        Links: String
        Memoranda: Large notes section
        Log: Start/Stop log?
"""

def start():
    """ This bit is the main control """
    app = Flask('projects')

    with app.app_context():
        database.init_app(app)

    bp = Blueprint("test", 'projects')

    @app.route("/hello")
    def hello_world():
        return "<h1>Hello!</h1>"

    @app.route("/")
    def home():
        return "<h1>Welcome to THINGS TO BE DONE!</h1>"

    @app.route("/list")
    def list():
        db = database.get_db()
        projects = db.execute("select number,idea,created,done from projects order by number").fetchall()
        return render_template("list.html.j2", projects=projects)

    @app.route("/project/<num>")
    def show_project(num):
        db = database.get_db()
        project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                             started_on,stopped_on,continuous,links
                             from projects where number = ?""", (num, )).fetchone()
        return render_template("project.html.j2", project=project)

    @app.route("/project/<num>/edit")
    def edit_project(num):
        db = database.get_db()
        project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                                 started_on,stopped_on,continuous,links
                                 from projects where number = ?""", (num,)).fetchone()
        return render_template("edit.html.j2", project=project)

    return app

# Start me up
if __name__ == '__main__':
    app = start()
    app.run()
