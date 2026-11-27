import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import AdminUser, Category, Content, CVTemplate, Job, SiteSettings
from werkzeug.security import generate_password_hash

with patch.dict(os.environ, {"SECRET_KEY": "test-passenger-secret"}):
    from passenger_wsgi import application


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(cls.temp_directory.name) / "routes.sqlite"
        cls.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///" + database_path.as_posix(),
            }
        )
        cls.password_hash = generate_password_hash(
            "a-secure-password-123",
            method="pbkdf2:sha256",
        )

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()
        cls.temp_directory.cleanup()

    def setUp(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            administrator = AdminUser(
                email="admin@example.com",
                password_hash=self.password_hash,
            )
            db.session.add(administrator)
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        return self.client.post(
            "/admin/login",
            data={"email": "admin@example.com", "password": "a-secure-password-123"},
        )

    def create_category(self, name="Emprego"):
        response = self.client.post(
            "/admin/categorias/novo",
            data={"name": name, "slug": "", "description": "Oportunidades profissionais"},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            return Category.query.filter_by(name=name).one().id

    def test_public_routes_render_with_empty_real_content(self):
        for route in ("/", "/sobre", "/vagas", "/contacto", "/tutoriais"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Emprego Angola", response.data)
        homepage = self.client.get("/")
        self.assertIn("Não existem vagas publicadas".encode(), homepage.data)
        self.assertNotIn(b"Assistente administrativo", homepage.data)

    def test_static_stylesheet_is_served(self):
        response = self.client.get("/static/css/portal.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"--portal-navy", response.data)
        response.close()

    def test_passenger_wsgi_entry_point_serves_application(self):
        response = application.test_client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Emprego Angola", response.data)

    def test_admin_requires_login_and_invalid_login_fails(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])
        self.assertEqual(self.client.get("/admin/login").status_code, 200)

        failed_login = self.client.post(
            "/admin/login",
            data={"email": "admin@example.com", "password": "incorrect"},
        )
        self.assertEqual(failed_login.status_code, 200)
        self.assertIn("inválidos".encode(), failed_login.data)

        blocked_write = self.client.post("/admin/artigos/novo", data={})
        self.assertEqual(blocked_write.status_code, 302)

    def test_article_crud_persists_and_only_published_content_is_public(self):
        self.login()
        category_id = self.create_category()
        create_response = self.client.post(
            "/admin/artigos/novo",
            data={
                "title": "Oportunidade real",
                "slug": "",
                "category_id": str(category_id),
                "featured_image_url": "",
                "summary": "Resumo editorial",
                "body": "Conteúdo publicado",
                "status": "published",
            },
        )
        self.assertEqual(create_response.status_code, 302)
        with self.app.app_context():
            article = Content.query.one()
            article_id = article.id
            article_slug = article.slug
        self.assertEqual(article_slug, "oportunidade-real")
        self.assertIn(b"Oportunidade real", self.client.get("/").data)
        self.assertIn(b"Oportunidade real", self.client.get("/vagas").data)
        self.assertIn("Conteúdo publicado".encode(), self.client.get(f"/artigos/{article_slug}").data)

        edit_response = self.client.post(
            f"/admin/artigos/{article_id}/editar",
            data={
                "title": "Oportunidade actualizada",
                "slug": "",
                "category_id": str(category_id),
                "featured_image_url": "",
                "summary": "Resumo actualizado",
                "body": "Texto actualizado",
                "status": "draft",
            },
        )
        self.assertEqual(edit_response.status_code, 302)
        with self.app.app_context():
            article = db.session.get(Content, article_id)
            self.assertEqual(article.title, "Oportunidade actualizada")
        self.assertNotIn(b"Oportunidade actualizada", self.client.get("/").data)
        self.assertEqual(self.client.get("/artigos/oportunidade-actualizada").status_code, 404)

        delete_response = self.client.post(f"/admin/artigos/{article_id}/apagar")
        self.assertEqual(delete_response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(Content.query.count(), 0)

    def test_categories_cannot_be_deleted_while_in_use(self):
        self.login()
        category_id = self.create_category()
        with self.app.app_context():
            article = Content(
                content_type="article",
                title="Artigo",
                slug="artigo",
                category_id=category_id,
                summary="Resumo",
                body="Corpo",
            )
            db.session.add(article)
            db.session.commit()

        response = self.client.post(f"/admin/categorias/{category_id}/apagar")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Category, category_id))

    def test_jobs_are_managed_and_searchable_in_public_listing(self):
        self.login()
        response = self.client.post(
            "/admin/vagas/novo",
            data={
                "title": "Técnico de redes",
                "company": "Empresa Angola",
                "location": "Luanda",
                "employment_type": "Tempo inteiro",
                "deadline": "",
                "application_url": "https://example.com/apply",
                "description": "Experiência em redes.",
                "status": "published",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            job_id = Job.query.one().id
        public = self.client.get("/vagas?q=redes")
        self.assertIn(b"T\xc3\xa9cnico de redes", public.data)
        self.assertIn(b"Empresa Angola", public.data)

        self.client.post(f"/admin/vagas/{job_id}/apagar")
        with self.app.app_context():
            self.assertEqual(Job.query.count(), 0)
        self.assertNotIn(b"T\xc3\xa9cnico de redes", self.client.get("/vagas").data)

    def test_cv_template_upload_is_persisted_downloadable_and_public_only(self):
        self.login()
        category_id = self.create_category("Currículos")
        response = self.client.post(
            "/admin/modelos-cv/novo",
            data={
                "title": "CV base",
                "description": "Modelo editável",
                "category_id": str(category_id),
                "preview_url": "",
                "status": "published",
                "file": (io.BytesIO(b"%PDF-1.4 test"), "cv.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            template_id = CVTemplate.query.one().id
        self.assertIn(b"CV base", self.client.get("/sobre").data)
        download = self.client.get(f"/modelos-cv/{template_id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"%PDF-1.4 test")
        download.close()

        self.client.post(f"/admin/modelos-cv/{template_id}/apagar")
        with self.app.app_context():
            self.assertEqual(CVTemplate.query.count(), 0)

    def test_settings_are_saved_and_used_by_public_templates(self):
        self.login()
        response = self.client.post(
            "/admin/configuracoes",
            data={
                "site_name": "Portal Actualizado",
                "tagline": "Novas oportunidades",
                "about_text": "Informação profissional.",
                "hero_title": "Encontre o próximo passo",
                "hero_description": "Conteúdo actualizado.",
                "hero_image_url": "/static/img/imagem_index.jpg",
                "contact_email": "contacto@example.com",
                "contact_whatsapp": "+244 900 000 000",
                "footer_note": "Direitos reservados.",
                "language": "Português",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(SiteSettings, 1).site_name, "Portal Actualizado")
        self.assertIn(b"Portal Actualizado", self.client.get("/").data)
        self.assertIn(b"contacto@example.com", self.client.get("/contacto").data)

    def test_invalid_slug_and_url_inputs_are_reported_without_persistence(self):
        self.login()
        category_id = self.create_category()
        response = self.client.post(
            "/admin/artigos/novo",
            data={
                "title": "Artigo inválido",
                "slug": "",
                "category_id": str(category_id),
                "featured_image_url": "javascript:alert(1)",
                "summary": "Resumo",
                "body": "Conteúdo",
                "status": "published",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"URL HTTPS/HTTP", response.data)
        with self.app.app_context():
            self.assertEqual(Content.query.count(), 0)

    def test_unknown_admin_content_type_returns_not_found_after_login(self):
        self.login()

        response = self.client.get("/admin/unknown")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
