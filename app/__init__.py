import os
from pathlib import Path
from typing import Mapping, Optional

import click
from flask import Flask

from .admin import admin
from .auth import auth
from .extensions import csrf, db, login_manager, migrate
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

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key and not (test_config and test_config.get("TESTING")):
        raise RuntimeError("Set SECRET_KEY in the environment before starting the application.")

    app.config.from_mapping(
        SECRET_KEY=secret_key or "test-only-secret-key",
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true",
    )
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(email: str, password: str) -> None:
        """Create the first administrative account."""
        normalized_email = email.strip().lower()
        if "@" not in normalized_email:
            raise click.BadParameter("Enter a valid email address.", param_hint="--email")
        if len(password) < 12:
            raise click.BadParameter("Password must contain at least 12 characters.")
        if db.session.query(models.AdminUser).filter_by(email=normalized_email).first():
            raise click.ClickException("An administrator with this email already exists.")

        user = models.AdminUser(email=normalized_email, password_hash="")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrator created.")

    return app
