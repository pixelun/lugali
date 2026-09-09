# Validação — etapa 1 (correção de entrega)

Nota (2026-09-07): a identidade pública vigente é Lugali, com o símbolo azul da proposta Lugiro. Este registro descreve a validação da etapa 1 com o nome e o ícone anteriores. Ver `docs/plans/2026-09-07-lugali-brand-design.md` e `docs/screenshots/04-lugali-home.png`.

Data: 2026-09-06. Simulator: iPhone 16 Pro, iOS 18.6 (`EF744CE4-26F6-4C38-955A-6BBEEA5B98D0`). Capturas via `xcrun simctl io screenshot` (LCD do Simulator). Sem Orca. Sem alteração de permissões globais do macOS.

## Ícone

Aplicado o arquivo aprovado `docs/icon-proposals/inthecity-pin-proposal.png` em `InTheCity/Assets.xcassets/AppIcon.appiconset/AppIcon.png`. Arte inalterada; apenas redimensionada de 1254×1254 RGB (sem alpha) para o slot 1024×1024 do App Icon. Visível na Springboard como **In The City** em `03-springboard-icon.png`.

## Screenshots reais

| Arquivo | O que mostra |
|---|---|
| `01-home-demo.png` | Tela principal. Interruptor ligado. Status: *Ativado para simulação. GPS real ainda não está neste app.* Local atual · simulação: Puerto Iguazú. População fictícia. Painel Simulação visível. Histórico: 3 cidades. |
| `02-history-demo.png` | Histórico recapturado após correção de alinhamento (2026-09-06 15:51). Título, aviso de dados fictícios, linhas e separadores no mesmo eixo lateral. Mais recente primeiro. Cada linha com *Simulação* e população fictícia. |
| `03-springboard-icon.png` | Springboard do Simulator com o ícone In The City. Extra para evidenciar o ícone; não é captura de banner. |

Estado de demonstração carregado só em Debug, com argumentos `-DemoScreenshots` e `-DemoShowHistory`. Não é GPS real. Não entra no binário Release.

Na Springboard deste Simulator ainda aparece um ícone **CityWatch** de instalação anterior, alheia a este projeto.

## Build e testes

```bash
xcodebuild -project InTheCity.xcodeproj -scheme InTheCity \
  -destination 'platform=iOS Simulator,id=EF744CE4-26F6-4C38-955A-6BBEEA5B98D0' \
  -derivedDataPath /tmp/InTheCity-derived CODE_SIGNING_ALLOWED=NO test
```

**TEST SUCCEEDED.** 8 testes: os 5 fluxos originais, proteção contra sobrescrever histórico corrompido, desligamento durante autorização assíncrona e falha ao agendar notificação sem criar histórico.

O build **Release** também foi concluído com sucesso. Os nomes e textos das cidades simuladas não aparecem no executável, e o pacote contém a versão `0.1.0` (build `1`).

## Não validado

**Banner silencioso em segundo plano (Maps/Waze): não observado.** Não está aprovado. Mostrar o diálogo de notificação e o banner sobre outro app exige toque humano. Computer Use do Orca pediu Acessibilidade do macOS; essa permissão global não foi alterada.

## Bloqueio de ferramenta (contornado só no destino do arquivo)

`simctl io screenshot` recusou gravar direto em `/Volumes/KINGSTON/app-in-the-city/docs/screenshots` (`NSPOSIXErrorDomain` 1, Operation not permitted). Captura feita em `/tmp/inthecity-screens` e copiada para `docs/screenshots`. As PNG são as mesmas geradas pelo simctl.

## Reprodução das capturas (Debug)

```bash
xcrun simctl launch --terminate-running-process EF744CE4-26F6-4C38-955A-6BBEEA5B98D0 com.pixelun.InTheCity -DemoScreenshots
# tela principal

xcrun simctl launch --terminate-running-process EF744CE4-26F6-4C38-955A-6BBEEA5B98D0 com.pixelun.InTheCity -DemoScreenshots -DemoShowHistory
# histórico
```
