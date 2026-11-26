# Emprego Angola

Portal editorial de emprego e orientação profissional para Angola, servido por Flask e templates Jinja2. As páginas e vagas continuam a ser conteúdo demonstrativo; não existe integração com base de dados. O formulário de contacto encaminha mensagens através do Web3Forms.

## Estrutura

```text
.
├── app/
│   ├── __init__.py          # App factory e registo do Blueprint
│   └── routes.py            # Rotas editoriais
├── templates/               # HTML renderizado pelo Jinja2
│   ├── index.html
│   └── pages/
├── static/                  # CSS, JavaScript, imagens, downloads e vendor
├── legacy/php/              # Handler PHP antigo, inactivo e não registado
├── tests/
│   └── test_routes.py
├── requirements.txt
└── run.py                   # Ponto de entrada local
```

## Executar localmente

Com Python instalado, a partir da pasta do projecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Abra `http://127.0.0.1:5000/`. O Flask serve os ficheiros de `static/` em `/static/`. A aplicação é para desenvolvimento local; não executar com o servidor de desenvolvimento do Flask em produção.

## Rotas

| URL | Endpoint do Blueprint | Template |
| --- | --- | --- |
| `/` | `main.index` | `templates/index.html` |
| `/sobre` | `main.sobre` | `templates/pages/about.html` |
| `/vagas` | `main.vagas` | `templates/pages/category.html` |
| `/contacto` | `main.contacto` | `templates/pages/contact.html` |
| `/tutoriais` | `main.tutoriais` | `templates/pages/starter-page.html` |
| `/artigo-exemplo` | `main.artigo_exemplo` | `templates/pages/single-post.html` |

A pesquisa de vagas aceita `q` por query string (por exemplo, `/vagas?q=contabilidade`) e mantém o termo no campo de pesquisa. A filtragem do conteúdo demonstrativo é feita no navegador.

## Testes

```powershell
python -m unittest discover -s tests
```

O handler em `legacy/php/contact.php` foi preservado apenas como legado; não é chamado pelas rotas Flask nem utilizado pelo formulário de contacto.
