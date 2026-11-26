import unittest

from app import create_app
from passenger_wsgi import application


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()

    def test_editorial_routes_render_successfully(self):
        routes = (
            "/",
            "/sobre",
            "/vagas",
            "/contacto",
            "/tutoriais",
            "/artigo-exemplo",
        )

        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Emprego Angola", response.data)

    def test_homepage_image_credit_links_to_source(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/img/imagem_index.jpg", response.data)
        self.assertIn(b"Image by pch.vector on Magnific", response.data)
        self.assertIn(b'rel="noopener noreferrer"', response.data)

    def test_vacancies_route_preserves_search_query(self):
        response = self.client.get("/vagas?q=contabilidade")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="contabilidade"', response.data)

    def test_contact_page_has_direct_contacts_and_web3forms(self):
        response = self.client.get("/contacto")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="mailto:josemanuelmiguel070@gmail.com"', response.data)
        self.assertIn(b'href="https://wa.me/244939815394"', response.data)
        self.assertIn(b'action="https://api.web3forms.com/submit" method="POST"', response.data)
        self.assertIn(b'name="access_key"', response.data)

    def test_static_stylesheet_is_served(self):
        response = self.client.get("/static/css/portal.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"--portal-navy", response.data)

    def test_passenger_wsgi_entry_point_serves_the_application(self):
        response = application.test_client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Emprego Angola", response.data)

    def test_admin_routes_render_mock_management_interfaces(self):
        routes = (
            "/admin",
            "/admin/artigos",
            "/admin/artigos/novo",
            "/admin/artigos/1/editar",
            "/admin/tutoriais",
            "/admin/modelos-cv",
            "/admin/categorias",
            "/admin/configuracoes",
        )

        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Modo de demonstra", response.data)

    def test_admin_upload_and_rich_editor_are_visual_only(self):
        articles = self.client.get("/admin/artigos/novo")
        cv_templates = self.client.get("/admin/modelos-cv/novo")

        self.assertIn(b"Editor rico a integrar", articles.data)
        self.assertIn(b'type="file"', cv_templates.data)
        self.assertIn(b"o ficheiro n", cv_templates.data)

    def test_admin_unknown_content_type_returns_not_found(self):
        response = self.client.get("/admin/unknown")

        self.assertEqual(response.status_code, 404)
