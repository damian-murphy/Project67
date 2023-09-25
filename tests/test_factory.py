from projects import app


def test_config():
    assert not app().testing
    assert app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert response.data == b'Hello!'
