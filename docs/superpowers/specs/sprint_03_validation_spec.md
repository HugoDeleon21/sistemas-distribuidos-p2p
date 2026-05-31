# Sprint 03 — Spec de Validação (Contrato Master-to-Master)

Objetivo
- Validar que a implementação em `master.py` e `worker.py` cumpre os contratos e regras descritos em `sprint_03_docs.md`.

Checklist de validação

1. request_help
- [ ] Mensagem enviada com `type: "request_help"` e `request_id` UUID v4
- [ ] Payload contém `master_id`, `master_address`, `current_load`, `capacity`, `workers_needed`
- [ ] Uso de conexão TCP Master-to-Master
- [ ] Timeout de 5 segundos aguardando resposta

2. response_accepted / response_rejected
- [ ] Resposta reutiliza o mesmo `request_id`
- [ ] `response_accepted` só é enviada quando houver Workers ociosos suficientes
- [ ] `response_rejected` cobre razões: `high_load`, `no_workers_available`, `refused`
- [ ] `worker_details` contém `id` e `address` reais ou `unknown` documentado

3. command_redirect
- [ ] Enviado Master→Worker pela conexão Master→Worker existente
- [ ] Campo `payload.new_master_address` presente
- [ ] Cada Worker acordado recebe um `command_redirect`

4. register_temporary_worker
- [ ] Worker envia `type: "register_temporary_worker"` ao novo Master
- [ ] Payload contém `worker_id` e `original_master_address`
- [ ] `request_id` é UUID v4
- [ ] Master registra o Worker como emprestado e responde com `STATUS: "ACK"`

5. Worker emprestado (runtime)
- [ ] Worker reconnecta e apresenta `ALIVE` com `SERVER_UUID` preenchido com o Master de origem
- [ ] Master entrega `QUERY` ou `NO_TASK` corretamente
- [ ] Worker reporta `STATUS` e recebe `ACK`

6. command_release
- [ ] Master emissor envia `command_release` com `payload.original_master_address`
- [ ] Worker fecha conexão e reconecta ao Master de origem

7. notify_worker_returned
- [ ] Master notificante envia `type: "notify_worker_returned"` via TCP
- [ ] Payload contém `worker_id`
- [ ] Master receptor atualiza estado (remove de `borrowed_workers`)

8. Saturação / histerese
- [ ] `current_load > capacity` dispara envio de `request_help`
- [ ] `current_load <= release_threshold` dispara `command_release` para emprestados
- [ ] `workers_needed` calculado proporcionalmente ao excedente (pelo menos 1)

9. Resiliência
- [ ] Mensagens com `type` desconhecido são logadas e ignoradas
- [ ] Desconexões não derrubam o processo
- [ ] Worker emprestado tenta reconectar ao `original_master_address` se perder conexão com Master emprestado

10. Observabilidade
- [ ] Logs Master-to-Master incluem `type`, `request_id`, `payload` e `timestamp`
- [ ] O sistema exibe contadores de Workers locais e emprestados ao alterar estado

Procedimento de verificação
- Executar uma execução controlada com dois Masters (porta 5000 e 5001) e ao menos um Worker por Master.
- Testar cenários CT01–CT09 descritos em `sprint_03_docs.md`.
- Registrar evidências (logs) para cada item marcado.

Resultados esperados
- Todos os itens marcados como obrigatórios devem passar; divergências devem ser documentadas e remediadas conforme o plano de correção.
