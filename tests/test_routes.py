import unittest

from app import create_app


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
