# Emprego Angola

Portal editorial de emprego e orientação profissional para Angola, servido por Flask, SQLAlchemy e templates Jinja2. Artigos, tutoriais, vagas, modelos de CV, categorias e configurações são guardados na base de dados. Só registos publicados aparecem nas páginas públicas. O formulário de contacto encaminha mensagens através do Web3Forms.

## Estrutura

```text
.
├── app/
│   ├── __init__.py          # App factory, configuração e registo das extensões
│   ├── extensions.py        # SQLAlchemy, Flask-Migrate e Flask-Login
│   ├── models.py            # Modelos e relacionamentos
│   ├── admin.py             # CRUD administrativo protegido
│   ├── auth.py              # Sessão de administrador
│   ├── site.py              # Configurações públicas
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

O cPanel gera o `.htaccess` com os caminhos específicos da conta e do ambiente virtual; não copie um `.htaccess` de outra instalação. Configure `SECRET_KEY` com um valor aleatório longo, `DATABASE_URL` com as credenciais MySQL e `SESSION_COOKIE_SECURE=true` quando o site estiver em HTTPS. Para actualizar a base de dados, execute `flask --app run.py db upgrade` no terminal do cPanel, com o ambiente virtual activo. Crie o primeiro administrador com `flask --app run.py create-admin`; o comando solicita email e palavra-passe (mínimo 12 caracteres). Reinicie a aplicação no cPanel depois de alterar código ou configuração.

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

O painel em `/admin` exige início de sessão. O comando `create-admin` cria a primeira conta; palavras-passe são armazenadas com hash e formulários protegidos por CSRF. O CRUD abrange artigos, tutoriais, vagas, modelos de CV, categorias e configurações. Upload de modelos de CV aceita PDF, DOC, DOCX ou HTML até ao limite total de pedido e guarda os ficheiros em `instance/uploads/cv-templates`; faça backup dessa pasta juntamente com a base de dados. Categorias em uso não podem ser apagadas. Não são inseridos conteúdos de exemplo automaticamente.

Artigos e tutoriais têm páginas de detalhe em `/artigos/<slug>` e `/tutoriais/<slug>`. Vagas publicadas e dentro do prazo, artigos, tutoriais e modelos publicados aparecem nas páginas públicas; rascunhos não são visíveis sem autenticação. O site não inclui um fluxo público de registo nem recuperação de palavra-passe.

## Estado do CRUD

O CRUD administrativo está implementado e as operações foram cobertas por testes automáticos:

- criar, editar e apagar artigos e tutoriais;
- criar, pesquisar e apagar vagas;
- criar e apagar categorias, com proteção para categorias associadas a outros registos;
- enviar, listar, disponibilizar e apagar modelos de CV;
- guardar e aplicar as configurações do site;
- validar dados obrigatórios, estados, slugs e URLs;
- restringir a área administrativa a utilizadores autenticados;
- mostrar apenas conteúdos publicados nas páginas públicas.

Antes de utilizar o painel em uma instalação nova, aplique as migrações e crie o administrador:

```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
flask create-admin
```

Acceda ao painel em `/admin/login`.

## Rotas

| URL | Endpoint do Blueprint | Template |
| --- | --- | --- |
| `/` | `main.index` | `templates/index.html` |
| `/sobre` | `main.sobre` | `templates/pages/about.html` |
| `/vagas` | `main.vagas` | `templates/pages/category.html` |
| `/contacto` | `main.contacto` | `templates/pages/contact.html` |
| `/tutoriais` | `main.tutoriais` | `templates/pages/starter-page.html` |
| `/artigos/<slug>` | `main.article_detail` | `templates/pages/content_detail.html` |
| `/tutoriais/<slug>` | `main.tutorial_detail` | `templates/pages/content_detail.html` |

A pesquisa de vagas e artigos aceita `q` por query string (por exemplo, `/vagas?q=contabilidade`) e consulta os registos publicados na base de dados.

## Testes

```powershell
py -m unittest discover -s tests -v
```

Na validação local, 13 dos 14 testes passam. O teste restante verifica o ponto de entrada Passenger com uma segunda aplicação ligada à base SQLite por omissão; para o passar numa instalação limpa, execute `flask db upgrade` antes da suite. Os testes CRUD, de autenticação, uploads, modelos e rotas públicas passam.

O handler em `legacy/php/contact.php` foi preservado apenas como legado; não é chamado pelas rotas Flask nem utilizado pelo formulário de contacto.
