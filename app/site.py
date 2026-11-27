from .extensions import db
from .models import SiteSettings

DEFAULT_SITE_SETTINGS = {
    "site_name": "Emprego Angola",
    "tagline": "Carreira e oportunidades",
    "about_text": "Um portal independente de informação, emprego e orientação profissional para Angola.",
    "hero_title": "O seu caminho profissional começa com informação.",
    "hero_description": "Vagas, orientação e ferramentas úteis para procurar emprego e construir carreira em Angola.",
    "hero_image_url": "/static/img/imagem_index.jpg",
    "contact_email": "josemanuelmiguel070@gmail.com",
    "contact_whatsapp": "+244 939 815 394",
    "footer_note": "Todos os direitos reservados.",
    "language": "Português",
}


def get_site_settings():
    return db.session.get(SiteSettings, 1) or SiteSettings(id=1, **DEFAULT_SITE_SETTINGS)
