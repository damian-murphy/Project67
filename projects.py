# The Project File
# (C) Damian Murphy. Original Projects.txt, 1995/1996-2003, previous organisers 1989-1993
#
import database
import datetime
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
def dt_from_str(string):
    """ Simple func to return datetime based on string input from html datetime
        Empty values or blank strings are returned as None value """
    if string != '':
        return datetime.datetime.strptime(str(string), "%Y-%m-%dT%H:%M")
    else:
        return None

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
                        where started_on is not NULL and ( done='0' or done is NULL )
                         order by started_on""").fetchall()
        return render_template("index.html.j2", title="Currently Active", projects=projects)

    @app.route("/paused")
    def paused():
        """ Projects that have been stopped but not completed """
        db = database.get_db()
        projects = db.execute("""select number,idea,created,started_on,stopped_on,done from projects 
                        where started_on is not NULL and stopped_on is not NULL 
                        and done is NULL order by started_on""").fetchall()
        return render_template("list.html.j2", title="Paused", projects=projects)

    @app.route("/done")
    def done():
        """ Projects that have been completed """
        db = database.get_db()
        projects = db.execute("""select number,idea,created,started_on,stopped_on,done from projects 
                        where (done is NOT NULL) order by done DESC""").fetchall()
        columns = ("number", "idea", "created", "started_on", "stopped_on", "done")
        return render_template("list.html.j2", title="Completed", projects=projects,
                               columns=columns)

    @app.route("/list")
    def list():
        db = database.get_db()
        projects = db.execute("select number,idea,created,done from projects order by number").fetchall()
        columns = ("number", "idea", "created", "done")
        return render_template("list.html.j2", title="All", projects=projects, columns=columns)

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
                # Remember to convert the datetime parameters into datetime
                # objects in the format we're storing
                db.execute(
                    """UPDATE projects SET idea = ?, memoranda = ?, created = ?, done = ?, 
                    last_modified = ?, started_on = ?, stopped_on = ?, continuous = ?, 
                    links = ? where number = ?;""",
                    (request.form["idea"], request.form["memoranda"],
                     dt_from_str(request.form["created"]),
                     dt_from_str(request.form["done"]), dt_from_str(request.form["last_modified"]),
                     dt_from_str(request.form["started_on"]),
                     dt_from_str(request.form["stopped_on"]), request.form["continuous"],
                     request.form["links"], num)
                )
                db.commit()
                return redirect(url_for("show_project", num=num))

        return render_template("edit.html.j2", title="Editing", project=project,
                        dtnow=datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%dT%H:%M"))

    return app

# Start me up
if __name__ == '__main__':
    app = start()
    app.run()
