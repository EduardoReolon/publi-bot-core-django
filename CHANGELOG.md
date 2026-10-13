# Mudanças

## 1.4.0

Nada a rodar (sem migração). Atualize o pacote e faça o deploy do site.

- **Destaque no meio do texto**: o `html_content` pode trazer ate dois
  `<aside data-publibot="destaque"><p><strong>frase</strong></p></aside>` — a
  frase que resume a ideia mais importante de uma secao, em letra maior. O
  sanitizador aceita (com o texto dentro) e o `publibot/head.html` traz um
  estilo padrao (borda lateral, fonte 1,4x); para mudar, use o seletor
  `aside[data-publibot="destaque"]` no CSS do site. Sem o `head.html`, o
  destaque aparece como paragrafo em negrito.

## 1.3.0

Rode `migrate` (faça um novo deploy do site; ver `docs/IMPLANTACAO.md`, "Atualizar").
Nada a mudar nos templates: o `leitura.js` novo vem no pacote (se o site serve
uma copia propria do script, troque pela nova).

- Leitura **por origem da visita**: cada abertura conta tambem para o seu canal
  e a sua fonte (o `utm_source` do link, ou quem mandou: `instagram`, `google`,
  `linkedin`...). Navegar dentro do site mantem a origem da entrada (guardada
  so na sessao do navegador). Tabela interna nova, `SourceReading`.
- **Ate onde rolou**: o script manda a profundidade (0 a 100) e o site conta
  `half_read` (passou da metade do texto), no total do dia e por origem.
- `GET /insights/` devolve `half_read` em cada linha e `reading_by_source` na
  primeira pagina. `docs/openapi.yaml` atualizado (`LeituraPorOrigem`).

## 1.2.1

Só documentação; nada a rodar.

- `docs/IMPLANTACAO.md` e `docs/SEO_DO_SITE.md`: o `robots.txt` com a linha
  `Sitemap:` (com exemplo de view), e o envio no Search Console como
  recomendado uma vez, para ver o status e os erros.

## 1.2.0

Rode `migrate` (faça um novo deploy do site; ver `docs/IMPLANTACAO.md`, "Atualizar").

- Campo novo `call_to_action_copy`: o texto do bloco da chamada escrito pelo
  PubliBot para cada artigo (`{"inline"|"end": {"title", "text", "button"}}`),
  gravado como texto puro e dentro dos limites (70, 200 e 30 caracteres).
- O template `publibot/chamada.html` recebe `texto` (o do lugar: meio ou fim)
  além de `onde`. **Ajuste o seu template** para usar `texto.title`,
  `texto.text` e `texto.button` com o seu texto como reserva (exemplo em
  `docs/PARA_IA.md`). Sem o ajuste, nada quebra: o bloco segue com o seu texto.
- `docs/openapi.yaml` atualizado (`TextoDaChamada`).

## 1.1.1

Sem migração. Faça um novo deploy do site; se o deploy do site não reinstalar a
biblioteca, rode no servidor
`pip install -U "publi-bot-core-django @ git+https://github.com/EduardoReolon/publi-bot-core-django@main"`
e reinicie (ver `docs/IMPLANTACAO.md`, "Atualizar").

- O sanitizador aceita `details` e `summary` (com `class` e `open` em
  `details`): é a lista de referências que o PubliBot põe no fim do artigo
  (`<details class="publibot-referencias">`). Antes as tags eram removidas e a
  lista aparecia sempre aberta, como texto comum.
- `docs/PARA_IA.md`: seção "Referências do artigo".
- `docs/IMPLANTACAO.md`: atualizar é um novo deploy do site, que reinstala a
  biblioteca de `@main` a cada vez; `pip install -U` à mão só se o deploy não fizer isso.

## 1.1.0

Rode `migrate`. Recomendado: `publibot_baixar_capas` num cron de hora em hora.

- A capa passa a ser baixada para o site (o contrato pede servir do próprio
  domínio): `artigo.capa_url`. Campos novos `cover_image` e `cover_image_sha256`.
- `{% publibot_head artigo %}`: title, description, canonical (o do próprio
  artigo), Open Graph e JSON-LD `Article`/`FAQPage`.
- `publibot_core.sitemaps.PublicationSitemap`, com `lastmod` real.
- `docs/SEO_DO_SITE.md`: para que o site existe e o que a página precisa ter.
- Corrigido o exemplo do PARA_IA que usava `canonical_source` como canonical
  (isso tiraria o artigo da busca).

## 1.0.0

Primeira versão como pacote, a partir da implementação de referência que vivia
no repositório do PubliBot (`publibot_node`).

- App `publibot_core` (antes `publibot_node`), tags `{% load publibot %}` e
  templates em `publibot/`.
- Models em inglês: `Publication` (antes `ReceivedPublication`),
  `VisitorQuestion` e `AuthorPhoto`. As tabelas internas (`DailyReading`,
  `Conversion` e `UsedNonce`) ficam em `publibot_core.models._internos`.
- Nonce contra reenvio no banco, e não mais no cache: vale com vários processos.
- Paginação por (data, id): antes, o cursor só pelo id podia pular linhas.
- Settings `PUBLIBOT_*` (saem os `PUBLIBOT_NODE_*`), com `PUBLIBOT_ARTICLE_PATH`
  e `PUBLIBOT_QA_PATH` para a URL de cada conteúdo.
- `Publication.objects.visiveis()`, `data_de_publicacao`, `foto_do_autor`
  (propriedade e tag).
- Comando `publibot_conferir` e `publibot_core.testing.cabecalhos_assinados`.
- Admin somente leitura para as publicações.
