from flask import Blueprint, render_template, request

main = Blueprint("main", __name__)


@main.get("/")
def index():
    return render_template("index.html")


@main.get("/sobre")
def sobre():
    return render_template("pages/about.html")


@main.get("/vagas")
def vagas():
    query = request.args.get("q", "").strip()
    return render_template("pages/category.html", query=query)


@main.get("/contacto")
def contacto():
    return render_template("pages/contact.html")


@main.get("/tutoriais")
def tutoriais():
    return render_template("pages/starter-page.html")


@main.get("/artigo-exemplo")
def artigo_exemplo():
    return render_template("pages/single-post.html")
