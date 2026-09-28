# O site que recebe o PubliBot: para que ele existe e o que ele precisa ter

Leia antes de desenhar ou mudar o site. Vale para uma pessoa e para uma IA.

## Para que serve este site

Ele existe para **ser achado no Google e converter quem chega**. O PubliBot
escreve artigos a partir de buscas reais (o que as pessoas perguntam), com
fontes conferidas, e os manda para cá. O site transforma cada artigo numa
página que:

1. o Google entende e mostra bem (esta página de regras);
2. a pessoa lê até o fim (texto limpo, rápido, sem distração);
3. leva à oferta do negócio, sem forçar (o bloco da chamada);
4. mede o que aconteceu, para o PubliBot aprender quais temas vendem
   (o `leitura.js`).

Tudo o que atrapalha uma dessas quatro coisas atrapalha o motivo de o site
existir: pop-up na entrada, página lenta, texto escondido atrás de clique,
anúncio no meio do artigo.

## Obrigatório na página do artigo

| O quê | Como |
|---|---|
| `<title>`, description, canonical, Open Graph, JSON-LD | `{% publibot_head artigo %}` dentro do `<head>`. |
| Um único `<h1>` | `{{ artigo.title }}`. O corpo já começa em `<h2>`. |
| Autor visível, com credencial | `author_name` e `author_credentials`, com foto (`{% foto_do_autor artigo %}`). Idealmente um link para a página do autor. |
| Datas visíveis | Publicado em `data_de_publicacao`; "Atualizado em" `data_de_atualizacao` quando `version > 1`. |
| Perguntas frequentes | `artigo.faq`, visíveis na página (o JSON-LD `FAQPage` já vai no head). |
| Aviso de produção | `content_disclosure`, quando vier. |
| "Leia também" | `{% leia_tambem artigo %}`: links comuns, no HTML (não carregados por script). |
| Medição | `data-publibot-id` no `<article>` e o `leitura.js` (ver PARA_IA). |

## Erros que tiram o artigo do Google

- **`canonical_source` no `<link rel="canonical">`.** Esse campo é a FONTE
  citada (o estudo, a tabela). Como canonical, ele diz ao Google que o
  artigo é cópia da fonte, e o artigo some da busca. O canonical é sempre o
  endereço do próprio artigo; o `publibot_head` já faz certo.
- **Mudar o endereço de um artigo publicado** sem redirecionar (301) o
  antigo. O endereço acumula posição; perdê-lo é recomeçar do zero.
- **`noindex`** esquecido de um ambiente de teste, ou `robots.txt`
  bloqueando `/blog/`.
- **Mostrar o corpo com JavaScript** (carregar o texto depois, por API). O
  Google até executa, mas mais tarde e nem sempre. O HTML tem de vir pronto.
- **`<meta name="keywords">`**: o Google ignora desde 2009. Não precisa.

## O site inteiro

- **Sitemap** com todas as páginas, e `lastmod` real:
  `publibot_core.sitemaps.PublicationSitemap` cobre os artigos (ver
  IMPLANTACAO). Envie o endereço no Search Console.
- **Search Console** verificado para o domínio. É por ele que o PubliBot vê
  cliques e posições (a conta de serviço do PubliBot precisa de acesso).
- **HTTPS** em tudo, e um só domínio (com ou sem `www`, o outro redireciona).
- **Rápido no celular** (Core Web Vitals): imagens com `width`/`height`,
  `loading="lazy"` abaixo da dobra, CSS e fontes enxutos. As imagens do
  PubliBot já chegam em WebP.
- **Página de autor** (`/autores/<nome>/`) com a biografia e as credenciais,
  e o nome no artigo ligando para ela. Para temas de saúde, dinheiro e
  jurídico, o Google pesa muito quem escreve e a experiência que tem.
- **Página "sobre" e contato** reais. Um site sem dono aparente perde
  confiança.
- **Lista do blog** com links comuns para cada artigo (paginação por link,
  não só "carregar mais" por script).
- **Breadcrumb** (Início › Blog › Artigo) ajuda o Google a entender a
  estrutura; opcional.

## A chamada para a oferta

O bloco é do site (template `publibot/chamada.html`). O PubliBot só decide
**se** e **onde** ele entra: no fim, no meio (depois da seção que trata do
que a oferta resolve) ou em nenhum lugar (tema longe da oferta). Um bloco
curto, com uma frase e um botão, converte mais que um banner. Mantenha
`data-publibot-bloco` e `data-publibot-conversao` (é a medição).
