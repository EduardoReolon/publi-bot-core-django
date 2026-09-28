# Para a IA que mantém este repositório

Este pacote é o lado do SITE no contrato PubliBot `/api/v1`. O outro lado (o
cliente que chama estas rotas) está em EduardoReolon/publi-bot, em
`apps/integrations/client.py`, e o contrato em `docs/contrato/` de lá.

- **O contrato manda.** Mudança de rota, campo ou regra de assinatura começa no
  `openapi.yaml` do publi-bot; copie para `docs/openapi.yaml` aqui e
  implemente. Os testes de contrato do publi-bot (`tests_contrato/`) instalam
  ESTE pacote e exercitam os dois lados por HTTP.
- **Qualquer banco.** Nada de campo, função ou consulta só do Postgres
  (ArrayField, SearchVector, `distinct` por campo...). O CI roda SQLite,
  PostgreSQL e MySQL.
- **O site vê três models:** `Publication`, `VisitorQuestion` e `AuthorPhoto`.
  Tabela nova que o site não usa vai para `models/_internos.py`, fora do
  `__all__` e do admin.
- **Documentação junto com o código:** o que o site usa está em
  `docs/PARA_IA.md`; como instalar, em `docs/IMPLANTACAO.md`; para que o site
  existe e as regras de SEO, em `docs/SEO_DO_SITE.md`. Campo novo em
  model público entra na tabela do PARA_IA no mesmo commit.
- **Versão:** `publibot_core/__init__.py::__version__` e uma entrada no
  `CHANGELOG.md` a cada mudança. O site atualiza com
  `pip install -U ...@main` e `migrate`: migração que precisa de algo além disso
  é dita no CHANGELOG.
- Testes: `pip install -e ".[dev]" && pytest` (SQLite em memória).
  `BANCO=postgres` ou `BANCO=mysql` com `DB_*` para os outros bancos.
