""" The Projects File
    A tool to keep track of ideas, projects and so on
    """

# The Project File
# (C) Damian Murphy. Original Projects.txt, 1995/1996-2003, previous organisers 1989-1993
#
import datetime
import operator

from flask import Flask, flash, redirect, render_template, request, url_for, g
import database
from boto3.dynamodb.conditions import Key, Attr


# MEMO On Data
#     Project:
#         Number: n
#         Idea: String
#         Added: Date
#         Done: Date
#         Started On: Date # Implies in progress
#         Stopped On: Date
#         Continuous: Neverending idea
#         Links: String
#         Memoranda: Large notes section
#

def dt_from_str(string):
    """ Simple func to return datetime based on string input from html datetime
        Empty values or blank strings are returned as None value """
    if string != '':
        return datetime.datetime.strptime(str(string), "%Y-%m-%dT%H:%M")
    else:
        return None


def get_sort_value(**arglist):
    """ Return value in dict that we're sorting on """
    item = arglist.get('item', None)
    key = arglist.get('key', None)
    return item[key]

def start():
    """ This bit is the main control """
    app = Flask('projects')

    # Load the config file
    app.config.from_pyfile('projects.cfg')

    with app.app_context():
        # Set the DB type into G so we can access from the database functions module
        database.init_app(app)

    # bp = Blueprint("test", 'projects')

    @app.route("/hello")
    def hello():
        return "<h1>Hello!</h1>"

    @app.route("/")
    def home():
        """ Main index page, also show a list of currently active projects for focus """
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            projects = db.execute("""select number,idea,created,started_on from projects
                                where started_on is not NULL and ( done='0' or done is NULL )
                                order by started_on""").fetchall()
        else:
            projects = db.scan(
                FilterExpression=Attr('started_on').exists() & ~Attr('done').exists()
            )
            projects = sorted(projects['Items'], key=operator.attrgetter('number'))
        return render_template("index.html.j2", title="Currently Active", projects=projects)

    @app.route("/paused")
    def paused():
        """ Projects that have been stopped but not completed """
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            projects = db.execute("""select number,idea,created,started_on,stopped_on,done from projects
                            where started_on is not NULL and stopped_on is not NULL 
                            and done is NULL order by started_on""").fetchall()
        else:
            projects = db.scan(
                FilterExpression=Attr('started_on').exists() & Attr('stopped_on').exists()
                                 & ~Attr('done').exists()
            )
            projects = sorted(projects['Items'], key=get_sort_value(key='started_on'))
        return render_template("list.html.j2", title="Paused", projects=projects)

    @app.route("/done")
    def done():
        """ Projects that have been completed """
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            projects = db.execute("""select number,idea,created,started_on,stopped_on,done from projects
                            where (done is NOT NULL) order by done DESC""").fetchall()
        else:
            projects = db.scan(
                FilterExpression=Attr('done').exists()
            )
            projects = sorted(projects['Items'], key=get_sort_value(key='done'))
        columns = ("number", "idea", "created", "started_on", "stopped_on", "done")
        return render_template("list.html.j2", title="Completed", projects=projects,
                               columns=columns)

    @app.route("/list")
    def getlist():
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            projects = db.execute("""select number,idea,created,done from projects
                                   order by number""").fetchall()
        else:
            projects = db.scan()
            projects = sorted(projects['Items'], key=get_sort_value)
        columns = ("number", "idea", "created", "done")
        return render_template("list.html.j2", title="All", projects=projects, columns=columns)

    @app.route("/project/<num>")
    def show_project(num):
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                                 started_on,stopped_on,continuous,links
                                 from projects where number = ?""", (num,)).fetchone()
            return render_template("project.html.j2", title=project['idea'], project=project)
        else:
            project = db.query(
                KeyConditionExpression=Key('number').eq(int(num))
            )
            project = project['Items']
            return render_template("project.html.j2", title=project[0]['idea'], project=project[0])

    @app.route("/project/<num>/edit", methods=("GET", "POST"))
    def edit_project(num):
        db = database.get_db()
        if app.config["DBTYPE"] == "sqlite3":
            project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                                    started_on,stopped_on,continuous,links
                                    from projects where number = ?""", (num,)).fetchone()
        else:
            project = db.query(
                KeyConditionExpression=Key('number').eq(int(num))
            )
            project = project['Items'][0]

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
                if app.config["DBTYPE"] == "sqlite3":
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
                else:
                    db.put_item(
                        Item={
                            'number': int(num),
                            'idea': request.form["idea"],
                            'memoranda': request.form["memoranda"],
                            'created': request.form["created"],
                            'done': request.form["done"],
                            'last_modified': request.form["last_modified"],
                            'started_on': request.form["started_on"],
                            'stopped_on': request.form["stopped_on"],
                            'continuous': request.form["continuous"],
                            'links': request.form["links"]
                        }
                    )

                return redirect(url_for("show_project", num=num))

        return render_template("edit.html.j2", title="Editing", project=project,
                               dtnow=datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M"))

    return app


# Start me up
if __name__ == '__main__':
    myapp = start()
    myapp.run()
