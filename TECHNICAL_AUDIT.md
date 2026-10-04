
## Correções aplicadas após a auditoria

Nesta primeira fase foram corrigidos:

- gravação atômica e validação prévia de `config.json`, com permissões `0600` ao salvar;
- `busy_timeout` e WAL para SQLite em arquivo;
- `rollback` explícito em falhas de coleta;
- commit do anúncio antes do envio de notificações;
- validação de URLs para aceitar somente `http` e `https`;
- parsing de valores monetários comuns, incluindo formatos brasileiro, internacional e intervalos;
- correspondência de palavras com limites para reduzir falsos positivos;
- relatórios completos sem truncamento silencioso em 500 linhas;
- ocultação do token Telegram no HTML e preservação do token quando o campo fica vazio;
- testes ampliados para 17 casos, incluindo URL insegura, configuração inválida, moedas e token oculto.

Continuam como próximas etapas: adaptadores independentes por fonte, status/histórico de oportunidades, versionamento e recálculo do score, retry/backoff com logs, serviço supervisionado e autenticação caso o painel deixe de ser exclusivamente local.
