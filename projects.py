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
    def hello():
        return "<h1>Hello!</h1>"

    @app.route("/")
    def home():
        """ Main index page, also show a list of currently active projects for focus """
        db = database.get_db()
        projects = db.execute("""select number,idea,created,started_on from projects 
                        where started_on is not NULL and done='0' order by started_on""").fetchall()
        return render_template("index.html.j2", title="Welcome", projects=projects)

    @app.route("/list")
    def list():
        db = database.get_db()
        projects = db.execute("select number,idea,created,done from projects order by number").fetchall()
        return render_template("list.html.j2", title="List", projects=projects)

    @app.route("/project/<num>")
    def show_project(num):
        db = database.get_db()
        project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                             started_on,stopped_on,continuous,links
                             from projects where number = ?""", (num, )).fetchone()
        return render_template("project.html.j2", title=project['idea'], project=project)

    @app.route("/project/<num>/edit", methods=("GET", "POST"))
    def edit_project(num):
        db = database.get_db()
        project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                                 started_on,stopped_on,continuous,links
                                 from projects where number = ?""", (num,)).fetchone()

        if request.method == "POST":

            error = None

            if not request.form["idea"]:
                error = "Idea is required."

            if error is not None:
                flash(error)
            else:
                db = database.get_db()
                db.execute(
                    """UPDATE projects SET idea = ?, memoranda = ?, created = ?, done = ?, 
                    last_modified = ?, started_on = ?, stopped_on = ?, continuous = ?, 
                    links = ? where number = ?;""",
                    (request.form["idea"], request.form["memoranda"], request.form["created"],
                     request.form["done"], request.form["last_modified"],
                     request.form["started_on"],
                     request.form["stopped_on"], request.form["continuous"],
                     request.form["links"], num)
                )
                db.commit()
                return redirect(url_for("show_project", num=num))

        return render_template("edit.html.j2", title="Editing", project=project)

    return app

# Start me up
if __name__ == '__main__':
    app = start()
    app.run()
