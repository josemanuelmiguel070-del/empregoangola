from copy import deepcopy

from flask import Blueprint, abort, render_template

admin = Blueprint("admin", __name__, url_prefix="/admin")

# Replace these in-memory examples with repository/API reads when persistence is added.
MOCK_CATEGORIES = [
    {"id": 1, "name": "Carreira", "slug": "carreira", "count": 8, "description": "Orientação e desenvolvimento profissional."},
    {"id": 2, "name": "Emprego", "slug": "emprego", "count": 12, "description": "Procura de emprego e candidaturas."},
    {"id": 3, "name": "Currículos", "slug": "curriculos", "count": 5, "description": "Modelos e conselhos para CV."},
    {"id": 4, "name": "Entrevistas", "slug": "entrevistas", "count": 4, "description": "Preparação para entrevistas."},
]

MOCK_CONTENT = {
    "artigos": [
        {"id": 1, "title": "Como avaliar uma oportunidade de emprego", "category": "Emprego", "status": "Publicado", "updated": "26 nov 2026", "image": "/static/img/post-landscape-5.jpg", "excerpt": "Critérios práticos para analisar uma oportunidade antes de se candidatar.", "content": "Confirme a origem do anúncio, reveja os requisitos e prepare a candidatura."},
        {"id": 2, "title": "Um currículo claro e fácil de actualizar", "category": "Currículos", "status": "Rascunho", "updated": "24 nov 2026", "image": "/static/img/post-landscape-4.jpg", "excerpt": "Uma estrutura simples ajuda a destacar as competências relevantes.", "content": "Organize a informação por secções e adapte o documento a cada oportunidade."},
        {"id": 3, "title": "Planear os próximos passos da carreira", "category": "Carreira", "status": "Publicado", "updated": "20 nov 2026", "image": "/static/img/post-landscape-3.jpg", "excerpt": "Transforme os seus objectivos profissionais em acções concretas.", "content": "Defina objectivos, identifique competências e reveja o seu progresso."},
    ],
    "tutoriais": [
        {"id": 1, "title": "Preparar uma candidatura online", "category": "Emprego", "status": "Publicado", "updated": "25 nov 2026", "description": "Organize documentos, reveja os dados e confirme cada etapa.", "image": "/static/img/post-landscape-2.jpg", "content": "Confirme a origem do anúncio antes de partilhar qualquer documento."},
        {"id": 2, "title": "Preparar-se para uma entrevista", "category": "Entrevistas", "status": "Rascunho", "updated": "22 nov 2026", "description": "Uma lista de verificação para chegar preparado à entrevista.", "image": "/static/img/post-landscape-3.jpg", "content": "Pesquise a função e prepare exemplos concretos da sua experiência."},
    ],
    "modelos-cv": [
        {"id": 1, "title": "Currículo simples", "category": "Currículos", "status": "Publicado", "updated": "18 nov 2026", "description": "Modelo editável de uma página para candidaturas gerais.", "preview": "/static/downloads/modelo-cv-base.html", "file": "modelo-cv-base.html"},
        {"id": 2, "title": "Currículo profissional", "category": "Currículos", "status": "Em revisão", "updated": "16 nov 2026", "description": "Estrutura para destacar experiência e competências.", "preview": "/static/img/post-landscape-4.jpg", "file": "curriculo-profissional.docx"},
    ],
    "categorias": deepcopy(MOCK_CATEGORIES),
}

CATEGORY_OPTIONS = ["Carreira", "Emprego", "Currículos", "Entrevistas", "Notícias"]

CONTENT_TYPES = {
    "artigos": {
        "title": "Artigos e blog",
        "eyebrow": "Publicações",
        "description": "Gira artigos, notícias e outros conteúdos editoriais do portal.",
        "icon": "bi-journal-richtext",
        "new_label": "Novo artigo",
        "columns": [
            {"key": "title", "label": "Título"},
            {"key": "category", "label": "Categoria"},
            {"key": "status", "label": "Estado"},
            {"key": "updated", "label": "Actualizado"},
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True, "placeholder": "Título do artigo"},
            {"name": "category", "label": "Categoria", "type": "select", "required": True},
            {"name": "image", "label": "Imagem de destaque", "type": "url", "placeholder": "https://... ou caminho da imagem"},
            {"name": "excerpt", "label": "Resumo", "type": "textarea", "required": True, "rows": 3, "placeholder": "Resumo que aparece nas listagens"},
            {"name": "content", "label": "Conteúdo", "type": "editor", "required": True, "rows": 8, "placeholder": "Escreva o conteúdo do artigo..."},
        ],
    },
    "tutoriais": {
        "title": "Tutoriais",
        "eyebrow": "Conteúdo educativo",
        "description": "Organize guias, passos práticos e recursos de aprendizagem.",
        "icon": "bi-lightbulb",
        "new_label": "Novo tutorial",
        "columns": [
            {"key": "title", "label": "Título"},
            {"key": "category", "label": "Categoria"},
            {"key": "status", "label": "Estado"},
            {"key": "updated", "label": "Actualizado"},
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True, "placeholder": "Título do tutorial"},
            {"name": "description", "label": "Descrição", "type": "textarea", "required": True, "rows": 3, "placeholder": "Breve descrição do tutorial"},
            {"name": "category", "label": "Categoria", "type": "select", "required": True},
            {"name": "image", "label": "Imagem", "type": "url", "placeholder": "https://... ou caminho da imagem"},
            {"name": "content", "label": "Conteúdo", "type": "editor", "required": True, "rows": 8, "placeholder": "Escreva os passos e orientações..."},
        ],
    },
    "modelos-cv": {
        "title": "Modelos de CV",
        "eyebrow": "Recursos para download",
        "description": "Gira modelos, pré-visualizações e ficheiros disponibilizados aos visitantes.",
        "icon": "bi-file-earmark-person",
        "new_label": "Adicionar modelo",
        "columns": [
            {"key": "title", "label": "Modelo"},
            {"key": "category", "label": "Categoria"},
            {"key": "status", "label": "Estado"},
            {"key": "updated", "label": "Actualizado"},
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True, "placeholder": "Nome do modelo"},
            {"name": "description", "label": "Descrição", "type": "textarea", "required": True, "rows": 3, "placeholder": "Descreva este modelo"},
            {"name": "category", "label": "Categoria", "type": "select", "required": True},
            {"name": "preview", "label": "Pré-visualização (URL)", "type": "url", "placeholder": "https://... ou caminho da imagem"},
            {"name": "file", "label": "Ficheiro do modelo", "type": "file", "accept": ".pdf,.doc,.docx,.html"},
        ],
    },
    "categorias": {
        "title": "Categorias",
        "eyebrow": "Organização",
        "description": "Agrupe artigos, tutoriais e recursos por temas.",
        "icon": "bi-tags",
        "new_label": "Nova categoria",
        "columns": [
            {"key": "name", "label": "Nome"},
            {"key": "slug", "label": "Slug"},
            {"key": "count", "label": "Conteúdos"},
            {"key": "description", "label": "Descrição"},
        ],
        "fields": [
            {"name": "name", "label": "Nome da categoria", "type": "text", "required": True, "placeholder": "Ex.: Orientação profissional"},
            {"name": "slug", "label": "Slug", "type": "text", "required": True, "placeholder": "orientacao-profissional"},
            {"name": "description", "label": "Descrição", "type": "textarea", "rows": 3, "placeholder": "Uma descrição breve"},
        ],
    },
}


def _render_content_page(content_type, open_form=False, record_id=None):
    config = CONTENT_TYPES.get(content_type)
    if config is None:
        abort(404)

    records = deepcopy(MOCK_CONTENT[content_type])
    initial_record = next((record for record in records if record["id"] == record_id), None)
    if record_id is not None and initial_record is None:
        abort(404)

    return render_template(
        "admin/content_list.html",
        active_page=content_type,
        page_title=config["title"],
        content_type=content_type,
        config=config,
        records=records,
        categories=CATEGORY_OPTIONS,
        open_form=open_form,
        initial_record=initial_record,
    )


@admin.get("/")
@admin.get("")
def dashboard():
    recent_content = MOCK_CONTENT["artigos"][:2] + MOCK_CONTENT["tutoriais"][:1]
    return render_template(
        "admin/dashboard.html",
        active_page="dashboard",
        page_title="Dashboard",
        stats=[
            {"label": "Conteúdos publicados", "value": "28", "change": "+12% este mês", "icon": "bi-file-earmark-text", "tone": "blue"},
            {"label": "Rascunhos", "value": "6", "change": "A aguardar revisão", "icon": "bi-pencil-square", "tone": "orange"},
            {"label": "Modelos de CV", "value": "4", "change": "2 categorias", "icon": "bi-file-earmark-person", "tone": "green"},
            {"label": "Categorias", "value": str(len(MOCK_CATEGORIES)), "change": "Em 3 áreas", "icon": "bi-tags", "tone": "violet"},
        ],
        recent_content=recent_content,
        categories=MOCK_CATEGORIES,
    )


@admin.get("/<content_type>")
def content_list(content_type):
    return _render_content_page(content_type)


@admin.get("/<content_type>/novo")
def content_create(content_type):
    return _render_content_page(content_type, open_form=True)


@admin.get("/<content_type>/<int:record_id>/editar")
def content_edit(content_type, record_id):
    return _render_content_page(content_type, open_form=True, record_id=record_id)


@admin.get("/configuracoes")
def settings():
    return render_template(
        "admin/settings.html",
        active_page="configuracoes",
        page_title="Configurações do site",
    )
