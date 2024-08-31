""" The Projects File
    A tool to keep track of ideas, projects and so on
    """

# The Project File
# (C) Damian Murphy. Original Projects.txt, 1995/1996-2003, previous organisers 1989-1993
#
import datetime
import operator
from flask import Flask, flash, redirect, render_template, request, url_for
from boto3.dynamodb.conditions import Key, Attr
import database


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

def convert_blank_to_null(test_item):
    """ Convert empty or 'falsy' item to a NULL value for SQLITE3 insertion
    This is to keep things in line with how we're dealing with empty values in
    dynamodb """
    if not test_item:
        return None
    # Otherwise...
    return test_item


app = Flask('projects')

# Load the config file
app.config.from_pyfile('projects.cfg')

with app.app_context():
    # Set the DB type into G so we can access from the database functions module
    database.init_app(app)


# bp = Blueprint("test", 'projects')
# Add template filters


@app.template_filter()
def format_datetime(datestring, fmt='standard'):
    """ Display date formatter, for jinja2 template use
    :parameters datestring (a standard date string), fmt (optional) - standard (only one currently)
    """

    if datestring:
        datestring = datetime.datetime.strptime(datestring, "%Y-%m-%dT%H:%M")
        if fmt == 'standard':
            return datetime.datetime.strftime(datestring, "%a, %d %b, %Y, %I:%M %p")
    return "-"

@app.context_processor
def count_processor():
    def get_counts(a_list, index_item):
        for project in a_list:
            Do sortug
            # TODO

        return len(b_list)
    return dict(get_counts=get_counts)


@app.route("/hello")
def hello():
    """ Standard first function, prints Hello! """
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
        projects = db.scan()
        projects = sorted(projects['Items'], key=operator.itemgetter('number'))
    return render_template("index.html.j2", title="Dashboard", projects=projects)

@app.route("/active")
def active():
    """ list of currently active projects """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created,started_on from projects
                            where started_on is not NULL and ( done='0' or done is NULL )
                            order by started_on""").fetchall()
    else:
        projects = db.scan(
            FilterExpression=Attr('started_on').exists() & ~Attr('done').exists()
        )
        projects = sorted(projects['Items'], key=operator.itemgetter('number'))
    columns = ("number", "idea", "created", "started_on")
    return render_template("list.html.j2", title="Active", projects=projects, columns=columns)


@app.route("/paused")
def paused():
    """ Projects that have been stopped but not completed """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created,started_on,stopped_on,done
                        from projects
                        where started_on is not NULL and stopped_on is not NULL 
                        and done is NULL order by started_on""").fetchall()
    else:
        projects = db.scan(
            FilterExpression=Attr('started_on').exists() & Attr('stopped_on').exists()
                             & ~Attr('done').exists()
        )
        projects = sorted(projects['Items'], key=operator.itemgetter('stopped_on'))
    columns = ("number", "idea", "created", "stopped_on")
    return render_template("list.html.j2", title="Paused", projects=projects, columns=columns)


@app.route("/todo")
def todo():
    """ Projects that are not done yet """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created,started_on,stopped_on,done
                        from projects
                        where done is NULL order by number""").fetchall()
    else:
        projects = db.scan(
            FilterExpression=Attr('done').not_exists()
        )
        projects = sorted(projects['Items'], key=operator.itemgetter('number'))
    columns = ("number", "idea", "created", "continuous")
    return render_template("list.html.j2", title="To Do", projects=projects, columns=columns)


@app.route("/done")
def done():
    """ Projects that have been completed """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created,started_on,stopped_on,done
                        from projects
                        where (done is NOT NULL) order by done DESC""").fetchall()
    else:
        projects = db.scan(
            FilterExpression=Attr('done').exists()
        )
        projects = sorted(projects['Items'], key=operator.itemgetter('done'), reverse=True)
    columns = ("number", "idea", "created", "started_on", "stopped_on", "done")
    return render_template("list.html.j2", title="Completed", projects=projects,
                           columns=columns)


@app.route("/list")
def getlist():
    """ Return a rendering of a list of all items """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created,done from projects
                               order by number""").fetchall()
    else:
        projects = db.scan()
        projects = sorted(projects['Items'], key=operator.itemgetter('number'))
    columns = ("number", "idea", "created", "done")
    return render_template("list.html.j2", title="All", projects=projects, columns=columns)


@app.route("/habits")
def gethabits():
    """ Return a rendering of a list of all items marked continuous and not done """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        projects = db.execute("""select number,idea,created from projects
                               where continuous = 1 order by number""").fetchall()
    else:
        projects = db.scan(
            FilterExpression=Attr('continuous').eq(1)
        )
        projects = sorted(projects['Items'], key=operator.itemgetter('number'))
    columns = ("number", "idea", "created", "continuous")
    return render_template("list.html.j2", title="Habits", projects=projects, columns=columns)


@app.route("/project/<num>")
def show_project(num):
    """ Return a rendering of a specific project item """
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
    """ Edit a specific project entry using a rendered form and handle
    updating the relevant datastore with the form input """
    db = database.get_db()
    if app.config["DBTYPE"] == "sqlite3":
        project = db.execute("""select number,idea,created,done,memoranda,last_modified,
                                started_on,stopped_on,continuous,links
                                from projects where number = ?""", (num,)).fetchone()
    else:
        project = db.query(
            KeyConditionExpression=Key('number').eq(int(num)),
            Select='ALL_ATTRIBUTES'
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
            # Remember to convert empty items to NULL for sqlite3
            # For dynamodb, we simply remove or don't add that entry.
            if app.config["DBTYPE"] == "sqlite3":
                db.execute(
                    """UPDATE projects SET idea = ?, memoranda = ?, created = ?, done = ?, 
                    last_modified = ?, started_on = ?, stopped_on = ?, continuous = ?, 
                    links = ? where number = ?;""",
                    (request.form["idea"], request.form["memoranda"],
                     request.form["created"], convert_blank_to_null(request.form["done"]),
                     convert_blank_to_null(request.form["last_modified"]),
                     convert_blank_to_null(request.form["started_on"]),
                     convert_blank_to_null(request.form["stopped_on"]), request.form["continuous"],
                     request.form["links"], num)
                )
                db.commit()
            else:
                # Check for any empty items and don't add them to the key value store
                # Add the number, which is the primary key first, as it's not stored in the
                # form data.
                my_items = {'number': int(num)}
                for key, entry in request.form.items():
                    if entry:
                        my_items[key] = entry
                db.put_item(
                    Item=my_items
                )

            return redirect(url_for("show_project", num=num))

    return render_template("edit.html.j2", title="Editing", project=project,
                           dtnow=datetime.datetime.strftime(datetime.datetime.now(),
                                                            "%Y-%m-%dT%H:%M"))


# Start me up
if __name__ == '__main__':
    # myapp = start()
    app.run()
