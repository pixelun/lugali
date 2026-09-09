# Localização real e avisos periódicos

## Comportamento aprovado

- Ao ativar, o app solicita notificações e localização em segundo plano.
- Enquanto ativo, recebe posições reais continuamente e identifica cidade, estado e país com a geocodificação da Apple.
- Após obter uma posição recente e confiável, mostra um aviso silencioso; os avisos seguintes ocorrem em intervalos mínimos de 10 minutos, mesmo dentro da mesma cidade.
- Se a posição estiver antiga, imprecisa ou sem geocodificação válida, o aviso aguarda a próxima leitura confiável em vez de exibir uma cidade possivelmente errada.
- O histórico registra somente mudanças de cidade.
- Ao desativar, o app encerra a localização e cancela avisos pendentes.

## Implementação mínima

- Usar `CLLocationManager` com atualizações em segundo plano, atividade de navegação automotiva e pausa automática desativada enquanto o recurso estiver ligado.
- Considerar somente coordenadas recentes e com precisão suficiente para identificar um município.
- Usar `CLGeocoder` para obter `locality`, `administrativeArea` e `country`.
- Controlar o intervalo de 10 minutos pelo horário do último aviso confirmado.
- Persistir a última cidade e o horário do último aviso para sobreviver à reabertura do app.
- Manter população fora desta versão.

## Limites aceitos

- O horário pode atrasar quando o sistema não entregar uma posição confiável.
- O uso contínuo de localização aumenta o consumo de bateria e pode exibir o indicador de localização do iOS.
- Encerrar o app à força ou desativar localização/notificações interrompe o funcionamento.

## Validação

- Testar o filtro de posição, o intervalo mínimo de 10 minutos, a repetição na mesma cidade e o registro único por mudança de cidade.
- Validar no iPhone com localização simulada pelo Xcode e depois em um deslocamento real.
