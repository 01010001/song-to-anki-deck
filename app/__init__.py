import os

import logging

from flask import Flask, request

from dotenv import load_dotenv



from app.controllers.main_controller import bp

from app.database import db

from app.logging_config import setup_logging

from app.services import song_repository



logger = logging.getLogger(__name__)





def create_app():

    load_dotenv()

    setup_logging()



    app = Flask(__name__)

    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")



    if os.getenv("TESTING"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_path = os.path.join(base_dir, "data", "app.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



    db.init_app(app)

    with app.app_context():

        from app.models import db_models  # noqa: F401

        db.create_all()



    app.register_blueprint(bp)



    @app.context_processor

    def inject_sidebar():

        try:

            songs = song_repository.list_songs(limit=80)

            history = [s.to_sidebar_dict() for s in songs]

        except Exception:

            history = []

        return dict(history_songs=history)



    @app.before_request

    def log_request_start():

        if request.path.startswith("/api/"):

            logger.debug(">>> %s %s", request.method, request.path)



    @app.after_request

    def log_request_end(response):

        if request.path.startswith("/api/"):

            logger.debug("<<< %s %s -> HTTP %s", request.method, request.path, response.status_code)

        return response



    logger.info("Uygulama hazır (DEBUG=%s)", os.getenv("DEBUG", "true"))

    return app


