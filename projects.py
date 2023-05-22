# The Project File
# (C) Damian Murphy. Original Projects.txt, 1995/1996-2003, previous organisers 1989-1993
#

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
    app = Flask(__name__)

    bp = Blueprint("test", __name__)

    @app.route("/hello")
    def hello_world():
        return "<h1>Hello!</h1>"

    @app.route("/list")
    def list():
        p_file = open("PROJECTS.TXT.data.sql", "r")
        projects = p_file.read()
        print(projects)
        return render_template("display.html.j2", projects=projects)

    return app

# Start me up
if __name__ == '__main__':
    app = start()
    app.run()
