import os
from pathlib import Path
from typing import Mapping, Optional

from flask import Flask

from .admin import admin
from .extensions import db, login_manager, migrate
# Load model declarations before Flask-Migrate reads SQLAlchemy metadata.
from . import models  # pyright: ignore[reportUnusedImport]
from .routes import main


@login_manager.user_loader
def load_admin_user(user_id: str) -> models.AdminUser | None:
    try:
        admin_id = int(user_id)
    except ValueError:
        return None
    return db.session.get(models.AdminUser, admin_id)


def create_app(test_config: Optional[Mapping[str, object]] = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("mysql://"):
        database_url = "mysql+pymysql://" + database_url[len("mysql://") :]
    if not database_url:
        database_path = Path(app.instance_path) / "zenblog.sqlite"
        database_url = "sqlite:///" + database_path.as_posix()

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(main)
    # Add authentication and authorization checks here before enabling administrative writes.
    app.register_blueprint(admin)
    return app
