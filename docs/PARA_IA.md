# publibot_core para quem monta o site

Leia isto antes de escrever views, templates ou formulários que usem conteúdo
do PubliBot. Tudo o que o site precisa está aqui. O resto do pacote é a API
que o PubliBot chama, e o site não deve mexer nela.

**Leia também [SEO_DO_SITE.md](SEO_DO_SITE.md)**: para que o site existe (ser
achado no Google e converter), o que toda página de artigo precisa ter e os
erros que tiram o artigo da busca.

## A divisão de trabalho

| Quem | Faz |
|---|---|
| **PubliBot** | Escreve e revisa artigos e respostas, e manda para as rotas `/api/v1/` deste app. Também busca as perguntas dos visitantes e os números de leitura. |
| **publibot_core** (este app) | Confere a assinatura, sanitiza o HTML, guarda e responde ao PubliBot. |
| **O site** | Lê as tabelas abaixo e monta as páginas. Grava só as perguntas de visitantes, pelo formulário dele. |

O HTML que chega já foi sanitizado **duas vezes** (no PubliBot e aqui). Pode
ser mostrado com `|safe`, ou pelas tags deste app.

## As três tabelas que o site usa

```python
from publibot_core.models import Publication, VisitorQuestion, AuthorPhoto
```

Existem outras (leitura por dia, conversões, nonces), em
`publibot_core.models._internos`. **O site não lê nem grava nelas.**

### Publication: artigos e respostas (só leitura)

| Campo | Tipo | Para quê |
|---|---|---|
| `id` | UUID | Identidade. Vai no `data-publibot-id` do `<article>` (medição). |
| `kind` | `"article"` ou `"qa"` | Artigo ou resposta a uma pergunta. |
| `title` | texto (300) | Título (texto puro). |
| `slug` | slug (300) | Para a URL. Nunca muda depois da publicação, nem numa atualização. |
| `html_content` | HTML | O corpo, sanitizado. Use as tags abaixo em vez de mostrar direto. |
| `excerpt` | texto | Resumo para listas e cartões. |
| `meta_description` | texto (160) | `<meta name="description">`. |
| `focus_keyword` | texto (120) | A palavra-chave (não precisa aparecer na página). |
| `language` | texto | `pt-br` etc. Para o `lang` do HTML. |
| `author_name`, `author_credentials` | texto | Caixa do autor. |
| `author_reference` | UUID | Liga à `AuthorPhoto`. Use `artigo.foto_do_autor` ou a tag `foto_do_autor`. |
| `reviewed_by`, `reviewed_at` | texto, data | "Revisado por", quando houver. |
| `content_disclosure` | texto | Aviso sobre como o conteúdo foi produzido. Mostre, se vier preenchido. |
| `canonical_source` | URL | A FONTE principal citada (o estudo). **Nunca** use como `<link rel="canonical">`: o canonical é o endereço do próprio artigo. |
| `cover_image_alt` | texto | O `alt` da capa. |
| `capa_url` (propriedade) | URL | A capa. O app baixa a imagem para `MEDIA_ROOT/publibot/capas/` e serve do site; enquanto não baixou, é a URL de origem. Não use `cover_image_url` direto. |
| `faq` | lista `[{"question", "answer_html"}]` | Perguntas frequentes, separadas do corpo. Veja o exemplo com schema.org abaixo. |
| `call_to_action` | `"none"`, `"end"` ou `"inline"` | Onde vai o bloco da sua oferta. As tags cuidam disso. |
| `related_articles` | lista `[{"remote_id", "title", "url"}]` | "Leia também", escolhido pelo PubliBot. Tag `leia_tambem`. |
| `question_id` | texto | Em `kind="qa"`: o id da `VisitorQuestion` respondida. |
| `post_status` | `"published"`, `"draft"` ou `"scheduled"` | Use `Publication.objects.visiveis()` em vez de filtrar à mão. |
| `publish_at` | data | Quando entra no ar (agendado). |
| `published_at` | data | Quando entrou no ar. `artigo.data_de_publicacao` já escolhe a data certa. |
| `version`, `updated_at` | número, data | Quantas vezes foi atualizado, e quando. Para "Atualizado em". |

Consultas prontas:

```python
Publication.objects.visiveis()  # artigos no ar (publicados, ou agendados cuja hora chegou)
Publication.objects.respostas_visiveis()  # respostas publicadas
```

Métodos e propriedades:

- `artigo.get_absolute_url()`: o caminho, pelo `PUBLIBOT_ARTICLE_PATH` (ou
  `PUBLIBOT_QA_PATH`) do settings.
- `artigo.url`: o endereço completo. É o que volta ao PubliBot.
- `artigo.data_de_publicacao`: para mostrar e ordenar.
- `artigo.data_de_atualizacao`: "Atualizado em" (a última versão recebida).
- `artigo.capa_url`: a capa servida pelo site.
- `artigo.foto_do_autor`: a `AuthorPhoto`, ou `None`.

**Não grave nesta tabela.** O PubliBot substitui o conteúdo a cada
atualização; uma correção feita no site se perde. Corrija no PubliBot.

### VisitorQuestion: perguntas dos visitantes (o site grava)

O formulário "pergunte ao especialista" é do site. Ele grava aqui; o PubliBot
busca as pendentes, e a resposta volta como `Publication(kind="qa")`.

| Campo | Tipo | Para quê |
|---|---|---|
| `id` | UUID | |
| `question_text` | texto (500) | A pergunta. Obrigatório. |
| `author_name` | texto (150) | Opcional. Só vai para o PubliBot se `consent_at` estiver preenchido. |
| `consent_at` | data | Quando a pessoa aceitou que o nome fosse usado. |
| `submitted_at` | data | Preenchido sozinho. |
| `acknowledged_at`, `answered_at` | data | Preenchidos pelo app. Não mexa. |

`pergunta.resposta` devolve a `Publication` que a responde, se já publicada.

### AuthorPhoto: fotos dos autores (só leitura)

| Campo | Para quê |
|---|---|
| `author_reference` | O mesmo UUID de `Publication.author_reference`. |
| `image` | `ImageField` (WebP), em `MEDIA_ROOT/publibot/autores/`. |

A foto chega **depois** da primeira publicação do autor. Até lá,
`foto_do_autor` é vazio: tenha um marcador de lugar no template.

## Tags de template

```django
{% load publibot %}
```

| Tag | O que faz |
|---|---|
| `{% publibot_head artigo %}` | No `<head>`: title, description, canonical, Open Graph e JSON-LD (`Article` e `FAQPage`). |
| `{% corpo_com_chamada artigo %}` | O corpo. Se o artigo pede a chamada no meio (`inline`), põe o seu bloco no lugar da marca. |
| `{% chamada_no_fim artigo %}` | O seu bloco no fim (`end` e `inline`). Nada em `none`. |
| `{% leia_tambem artigo %}` | A lista "Leia também". |
| `{% foto_do_autor artigo %}` | A URL da foto, ou `""`. |

O bloco da chamada vem do template `publibot/chamada.html`, e a lista do
`publibot/relacionados.html`. **Sobrescreva os dois** no projeto, com o mesmo
caminho numa pasta de templates que venha antes deste app. No bloco da
chamada, mantenha:

- `data-publibot-bloco` no elemento de fora;
- `data-publibot-conversao="<tipo>"` no botão (ex.: `whatsapp`, `contato`).

É por eles que a medição conta a chamada vista, o clique e a conversão.

## Referências do artigo

O corpo (`artigo.body_html`) termina com a lista de todas as fontes que o
texto cita:

```html
<details class="publibot-referencias" open>
  <summary>Referências</summary>
  <ol><li><a href="https://doi.org/...">Gupta et al., 2006</a></li>...</ol>
</details>
```

No texto, só as fontes principais (até duas) viram link; as outras aparecem
citadas pelo nome, e todas estão na lista. A lista vem **aberta** (`open`) nos
artigos de pesquisa científica e **recolhida** nos demais ("Ver todas as
referências (N)"). Abrir e fechar é do próprio navegador: não precisa de
JavaScript.

- Mude a aparência pela classe `publibot-referencias` no CSS do site.
- Se o CSS do site esconde o marcador padrão do `summary`, ponha um próprio
  (▸ fechado, ▾ aberto), senão não fica claro que dá para abrir.
- Não remova o bloco nem as tags: o pacote já aceita `details` e `summary`
  no sanitizador.

## Medição (leitura e conversão)

Inclua o script em **todas** as páginas com artigo **e** na landing page da
oferta, porque a conversão pode acontecer fora do artigo:

```django
{% load static %}
<script src="{% static 'publibot/leitura.js' %}" data-endpoint="/api/v1/" defer></script>
```

- O `<article>` precisa de `data-publibot-id="{{ artigo.id }}"`.
- Com banner de consentimento: defina `window.publibotMedir = false` antes do
  script enquanto a pessoa não aceitar.
- Nada identifica quem lê: só contadores por dia, e a jornada fica no
  navegador da pessoa até ela converter.

## Exemplos

### views.py

```python
from django.shortcuts import get_object_or_404, render
from publibot_core.models import Publication


def blog(request):
    artigos = Publication.objects.visiveis().order_by("-published_at")
    return render(request, "blog/lista.html", {"artigos": artigos})


def artigo(request, slug):
    artigo = get_object_or_404(Publication.objects.visiveis(), slug=slug)
    return render(request, "blog/artigo.html", {"artigo": artigo})
```

```python
# urls.py (bate com PUBLIBOT_ARTICLE_PATH = "/blog/{slug}/")
(path("blog/", views.blog),)
(path("blog/<slug:slug>/", views.artigo),)
(path("api/v1/", include("publibot_core.urls")),)
```

### blog/artigo.html

```django
{% load publibot static %}
<html lang="{{ artigo.language }}">
<head>
  {% publibot_head artigo %}
</head>
<body>
<article data-publibot-id="{{ artigo.id }}">
  <h1>{{ artigo.title }}</h1>
  {% if artigo.capa_url %}<img src="{{ artigo.capa_url }}" alt="{{ artigo.cover_image_alt }}" width="1200" height="630">{% endif %}
  {% foto_do_autor artigo as foto %}
  <p>{% if foto %}<img src="{{ foto }}" alt="{{ artigo.author_name }}" width="48" height="48">{% endif %}
     {{ artigo.author_name }} · {{ artigo.author_credentials }} · {{ artigo.data_de_publicacao|date:"d/m/Y" }}
     {% if artigo.version > 1 %} · atualizado em {{ artigo.data_de_atualizacao|date:"d/m/Y" }}{% endif %}</p>
  {% corpo_com_chamada artigo %}
  {% if artigo.faq %}
    <section><h2>Perguntas frequentes</h2>
      {% for item in artigo.faq %}<h3>{{ item.question }}</h3>{{ item.answer_html|safe }}{% endfor %}
    </section>
  {% endif %}
  {% chamada_no_fim artigo %}
  {% leia_tambem artigo %}
  {% if artigo.content_disclosure %}<p><small>{{ artigo.content_disclosure }}</small></p>{% endif %}
</article>
<script src="{% static 'publibot/leitura.js' %}" data-endpoint="/api/v1/" defer></script>
</body>
</html>
```

### Formulário de pergunta

```python
from publibot_core.models import VisitorQuestion

VisitorQuestion.objects.create(
    question_text=form.cleaned_data["pergunta"][:500],
    author_name=form.cleaned_data.get("nome", ""),
    consent_at=timezone.now() if form.cleaned_data.get("aceito") else None,
)
```

## O que não fazer

- Gravar ou apagar `Publication` pelo site ou pelo admin: o admin deste app é
  somente leitura de propósito.
- Mudar a URL de um artigo publicado (`PUBLIBOT_ARTICLE_PATH`) sem
  redirecionar a antiga: o endereço acumula posição no Google.
- Ler as tabelas de `_internos`.
- Usar `canonical_source` como canonical (tira o artigo da busca).
- Mostrar `html_content` direto quando o artigo tem chamada: a marca
  `<aside data-publibot="chamada">` ficaria na página. Use
  `{% corpo_com_chamada %}`.

## O contrato

As rotas, os campos e as regras de assinatura estão em
[`openapi.yaml`](openapi.yaml). Ele é mantido junto com o PubliBot; este
pacote é a implementação para Django.
