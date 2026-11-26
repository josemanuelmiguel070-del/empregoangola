from pathlib import Path
from typing import Mapping, Optional

from flask import Flask

from .routes import main


def create_app(test_config: Optional[Mapping[str, object]] = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    if test_config is not None:
        app.config.update(test_config)

    app.register_blueprint(main)
    return app
