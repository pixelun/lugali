# Identidade Lugali

Data: 2026-09-07. Aprovada pelo gerente de produto. Este documento registra decisões já fechadas; não introduz marca nova.

## Promessa

Durante uma viagem, o app informa a cidade em que a pessoa está com um aviso nativo silencioso — cidade, estado ou província, e país — sem abrir o app nem interromper o áudio de Maps ou Waze. O nome e o símbolo falam desse instante de chegada em movimento, não de um mapa, um pino ou um horizonte de prédios.

## Nome

- **Público:** Lugali. Único nome visível na Springboard, no título da tela inicial, nas descrições de permissão de localização e nos textos dos App Intents.
- **Técnico:** permanece InTheCity para target, scheme, módulo Swift, nomes de arquivos, entitlements e `PRODUCT_NAME`. Bundle identifier: `com.pixelun.Lugali` (testes: `com.pixelun.LugaliTests`). A troca de bundle cria uma instalação distinta e reinicia dados e permissões.

## Símbolo

O ícone aprovado é o da proposta Lugiro:

- fundo azul-cobalto preenchendo o quadrado 1024×1024; o iOS aplica a máscara arredondada.
- arco circular grosso em creme quente, aberto do lado direito, com extremos arredondados.
- ponto amarelo-manga na abertura, atravessando o vão do arco.

Leitura pretendida: percurso, chegada e um sorriso sutil. Fonte vetorial: `docs/brand/lugali-icon.svg`. Raster do catálogo: `InTheCity/Assets.xcassets/AppIcon.appiconset/AppIcon.png`.

Proibido no símbolo: gradiente, sombra, pino, mapa, globo, prédios, texto, canal alpha.

## Paleta

| Papel | Hex | Uso |
|---|---|---|
| Cobalto | `#0B57F0` | acento e interruptor; fundo do ícone |
| Manga | `#FFC21C` | ponto do símbolo; não entra no cromado da interface |
| Branco | `#FFFFFF` | fundo da interface no modo claro |
| Cinza de cartão | `#F4F6F8` | fundo dos cards no modo claro |
| Hairline | `#E2E5E9` | contorno neutro no modo claro |
| Creme quente | `#FFF7E8` | arco do ícone; texto no modo escuro |
| Carvão | `#1C1C1E` | texto no modo claro |

Modo escuro: navy `#0B1528` no fundo e `#16263E` no cartão, da mesma família do cobalto. Acento no escuro: `#4D8CFF`, azul da mesma família com contraste de texto acessível sobre o navy. O interruptor permanece `#0B57F0` nos dois modos. No claro, o fundo é branco puro; cards e hairline usam cinza neutro, sem amarelo ou creme na interface. No escuro, texto secundário e hairline acompanham a família navy.

## Regras de uso

- Não substituir Lugali por In The City, InTheCity ou CityWatch em texto visível ao usuário.
- Não aplicar o pino verde anterior como ícone do app.
- Não usar manga como cor de acento, botão ou interruptor.
- Não reconstruir telas para “expressar” a marca; só paleta, nome visível e ícone.
- Manter o ícone opaco, RGB, 1024×1024. Elementos do símbolo cabem na área segura da máscara iOS; o azul vai de borda a borda.
- Não renomear tipos, targets, schemes, arquivos de entitlements, `PRODUCT_NAME` nem o módulo Swift. O bundle visível ao sistema é `com.pixelun.Lugali`.

## Superfícies alteradas nesta aplicação

- `HomeView` — título de navegação.
- `Info.plist` — `CFBundleDisplayName` e textos de permissão de localização.
- `AutomationIntents.swift` — descrições e diálogos. O tipo `InTheCityShortcuts` permanece.
- `Theme.swift` e `AccentColor.colorset`.
- `AppIcon.appiconset/AppIcon.png`, a partir de `docs/brand/lugali-icon.svg`.
- Notas pontuais em `docs/grok-brief.md` e `docs/screenshots/VALIDACAO.md`, só onde ainda afirmavam que o nome ou o ícone antigos continuavam aprovados.

## Identificadores técnicos

| Identificador | Valor |
|---|---|
| Projeto / target / scheme | `InTheCity` |
| Módulo Swift | `InTheCity` |
| `@main` | `InTheCityApp` |
| Bundle id | `com.pixelun.Lugali` |
| Bundle id de testes | `com.pixelun.LugaliTests` |
| Entitlements | `InTheCity/InTheCity.entitlements` |
| PRODUCT_NAME | `InTheCity` |
| Logger subsystem | `com.pixelun.Lugali` |

Não faz parte desta alteração: frequência de aviso, GPS, histórico, signing ou publicação.
