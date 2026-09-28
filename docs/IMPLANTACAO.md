# Implantação no site

Do zero até o PubliBot publicar o primeiro artigo.

## 1. Credenciais

No PubliBot, em **Site e cadência**, cadastre o site. Saem de lá dois
valores: a **chave de API** e o **segredo de assinatura**. Guarde os dois no
ambiente do site (`.env`, variáveis do serviço), **nunca** no código.

## 2. Instalar e configurar

```bash
pip install "publi-bot-core-django @ git+https://github.com/EduardoReolon/publi-bot-core-django@main"
```

No `requirements.txt`, a mesma linha. Para travar numa versão, troque `@main`
por uma tag, como `@v1.0.0`.

```python
# settings.py
INSTALLED_APPS = [..., "publibot_core"]

PUBLIBOT_API_KEY = os.environ["PUBLIBOT_API_KEY"]
PUBLIBOT_SIGNING_SECRET = os.environ["PUBLIBOT_SIGNING_SECRET"]
PUBLIBOT_PUBLIC_URL = "https://www.seusite.com.br"  # sem barra no fim
PUBLIBOT_ARTICLE_PATH = "/blog/{slug}/"  # {slug}, {id}
PUBLIBOT_QA_PATH = "/perguntas/{question_id}/"  # {question_id}, {slug}, {id}

# O que o PubliBot lê para conhecer o site. Texto, ou "func:caminho.da.funcao".
PUBLIBOT_SITE_TITLE = "Nome do site"
PUBLIBOT_HOME_TEXT = "func:meusite.textos.texto_da_home"

# Fotos de autor chegam por upload (até 5 MB): o padrão do Django (2,5 MB) recusa.
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
```

| Setting | Obrigatório | Padrão |
|---|---|---|
| `PUBLIBOT_API_KEY` | sim | |
| `PUBLIBOT_SIGNING_SECRET` | sim | |
| `PUBLIBOT_PUBLIC_URL` | sim | |
| `PUBLIBOT_ARTICLE_PATH` | não | `/blog/{slug}/` |
| `PUBLIBOT_QA_PATH` | não | `/perguntas/{question_id}/` |
| `PUBLIBOT_SITE_TITLE`, `PUBLIBOT_HOME_TEXT` | não | vazio |
| `PUBLIBOT_API_KEY_PREVIOUS` | só na troca de chave | vazio |
| `PUBLIBOT_REQUIRE_HTTPS` | não | exige HTTPS fora do `DEBUG` |

```python
# urls.py
(path("api/v1/", include("publibot_core.urls")),)
```

O prefixo `api/v1/` é o que o PubliBot espera por padrão. Outro prefixo
funciona se for o mesmo cadastrado no PubliBot.

## 3. Banco e mídia

```bash
python manage.py migrate
python manage.py collectstatic   # o leitura.js
```

- **Banco:** qualquer um suportado pelo Django. Nada depende do Postgres. Os
  campos `JSONField` pedem SQLite com JSON1 (o padrão desde o Python 3.9) ou
  MySQL 5.7+.
- **Mídia:** as fotos de autor vão para `MEDIA_ROOT/publibot/autores/` e as
  capas para `MEDIA_ROOT/publibot/capas/`. O servidor web precisa servir
  `MEDIA_URL`.
- **Capas:** baixadas logo depois de cada publicação, em segundo plano. O que
  falhar (rede, digest) fica pendente; um cron de hora em hora resolve:
  `python manage.py publibot_baixar_capas`.
- **Cache:** o limite de requisições por IP usa o cache do Django. Com um
  processo só, o padrão (memória) basta; com vários, use Redis ou o cache em
  banco. A proteção contra reenvio (nonce) fica no banco e não depende disso.

## 4. HTTPS e proxy

As rotas recusam HTTP fora do `DEBUG`. Atrás de Nginx ou de um balanceador,
diga ao Django que a conexão original era HTTPS:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
client_max_body_size 12m;   # corpo de /publish/ e fotos
```

O relógio do servidor precisa estar certo (NTP): requisição com mais de
5 minutos de diferença é recusada.

## 5. Sitemap

```python
# settings.py
INSTALLED_APPS = [..., "django.contrib.sitemaps"]

# urls.py
from django.contrib.sitemaps.views import sitemap
from publibot_core.sitemaps import PublicationSitemap

sitemaps = {"blog": PublicationSitemap}  # e as outras paginas do site
(path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),)
```

Envie `https://www.seusite.com.br/sitemap.xml` no Search Console. O que mais
o site precisa para o Google: [SEO_DO_SITE.md](SEO_DO_SITE.md).

## 6. Conferir

No site:

```bash
python manage.py publibot_conferir
```

Confere credenciais, migrações, rotas, mídia, limite de upload e HTTPS.

No PubliBot: `manage.py conferir_instalacao`, linha **site**. Ela chama a
rota `health/` com assinatura, provando que chave, segredo, endereço e
relógio batem dos dois lados.

## 7. Template

Veja [PARA_IA.md](PARA_IA.md): a lista do blog, a página do artigo, a
chamada, o "Leia também", a medição e o formulário de pergunta.

## Trocar a chave de API

1. No PubliBot, gere a chave nova.
2. No site, `PUBLIBOT_API_KEY_PREVIOUS = <antiga>` e `PUBLIBOT_API_KEY = <nova>`,
   e reinicie.
3. Depois que o PubliBot passar a usar a nova, apague a anterior.

## Atualizar

```bash
pip install -U "publi-bot-core-django @ git+https://github.com/EduardoReolon/publi-bot-core-django@main"
python manage.py migrate
python manage.py collectstatic
```

Antes, leia o [CHANGELOG](../CHANGELOG.md): ele diz quando uma versão pede
algo além disso.
