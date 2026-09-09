# Plano de implementação — localização real

1. **Permissões e capacidade**
   - Adicionar as descrições de uso de localização ao `Info.plist`.
   - Habilitar `UIBackgroundModes/location`.

2. **Serviço de localização**
   - Criar um único `LocationService` baseado em `CLLocationManager` e `CLGeocoder`.
   - Solicitar autorização adequada, iniciar/parar atualizações e aceitar somente coordenadas recentes e com precisão horizontal suficiente.
   - Manter atualizações em segundo plano enquanto o interruptor estiver ligado.

3. **Regra dos avisos**
   - Converter uma coordenada válida em cidade, estado e país.
   - Avisar imediatamente na primeira localização válida.
   - Depois, avisar novamente apenas quando tiverem passado pelo menos 10 minutos e houver uma localização válida atualizada, inclusive na mesma cidade.
   - Registrar no histórico somente quando a cidade mudar.

4. **Estado persistente e interface**
   - Persistir a última cidade real e o horário do último aviso.
   - Exibir a interface funcional nos builds Debug e Release.
   - Manter o painel de simulação somente em Debug e indicar claramente o estado das permissões.

5. **Verificação**
   - Testar a regra de 10 minutos e a deduplicação do histórico.
   - Compilar Debug e Release.
   - Assinar com a equipe pessoal temporária, instalar no iPhone e validar a primeira localização real e o primeiro aviso.

Não inclui população, servidor, conta de usuário ou API externa.
