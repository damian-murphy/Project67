# Tests for the p67 app
#

import pytest
from projects import app as my_app


@pytest.fixture()
def testapp():
    tapp = my_app
    tapp.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield tapp

    # clean up / reset resources here


@pytest.fixture()
def client(testapp):
    return testapp.test_client()


@pytest.fixture()
def runner(testapp):
    return testapp.test_cli_runner()
