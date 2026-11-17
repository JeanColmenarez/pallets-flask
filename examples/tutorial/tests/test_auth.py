import pytest
from flask import g
from flask import session

from flaskr.db import get_db


def test_register(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/auth/register").status_code == 200

    # test that successful registration redirects to the login page
    response = client.post(
        "/auth/register", data={"username": "a", "password": "abcdefgh"}
    )
    assert response.headers["Location"] == "/auth/login"

    # test that the user was inserted into the database
    with app.app_context():
        assert (
            get_db().execute("SELECT * FROM user WHERE username = 'a'").fetchone()
            is not None
        )


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required."),
        ("a", "", b"Password is required."),
        ("test", "test1234", b"already registered"),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )
    assert message in response.data


def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert client.get("/auth/login").status_code == 200

    # test that successful login redirects to the index page
    response = auth.login()
    assert response.headers["Location"] == "/"

    # login request set the user_id in the session
    # check that the user is loaded from the session
    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["username"] == "test"


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (("a", "test", b"Incorrect username."), ("test", "a", b"Incorrect password.")),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "user_id" not in session




@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("user_7", "abcdefg"),  # 7 caracteres: al limite de la validación
    ),
)
def test_register_password_too_short(client, app, username, password):
    # Enviamos el formulario de registro con una contraseña demasiado corta
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )

    # La app debe mostrar el mensaje de error del R2
    assert b"Password must be at least 8 characters long." in response.data

    # Y NO debe haber creado el usuario en la base de datos
    with app.app_context():
        user = (
            get_db()
            .execute("SELECT * FROM user WHERE username = ?", (username,))
            .fetchone()
        )
        assert user is None


@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("user_8", "abcdefgh"),  # 8 caracteres: justo en el límite
        ("user_9", "abcdefghi"),  # 9 caracteres: justo por encima
    ),
)
def test_register_password_valid_length(client, app, username, password):
    # Enviamos el formulario con una contraseña de longitud válida
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )

    # Debe redirigir a la página de login
    assert response.headers["Location"] == "/auth/login"

    # Y el usuario debe existir en la base de datos
    with app.app_context():
        user = (
            get_db()
            .execute("SELECT * FROM user WHERE username = ?", (username,))
            .fetchone()
        )
        assert user is not None
       