# Emprego Angola

Portal editorial de emprego e orientação profissional para Angola, servido por Flask e templates Jinja2. As páginas, vagas e o painel administrativo continuam demonstrativos; existe uma camada de modelos preparada para persistência, ainda sem CRUD. O formulário de contacto encaminha mensagens através do Web3Forms.

## Estrutura

```text
.
├── app/
│   ├── __init__.py          # App factory, configuração e registo das extensões
│   ├── extensions.py        # SQLAlchemy, Flask-Migrate e Flask-Login
│   ├── models.py            # Modelos e relacionamentos
│   ├── admin.py             # Rotas administrativas demonstrativas
│   └── routes.py            # Rotas editoriais
├── migrations/              # Histórico das migrações da base de dados
├── templates/               # HTML renderizado pelo Jinja2
│   ├── index.html
│   └── pages/
├── static/                  # CSS, JavaScript, imagens, downloads e vendor
├── legacy/php/              # Handler PHP antigo, inactivo e não registado
├── tests/
│   ├── test_models.py
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

## Publicar no cPanel

Em **Setup Python App** no cPanel, crie uma aplicação com Python 3.10 ou superior, defina o *Application root* para a pasta do projecto e escolha o domínio e o URI pretendidos. Configure `passenger_wsgi.py` como *Application startup file* e `application` como *Application entry point*. O ficheiro [passenger_wsgi.py](./passenger_wsgi.py) expõe a aplicação Flask para o Passenger.

Instale as dependências no ambiente virtual indicado pelo cPanel:

```text
pip install -r requirements.txt
```

O cPanel gera o `.htaccess` com os caminhos específicos da conta e do ambiente virtual; não copie um `.htaccess` de outra instalação. Defina `DATABASE_URL` nas variáveis de ambiente da aplicação antes de iniciar. Para actualizar a base de dados, execute `flask --app run.py db upgrade` no terminal do cPanel, com o ambiente virtual activo. Reinicie a aplicação no cPanel depois de alterar código ou configuração.

## Base de dados e migrações

SQLite é utilizado por omissão, com o ficheiro `instance/zenblog.sqlite` (ignorado pelo Git). Para MySQL, defina `DATABASE_URL` no ambiente, por exemplo:

```text
mysql+pymysql://utilizador:senha@servidor/base_de_dados
```

Uma URL no formato `mysql://` também é convertida para o driver PyMySQL. A mesma aplicação e os mesmos modelos servem ambos os dialectos; não há criação automática de tabelas ao iniciar. Aplique a migração inicial com:

```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
```

Os modelos cobrem contas administrativas e tokens de recuperação (preparação para autenticação, sem fluxo de login), categorias, artigos/notícias/tutoriais, modelos de CV e configurações do site. Categorias relacionam-se com conteúdos e modelos de CV; tokens relacionam-se com a conta administrativa. O painel ainda usa dados mockados: não há CRUD, persistência de conteúdos, upload nem gestão local de mensagens de contacto.

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
