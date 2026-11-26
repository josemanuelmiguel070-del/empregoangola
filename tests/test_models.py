import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import inspect
from sqlalchemy.schema import CreateTable

from app import create_app, load_admin_user
from app.extensions import db
from app.models import (
    AdminUser,
    Category,
    Content,
    CVTemplate,
    PasswordResetToken,
    SiteSettings,
)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "test.sqlite"
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///" + database_path.as_posix(),
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        self.temp_directory.cleanup()

    def test_tables_and_model_relationships(self):
        admin = AdminUser(email="admin@example.com", password_hash="hashed-password")
        token = PasswordResetToken(
            token_hash="hashed-token",
            expires_at=datetime(2030, 1, 1),
        )
        admin.reset_tokens.append(token)

        category = Category(name="Emprego", slug="emprego")
        article = Content(
            content_type="article",
            title="Artigo",
            slug="artigo",
            summary="Resumo",
            body="Conteúdo",
            category=category,
        )
        cv_template = CVTemplate(
            title="CV",
            description="Modelo editável",
            category=category,
            preview_url="/static/img/cv.jpg",
        )
        settings = SiteSettings(site_name="Emprego Angola")
        db.session.add_all([admin, category, article, cv_template, settings])
        db.session.commit()

        self.assertEqual(
            set(inspect(db.engine).get_table_names()),
            {
                "admin_users",
                "categories",
                "content",
                "cv_templates",
                "password_reset_tokens",
                "site_settings",
            },
        )
        self.assertIs(token.user, admin)
        self.assertIs(article.category, category)
        self.assertIs(cv_template.category, category)
        self.assertEqual(category.content_items, [article])
        self.assertEqual(category.cv_templates, [cv_template])
        self.assertEqual(settings.site_name, "Emprego Angola")
        self.assertEqual(admin.get_id(), str(admin.id))
        self.assertIs(load_admin_user(str(admin.id)), admin)
        self.assertIsNone(load_admin_user("invalid-id"))


class DatabaseConfigurationTests(unittest.TestCase):
    def test_default_database_is_sqlite(self):
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            app = create_app({"TESTING": True})

        self.assertTrue(app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"))

    def test_mysql_url_uses_pymysql_dialect_without_connecting(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "mysql://user:password@localhost/zenblog"},
        ):
            app = create_app({"TESTING": True})

        self.assertEqual(
            app.config["SQLALCHEMY_DATABASE_URI"],
            "mysql+pymysql://user:password@localhost/zenblog",
        )
        with app.app_context():
            engine = db.engine
            self.assertEqual(engine.dialect.name, "mysql")
            for model in (
                AdminUser,
                Category,
                Content,
                CVTemplate,
                PasswordResetToken,
                SiteSettings,
            ):
                ddl = str(CreateTable(model.__table__).compile(dialect=engine.dialect))
                self.assertIn("CREATE TABLE", ddl)
            engine.dispose()
