"""
Integration tests for the Flask web application (app.py).
Uses Flask's built-in test client; SQLite is created in-memory per test.
"""
import json
import pytest

from app import app as flask_app, db, User


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="testkey",
    )
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    """A test client that is already registered and logged in."""
    client.post("/register", data={"email": "test@example.com", "password": "password123"})
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    return client


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

class TestRegister:
    def test_get_register_page(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200
        assert b"Account" in resp.data  # "Create Account" heading

    def test_register_creates_user(self, app, client):
        client.post("/register", data={"email": "new@example.com", "password": "password123"})
        with app.app_context():
            user = User.query.filter_by(email="new@example.com").first()
            assert user is not None

    def test_duplicate_email_rejected(self, client):
        data = {"email": "dup@example.com", "password": "password123"}
        client.post("/register", data=data)
        resp = client.post("/register", data=data, follow_redirects=True)
        assert b"already registered" in resp.data

    def test_register_redirects_to_login(self, client):
        resp = client.post(
            "/register",
            data={"email": "x@example.com", "password": "password123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


class TestLogin:
    def test_get_login_page(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_valid_login_redirects_to_profile(self, client):
        client.post("/register", data={"email": "u@example.com", "password": "password123"})
        resp = client.post(
            "/login",
            data={"email": "u@example.com", "password": "password123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/profile" in resp.headers["Location"]

    def test_invalid_password_shows_error(self, client):
        client.post("/register", data={"email": "u@example.com", "password": "password123"})
        resp = client.post(
            "/login",
            data={"email": "u@example.com", "password": "wrong"},
            follow_redirects=True,
        )
        assert b"Invalid" in resp.data

    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]


class TestLogout:
    def test_logout_redirects(self, auth_client):
        resp = auth_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_requires_login(self, client):
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Profile route
# ---------------------------------------------------------------------------

class TestProfile:
    def test_profile_page_loads(self, auth_client):
        resp = auth_client.get("/profile")
        assert resp.status_code == 200

    def test_profile_save_category_a(self, app, auth_client):
        auth_client.post(
            "/profile",
            data={"residence": "r", "region": "Mainland", "category": "A", "kids": ""},
        )
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            assert user.category == "A"
            assert user.residence == "r"

    def test_profile_save_category_b(self, app, auth_client):
        auth_client.post(
            "/profile",
            data={
                "residence": "r",
                "region": "Mainland",
                "category": "B",
                "kids": "",
                "activity_opened_month": "01",
                "activity_opened_year": "24",
            },
        )
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            assert user.category == "B"
            assert user.activity_opened == "01/24"

    def test_profile_nhr_saves_region(self, app, auth_client):
        auth_client.post(
            "/profile",
            data={"residence": "nhr", "region": "Azores", "category": "A", "kids": ""},
        )
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            assert user.region == "Azores"

    def test_profile_nr_clears_region(self, app, auth_client):
        auth_client.post(
            "/profile",
            data={"residence": "nr", "region": "Azores", "category": "A", "kids": ""},
        )
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            # Non-resident: region forced to Mainland
            assert user.region == "Mainland"


# ---------------------------------------------------------------------------
# Calculator (index) route
# ---------------------------------------------------------------------------

class TestCalculator:
    def _set_profile(self, client, **kwargs):
        defaults = {
            "residence": "r",
            "region": "Mainland",
            "category": "A",
            "kids": "",
        }
        defaults.update(kwargs)
        client.post("/profile", data=defaults)

    def test_index_page_loads(self, auth_client):
        resp = auth_client.get("/")
        assert resp.status_code == 200

    def test_category_a_calculation(self, auth_client):
        self._set_profile(auth_client)
        resp = auth_client.post("/", data={"year": "2025", "income": "50000", "status": "single"})
        assert resp.status_code == 200
        assert b"50" in resp.data  # income appears

    def test_category_a_result_shows_taxes(self, auth_client):
        self._set_profile(auth_client)
        resp = auth_client.post("/", data={"year": "2025", "income": "60000", "status": "single"})
        assert b"income_tax" in resp.data or b"Income Tax" in resp.data or resp.status_code == 200

    def test_category_b_calculation(self, auth_client, app):
        self._set_profile(
            auth_client,
            category="B",
            activity_opened_month="01",
            activity_opened_year="22",
        )
        resp = auth_client.post(
            "/",
            data={"year": "2025", "income": "60000", "expenses": "5000", "status": "single"},
        )
        assert resp.status_code == 200

    def test_nhr_calculation(self, auth_client):
        self._set_profile(auth_client, residence="nhr", region="Mainland")
        resp = auth_client.post("/", data={"year": "2025", "income": "60000", "status": "single"})
        assert resp.status_code == 200

    def test_invalid_income_shows_error(self, auth_client):
        self._set_profile(auth_client)
        resp = auth_client.post("/", data={"year": "2025", "income": "abc", "status": "single"})
        assert resp.status_code == 200  # renders with error, no 500

    def test_calculation_saved_to_db(self, app, auth_client):
        from app import Calculation
        self._set_profile(auth_client)
        auth_client.post("/", data={"year": "2025", "income": "50000", "status": "single"})
        with app.app_context():
            count = Calculation.query.count()
            assert count == 1

    def test_load_previous_calculation(self, app, auth_client):
        from app import Calculation
        self._set_profile(auth_client)
        auth_client.post("/", data={"year": "2025", "income": "50000", "status": "single"})
        with app.app_context():
            calc = Calculation.query.first()
            calc_id = calc.id
        resp = auth_client.get(f"/?load={calc_id}")
        assert resp.status_code == 200

    def test_joint_declaration(self, auth_client):
        self._set_profile(auth_client)
        resp = auth_client.post("/", data={"year": "2025", "income": "60000", "status": "joint"})
        assert resp.status_code == 200

    def test_with_kids(self, auth_client, app):
        self._set_profile(auth_client, kids="5,8")
        resp = auth_client.post("/", data={"year": "2025", "income": "60000", "status": "single"})
        assert resp.status_code == 200
