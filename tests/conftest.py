# Tests for the p67 app
#

import pytest

import projects
from projects import app


@pytest.fixture()
def testapp():
    tapp = projects.app()
    tapp.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield tapp

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


