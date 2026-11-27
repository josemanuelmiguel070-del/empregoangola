import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from .extensions import db
from .models import CVTemplate, Category, Content, Job
from .site import get_site_settings

admin = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_OPTIONS = [("draft", "Rascunho"), ("published", "Publicado")]
CONTENT_SPECS = {
    "artigos": {
        "title": "Artigos e blog",
        "eyebrow": "Publicações",
        "description": "Gira artigos e notícias publicados no portal.",
        "new_label": "Novo artigo",
        "model": Content,
        "content_type": "article",
        "columns": [
            ("title", "Título"),
            ("category", "Categoria"),
            ("status_label", "Estado"),
            ("updated_label", "Actualizado"),
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True},
            {"name": "slug", "label": "Endereço (slug)", "type": "text", "help": "Deixe vazio para gerar a partir do título."},
            {"name": "category_id", "label": "Categoria", "type": "category", "required": True},
            {"name": "featured_image_url", "label": "Imagem de destaque (URL)", "type": "url"},
            {"name": "summary", "label": "Resumo", "type": "textarea", "required": True},
            {"name": "body", "label": "Conteúdo", "type": "textarea", "required": True, "rows": 10},
            {"name": "status", "label": "Estado", "type": "status", "required": True},
        ],
    },
    "tutoriais": {
        "title": "Tutoriais",
        "eyebrow": "Conteúdo educativo",
        "description": "Publique guias e orientações práticas.",
        "new_label": "Novo tutorial",
        "model": Content,
        "content_type": "tutorial",
        "columns": [
            ("title", "Título"),
            ("category", "Categoria"),
            ("status_label", "Estado"),
            ("updated_label", "Actualizado"),
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True},
            {"name": "slug", "label": "Endereço (slug)", "type": "text", "help": "Deixe vazio para gerar a partir do título."},
            {"name": "category_id", "label": "Categoria", "type": "category", "required": True},
            {"name": "featured_image_url", "label": "Imagem (URL)", "type": "url"},
            {"name": "summary", "label": "Descrição", "type": "textarea", "required": True},
            {"name": "body", "label": "Conteúdo", "type": "textarea", "required": True, "rows": 10},
            {"name": "status", "label": "Estado", "type": "status", "required": True},
        ],
    },
    "modelos-cv": {
        "title": "Modelos de CV",
        "eyebrow": "Recursos para download",
        "description": "Gira ficheiros de currículo disponibilizados aos visitantes.",
        "new_label": "Adicionar modelo",
        "model": CVTemplate,
        "columns": [
            ("title", "Modelo"),
            ("category", "Categoria"),
            ("status_label", "Estado"),
            ("updated_label", "Actualizado"),
        ],
        "fields": [
            {"name": "title", "label": "Título", "type": "text", "required": True},
            {"name": "description", "label": "Descrição", "type": "textarea", "required": True},
            {"name": "category_id", "label": "Categoria", "type": "category", "required": True},
            {"name": "preview_url", "label": "Pré-visualização (URL)", "type": "url"},
            {"name": "file", "label": "Ficheiro do modelo", "type": "file", "accept": ".pdf,.doc,.docx,.html"},
            {"name": "status", "label": "Estado", "type": "status", "required": True},
        ],
    },
    "categorias": {
        "title": "Categorias",
        "eyebrow": "Organização",
        "description": "Organize artigos, tutoriais e modelos por temas.",
        "new_label": "Nova categoria",
        "model": Category,
        "columns": [
            ("name", "Nome"),
            ("slug", "Slug"),
            ("content_count", "Conteúdos"),
            ("cv_count", "Modelos de CV"),
        ],
        "fields": [
            {"name": "name", "label": "Nome da categoria", "type": "text", "required": True},
            {"name": "slug", "label": "Slug", "type": "text", "help": "Deixe vazio para gerar a partir do nome."},
            {"name": "description", "label": "Descrição", "type": "textarea"},
        ],
    },
    "vagas": {
        "title": "Vagas de emprego",
        "eyebrow": "Oportunidades",
        "description": "Publique e mantenha actualizadas oportunidades de emprego.",
        "new_label": "Nova vaga",
        "model": Job,
        "columns": [
            ("title", "Cargo"),
            ("company", "Empresa"),
            ("location", "Localização"),
            ("status_label", "Estado"),
        ],
        "fields": [
            {"name": "title", "label": "Cargo", "type": "text", "required": True},
            {"name": "company", "label": "Empresa", "type": "text", "required": True},
            {"name": "location", "label": "Localização", "type": "text", "required": True},
            {"name": "employment_type", "label": "Tipo de contrato", "type": "text"},
            {"name": "deadline", "label": "Prazo de candidatura", "type": "date"},
            {"name": "application_url", "label": "URL de candidatura", "type": "url"},
            {"name": "description", "label": "Descrição da vaga", "type": "textarea", "required": True, "rows": 10},
            {"name": "status", "label": "Estado", "type": "status", "required": True},
        ],
    },
}


@admin.before_request
def require_admin_login():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.full_path))
    return None


def _slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:180].rstrip("-")


def _unique_slug(model, value, record_id=None):
    base = _slugify(value) or "conteudo"
    candidate = base
    suffix = 2
    query = db.session.query(model.id).filter(model.slug == candidate)
    if record_id is not None:
        query = query.filter(model.id != record_id)
    while query.first() is not None:
        candidate = f"{base[:175]}-{suffix}"
        query = db.session.query(model.id).filter(model.slug == candidate)
        if record_id is not None:
            query = query.filter(model.id != record_id)
        suffix += 1
    return candidate


def _required_form_value(name, label):
    value = request.form.get(name, "").strip()
    if not value:
        raise ValueError(f"O campo «{label}» é obrigatório.")
    return value


def _category_id():
    value = _required_form_value("category_id", "Categoria")
    try:
        category_id = int(value)
    except ValueError as error:
        raise ValueError("Seleccione uma categoria válida.") from error
    if db.session.get(Category, category_id) is None:
        raise ValueError("A categoria seleccionada já não existe.")
    return category_id


def _optional_url(name, label):
    value = request.form.get(name, "").strip()
    if not value:
        return None
    parsed = urlsplit(value)
    if value.startswith("/static/") or parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    raise ValueError(f"Indique um URL HTTPS/HTTP ou um caminho /static/ válido para «{label}».")


def _status():
    status = _required_form_value("status", "Estado")
    if status not in {"draft", "published"}:
        raise ValueError("Seleccione um estado válido.")
    return status


def _save_cv_file():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return None
    safe_name = secure_filename(upload.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in {".pdf", ".doc", ".docx", ".html"}:
        raise ValueError("O ficheiro deve ser PDF, DOC, DOCX ou HTML.")
    filename = f"{uuid.uuid4().hex}{extension}"
    upload_directory = Path(current_app.instance_path) / "uploads" / "cv-templates"
    upload_directory.mkdir(parents=True, exist_ok=True)
    try:
        upload.save(upload_directory / filename)
    except OSError as error:
        raise ValueError("Não foi possível guardar o ficheiro enviado.") from error
    return filename


def _save_content(content_type, record=None):
    spec = CONTENT_SPECS[content_type]
    row = record or Content(content_type=spec["content_type"])
    row.title = _required_form_value("title", "Título")
    row.category_id = _category_id()
    supplied_slug = request.form.get("slug", "").strip()
    row.slug = _unique_slug(Content, supplied_slug or row.title, row.id)
    row.featured_image_url = _optional_url("featured_image_url", "Imagem")
    row.summary = _required_form_value("summary", "Resumo/descrição")
    row.body = _required_form_value("body", "Conteúdo")
    row.status = _status()
    db.session.add(row)
    db.session.commit()


def _save_cv_template(record=None):
    row = record or CVTemplate()
    row.title = _required_form_value("title", "Título")
    row.description = _required_form_value("description", "Descrição")
    row.category_id = _category_id()
    row.preview_url = _optional_url("preview_url", "Pré-visualização")
    row.status = _status()
    previous_file = row.file_path
    upload = request.files.get("file")
    if row.status == "published" and not row.file_path and (upload is None or not upload.filename):
        raise ValueError("Carregue um ficheiro antes de publicar o modelo.")
    uploaded_file = _save_cv_file()
    if uploaded_file:
        row.file_path = uploaded_file
    db.session.add(row)
    db.session.commit()
    if uploaded_file and previous_file:
        _remove_cv_file(previous_file)


def _save_category(record=None):
    row = record or Category()
    row.name = _required_form_value("name", "Nome")
    slug = request.form.get("slug", "").strip() or row.name
    row.slug = _unique_slug(Category, slug, row.id)
    row.description = request.form.get("description", "").strip() or None
    db.session.add(row)
    db.session.commit()


def _save_job(record=None):
    row = record or Job()
    row.title = _required_form_value("title", "Cargo")
    row.company = _required_form_value("company", "Empresa")
    row.location = _required_form_value("location", "Localização")
    row.employment_type = request.form.get("employment_type", "").strip() or None
    row.application_url = _optional_url("application_url", "URL de candidatura")
    row.description = _required_form_value("description", "Descrição")
    deadline_value = request.form.get("deadline", "").strip()
    if deadline_value:
        try:
            row.deadline = datetime.strptime(deadline_value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("Indique um prazo de candidatura válido.") from error
    else:
        row.deadline = None
    row.status = _status()
    db.session.add(row)
    db.session.commit()


def _record_data(content_type, row):
    if content_type in {"artigos", "tutoriais"}:
        data = {
            "id": row.id,
            "title": row.title,
            "slug": row.slug,
            "category": row.category.name,
            "category_id": row.category_id,
            "status": row.status,
            "status_label": "Publicado" if row.status == "published" else "Rascunho",
            "updated_label": row.updated_at.strftime("%d/%m/%Y") if row.updated_at else "",
            "featured_image_url": row.featured_image_url or "",
            "summary": row.summary,
            "body": row.body,
        }
    elif content_type == "modelos-cv":
        data = {
            "id": row.id,
            "title": row.title,
            "category": row.category.name,
            "category_id": row.category_id,
            "status": row.status,
            "status_label": "Publicado" if row.status == "published" else "Rascunho",
            "updated_label": row.updated_at.strftime("%d/%m/%Y") if row.updated_at else "",
            "description": row.description,
            "preview_url": row.preview_url or "",
            "file_path": row.file_path or "",
        }
    elif content_type == "categorias":
        data = {
            "id": row.id,
            "name": row.name,
            "slug": row.slug,
            "description": row.description or "",
            "content_count": len(row.content_items),
            "cv_count": len(row.cv_templates),
        }
    else:
        data = {
            "id": row.id,
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "employment_type": row.employment_type or "",
            "deadline": row.deadline.strftime("%Y-%m-%d") if row.deadline else "",
            "application_url": row.application_url or "",
            "description": row.description,
            "status": row.status,
            "status_label": "Publicado" if row.status == "published" else "Rascunho",
        }
    return data


def _list_records(content_type):
    spec = CONTENT_SPECS[content_type]
    if content_type in {"artigos", "tutoriais"}:
        rows = (
            Content.query.filter_by(content_type=spec["content_type"])
            .order_by(Content.updated_at.desc(), Content.id.desc())
            .all()
        )
    else:
        rows = spec["model"].query.order_by(spec["model"].id.desc()).all()
    return [_record_data(content_type, row) for row in rows]


def _render_content_page(content_type, open_form=False, record=None, form_values=None):
    spec = CONTENT_SPECS.get(content_type)
    if spec is None:
        abort(404)
    initial_record = _record_data(content_type, record) if record is not None else None
    return render_template(
        "admin/content_list.html",
        active_page=content_type,
        page_title=spec["title"],
        content_type=content_type,
        config=spec,
        records=_list_records(content_type),
        categories=Category.query.order_by(Category.name).all(),
        status_options=STATUS_OPTIONS,
        open_form=open_form,
        initial_record=initial_record,
        form_values=form_values or {},
        form_action=(
            url_for("admin.content_edit", content_type=content_type, record_id=record.id)
            if record is not None
            else url_for("admin.content_create", content_type=content_type)
        ),
    )


@admin.get("/")
@admin.get("")
def dashboard():
    published_content = Content.query.filter_by(status="published").count()
    published_jobs = Job.query.filter_by(status="published").count()
    categories = Category.query.order_by(Category.name).all()
    recent = []
    for row in Content.query.order_by(Content.updated_at.desc()).limit(5):
        recent.append({
            "title": row.title,
            "category": row.category.name,
            "status": "Publicado" if row.status == "published" else "Rascunho",
            "updated": row.updated_at.strftime("%d/%m/%Y") if row.updated_at else "",
            "type": "Tutorial" if row.content_type == "tutorial" else "Artigo",
            "updated_at": row.updated_at,
        })
    for row in Job.query.order_by(Job.updated_at.desc()).limit(5):
        recent.append({
            "title": row.title,
            "category": row.company,
            "status": "Publicado" if row.status == "published" else "Rascunho",
            "updated": row.updated_at.strftime("%d/%m/%Y") if row.updated_at else "",
            "type": "Vaga",
            "updated_at": row.updated_at,
        })
    recent.sort(key=lambda item: item["updated_at"] or datetime.min, reverse=True)
    for item in recent:
        item.pop("updated_at")

    return render_template(
        "admin/dashboard.html",
        active_page="dashboard",
        page_title="Dashboard",
        stats=[
            {"label": "Conteúdos publicados", "value": str(published_content), "change": "Artigos e tutoriais", "icon": "bi-file-earmark-text", "tone": "blue"},
            {"label": "Vagas publicadas", "value": str(published_jobs), "change": "Oportunidades activas", "icon": "bi-briefcase", "tone": "orange"},
            {"label": "Modelos de CV", "value": str(CVTemplate.query.filter_by(status="published").count()), "change": "Disponíveis para download", "icon": "bi-file-earmark-person", "tone": "green"},
            {"label": "Categorias", "value": str(len(categories)), "change": "Categorias registadas", "icon": "bi-tags", "tone": "violet"},
        ],
        recent_content=recent[:5],
        categories=[
            {
                "name": category.name,
                "count": len(category.content_items) + len(category.cv_templates),
            }
            for category in categories
        ],
        site_settings=get_site_settings(),
    )


@admin.get("/<content_type>")
def content_list(content_type):
    return _render_content_page(content_type)


@admin.route("/<content_type>/novo", methods=["GET", "POST"])
def content_create(content_type):
    if content_type not in CONTENT_SPECS:
        abort(404)
    if request.method == "POST":
        try:
            if content_type in {"artigos", "tutoriais"}:
                _save_content(content_type)
            elif content_type == "modelos-cv":
                _save_cv_template()
            elif content_type == "categorias":
                _save_category()
            else:
                _save_job()
            flash("Registo criado com sucesso.", "success")
            return redirect(url_for("admin.content_list", content_type=content_type))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um registo com estes dados únicos. Reveja o slug ou o nome.", "error")
    return _render_content_page(content_type, open_form=True, form_values=request.form)


@admin.route("/<content_type>/<int:record_id>/editar", methods=["GET", "POST"])
def content_edit(content_type, record_id):
    spec = CONTENT_SPECS.get(content_type)
    if spec is None:
        abort(404)
    if content_type in {"artigos", "tutoriais"}:
        record = Content.query.filter_by(id=record_id, content_type=spec["content_type"]).first_or_404()
    else:
        record = db.get_or_404(spec["model"], record_id)

    if request.method == "POST":
        try:
            if content_type in {"artigos", "tutoriais"}:
                _save_content(content_type, record)
            elif content_type == "modelos-cv":
                _save_cv_template(record)
            elif content_type == "categorias":
                _save_category(record)
            else:
                _save_job(record)
            flash("Registo actualizado com sucesso.", "success")
            return redirect(url_for("admin.content_list", content_type=content_type))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um registo com estes dados únicos. Reveja o slug ou o nome.", "error")
    return _render_content_page(
        content_type,
        open_form=True,
        record=record,
        form_values=request.form,
    )


def _remove_cv_file(filename):
    if not filename:
        return
    path = Path(current_app.instance_path) / "uploads" / "cv-templates" / filename
    if path.is_file():
        path.unlink()


@admin.post("/<content_type>/<int:record_id>/apagar")
def content_delete(content_type, record_id):
    spec = CONTENT_SPECS.get(content_type)
    if spec is None:
        abort(404)
    if content_type in {"artigos", "tutoriais"}:
        record = Content.query.filter_by(id=record_id, content_type=spec["content_type"]).first_or_404()
    else:
        record = db.get_or_404(spec["model"], record_id)

    if content_type == "categorias" and (record.content_items or record.cv_templates):
        flash("Não é possível apagar uma categoria que ainda tem conteúdos associados.", "error")
        return redirect(url_for("admin.content_list", content_type=content_type))

    old_file = record.file_path if content_type == "modelos-cv" else None
    db.session.delete(record)
    db.session.commit()
    if old_file:
        _remove_cv_file(old_file)
    flash("Registo apagado.", "success")
    return redirect(url_for("admin.content_list", content_type=content_type))


@admin.route("/configuracoes", methods=["GET", "POST"])
def settings():
    row = get_site_settings()
    if request.method == "POST":
        try:
            row.site_name = _required_form_value("site_name", "Nome do site")
            row.tagline = request.form.get("tagline", "").strip() or None
            row.about_text = request.form.get("about_text", "").strip() or None
            row.hero_title = request.form.get("hero_title", "").strip() or None
            row.hero_description = request.form.get("hero_description", "").strip() or None
            row.hero_image_url = _optional_url("hero_image_url", "Imagem do banner")
            row.contact_email = request.form.get("contact_email", "").strip() or None
            row.contact_whatsapp = request.form.get("contact_whatsapp", "").strip() or None
            row.footer_note = request.form.get("footer_note", "").strip() or None
            row.language = request.form.get("language", "").strip() or None
            row.id = 1
            db.session.add(row)
            db.session.commit()
            flash("Configurações guardadas.", "success")
            return redirect(url_for("admin.settings"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template(
        "admin/settings.html",
        active_page="configuracoes",
        page_title="Configurações do site",
        settings=row,
        site_settings=get_site_settings(),
    )


@admin.get("/ficheiros-cv/<path:filename>")
def download_cv_file(filename):
    return send_from_directory(
        Path(current_app.instance_path) / "uploads" / "cv-templates",
        filename,
        as_attachment=True,
    )
