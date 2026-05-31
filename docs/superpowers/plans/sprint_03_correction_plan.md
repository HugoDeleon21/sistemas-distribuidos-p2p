# Sprint 03 — Plano de Correção Detalhado

Objetivo
- Executar as correções necessárias para que `master.py` e `worker.py` cumpram integralmente o contrato Sprint 03.

Prioridade Alta

1. Validar e rejeitar `request_help` quando não houver Workers ociosos
   - Implementar verificação de Workers ociosos antes de aceitar
   - Enviar `response_rejected` com `reason: "no_workers_available"` quando aplicável

2. Corrigir `worker_details.address`
   - Preencher `worker_details.address` com o endereço real do Worker (`host:port`) quando possível
   - Se não for possível obter, documentar explicitamente o placeholder como `unknown`

3. Padronizar `request_id` como UUID v4
   - Substituir geradores inteiros (random.randint) por `str(uuid.uuid4())` no `worker.py` e validar em `master.py`

4. Implementar fallback do Worker emprestado
   - Se o Worker perder conexão com o Master emprestado, tentar reconectar ao `original_master_address` antes de iniciar eleição

Prioridade Média

5. Tornar consistente o registro de Workers emprestados
   - Garantir que `borrowed_workers` e `workers_na_farm` sejam sincronizados e que os contadores sejam atualizados

6. Robustecer `notify_worker_returned`
   - Manter o Worker listado como emprestado até confirmação de retorno
   - Implementar retry limitado na notificação ao Master original

7. Centralizar logs Master-to-Master
   - Função `log_master_event` que inclui `timestamp`, `type`, `request_id` e `payload`

Prioridade Baixa

8. Validar campos obrigatórios em todas as mensagens Master-to-Master
   - `request_help`, `register_temporary_worker`, `command_release` devem falhar graciosamente com log quando faltarem campos

9. Adicionar testes de aceitação
   - Scripts ou instruções para reproduzir CT01–CT09 e coletar logs

10. Documentar mudanças
   - Atualizar `sprint_03_docs.md` se a implementação introduzir campos adicionais ou placeholders documentados

Plano de execução (ordem e estimativa)
- Passo 1 (2–3 horas): Padronizar UUIDs e ajustar `register_temporary_worker` no `worker.py`.
- Passo 2 (2–4 horas): Ajustar `master.py` para validar `request_help` e selecionar Workers disponíveis.
- Passo 3 (2–3 horas): Implementar fallback do Worker emprestado e confirmar reconexão ao Master original.
- Passo 4 (1–2 horas): Melhorar logs e contadores, adicionar retries em `notify_worker_returned`.
- Passo 5 (2–4 horas): Testes de aceitação automatizados / scripts manuais.

Critérios de aceitação
- Todos os itens do arquivo `docs/superpowers/specs/sprint_03_validation_spec.md` marcados como obrigatórios estão implementados e validados.
- Testes CT01–CT09 passam em ambiente controlado.
- Logs mostram `request_id` e `timestamp` para todas as trocas Master-to-Master.

Próximos passos sugeridos
- Executar testes manuais locais com dois Masters e múltiplos Workers.
- Commitar mudanças e abrir Pull Request com descrição das alterações e evidências de logs.
