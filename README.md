# publi-bot-core-django

O lado do **site** no contrato PubliBot `/api/v1`, como app Django instalável.
O PubliBot escreve artigos, respostas a perguntas de visitantes e fotos de
autor; este app recebe, confere a assinatura, sanitiza e guarda. O site só
**lê** as tabelas e monta as páginas do jeito dele.

Funciona com qualquer banco suportado pelo Django (testado em SQLite,
PostgreSQL e MySQL).

## Instalar

```bash
pip install "publi-bot-core-django @ git+https://github.com/EduardoReolon/publi-bot-core-django@main"
```

```python
# settings.py
INSTALLED_APPS = [..., "publibot_core"]

PUBLIBOT_API_KEY = os.environ["PUBLIBOT_API_KEY"]  # do cadastro no PubliBot
PUBLIBOT_SIGNING_SECRET = os.environ["PUBLIBOT_SIGNING_SECRET"]
PUBLIBOT_PUBLIC_URL = "https://www.seusite.com.br"
PUBLIBOT_ARTICLE_PATH = "/blog/{slug}/"  # onde o site mostra o artigo
```

```python
# urls.py
(path("api/v1/", include("publibot_core.urls")),)
```

```bash
python manage.py migrate
python manage.py publibot_conferir
```

Passo a passo completo (HTTPS, mídia, cache, atualização):
[docs/IMPLANTACAO.md](docs/IMPLANTACAO.md).

## Usar no site

```python
from publibot_core.models import Publication

Publication.objects.visiveis()  # a lista do blog
```

```django
{% load publibot %}
<head>{% publibot_head artigo %}</head>
<article data-publibot-id="{{ artigo.id }}">
  <h1>{{ artigo.title }}</h1>
  {% corpo_com_chamada artigo %}
  {% chamada_no_fim artigo %}
  {% leia_tambem artigo %}
</article>
```

Tudo o que o site usa (tabelas, campos, tags, exemplos de view e template):
[docs/PARA_IA.md](docs/PARA_IA.md). Escrito para ser lido por uma IA que vai
montar ou mudar o site.

Para que o site existe (ser achado no Google e converter) e o que toda página
de artigo precisa ter: [docs/SEO_DO_SITE.md](docs/SEO_DO_SITE.md).

## Atualizar

Faça um novo deploy do site, se ele reinstala a biblioteca a cada vez (o
recomendado, ver [docs/IMPLANTACAO.md](docs/IMPLANTACAO.md#atualizar)). Se não
reinstala, no servidor:

```bash
pip install -U "publi-bot-core-django @ git+https://github.com/EduardoReolon/publi-bot-core-django@main"
python manage.py migrate
```

O que mudou em cada versão: [CHANGELOG.md](CHANGELOG.md).
