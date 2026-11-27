from datetime import datetime

from flask import Blueprint, abort, render_template, request, send_from_directory, current_app
from sqlalchemy import or_

from .extensions import db
from .models import CVTemplate, Content, Job
from .site import get_site_settings

main = Blueprint("main", __name__)


@main.app_context_processor
def inject_site_settings():
    return {"site_settings": get_site_settings()}


@main.get("/")
def index():
    jobs = (
        Job.query.filter_by(status="published")
        .filter(or_(Job.deadline.is_(None), Job.deadline >= datetime.now()))
        .order_by(Job.created_at.desc())
        .limit(3)
        .all()
    )
    tutorials = (
        Content.query.filter_by(content_type="tutorial", status="published")
        .order_by(Content.created_at.desc())
        .limit(3)
        .all()
    )
    articles = (
        Content.query.filter_by(content_type="article", status="published")
        .order_by(Content.created_at.desc())
        .limit(1)
        .all()
    )
    return render_template("index.html", jobs=jobs, tutorials=tutorials, articles=articles)


@main.get("/sobre")
def sobre():
    cv_templates = (
        CVTemplate.query.filter_by(status="published")
        .order_by(CVTemplate.created_at.desc())
        .all()
    )
    return render_template("pages/about.html", cv_templates=cv_templates)


@main.get("/vagas")
def vagas():
    query = request.args.get("q", "").strip()
    job_query = Job.query.filter_by(status="published").filter(
        or_(Job.deadline.is_(None), Job.deadline >= datetime.now())
    )
    article_query = Content.query.filter_by(content_type="article", status="published")
    if query:
        pattern = f"%{query}%"
        job_query = job_query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.company.ilike(pattern),
                Job.location.ilike(pattern),
                Job.description.ilike(pattern),
            )
        )
        article_query = article_query.filter(
            or_(
                Content.title.ilike(pattern),
                Content.summary.ilike(pattern),
                Content.body.ilike(pattern),
            )
        )
    jobs = job_query.order_by(Job.created_at.desc()).all()
    articles = article_query.order_by(Content.created_at.desc()).all()
    return render_template("pages/category.html", query=query, jobs=jobs, articles=articles)


@main.get("/contacto")
def contacto():
    return render_template("pages/contact.html")


@main.get("/tutoriais")
def tutoriais():
    tutorials = (
        Content.query.filter_by(content_type="tutorial", status="published")
        .order_by(Content.created_at.desc())
        .all()
    )
    return render_template("pages/starter-page.html", tutorials=tutorials)


@main.get("/artigos/<slug>")
def article_detail(slug):
    content = Content.query.filter_by(
        slug=slug, content_type="article", status="published"
    ).first_or_404()
    return render_template("pages/content_detail.html", content=content, content_label="Artigo")


@main.get("/tutoriais/<slug>")
def tutorial_detail(slug):
    content = Content.query.filter_by(
        slug=slug, content_type="tutorial", status="published"
    ).first_or_404()
    return render_template("pages/content_detail.html", content=content, content_label="Tutorial")


@main.get("/modelos-cv/<int:template_id>/download")
def download_cv_template(template_id):
    template = db.get_or_404(CVTemplate, template_id)
    if template.status != "published" or not template.file_path:
        abort(404)
    return send_from_directory(
        current_app.instance_path + "/uploads/cv-templates",
        template.file_path,
        as_attachment=True,
    )
