# Mudanças

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
