import os
import pytest
from app import create_app
from app.database import db


@pytest.fixture
def client():
    os.environ["TESTING"] = "1"
    app = create_app()
    app.config["SECRET_KEY"] = "test-secret"

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()

    os.environ.pop("TESTING", None)
