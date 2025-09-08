import os
from src.main import create_app


def test_create_app():
    os.environ.setdefault("SECRET_KEY", "testing")
    app = create_app()
    assert app is not None
    with app.app_context():
        pass
