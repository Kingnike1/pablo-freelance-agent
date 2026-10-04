# Pablo Freelance Agent — MVP com painel web

Monitora duas fontes públicas de vagas remotas, filtra por palavras-chave, evita duplicatas com SQLite, oferece um painel web local e gera relatórios. Telegram e notificações no desktop são opcionais.

## Windows

1. Extraia o ZIP.
2. Abra o terminal na pasta `pablo_freelance_agent`.
3. Execute: `py -m pip install -r requirements.txt`.
4. Para usar o agente no terminal, execute: `py agent.py`.
5. Para abrir o painel web local, execute: `py web_app.py` e acesse <http://127.0.0.1:5000>.

No Linux/macOS, substitua `py` por `python3`. Edite `config.json` para ajustar palavras-chave e frequência. O padrão é 30 minutos. Deixe o computador ligado e o programa aberto.

## Painel web

O painel permite:

- visualizar as oportunidades salvas;
- pesquisar por título, empresa ou local;
- filtrar por fonte e localização;
- disparar uma atualização manual sem enviar notificações duplicadas;
- editar palavras-chave, termos excluídos e opções de notificação;
- abrir ou baixar relatórios HTML, CSV e JSON respeitando os filtros atuais.

O painel é local por padrão e não deve ser exposto diretamente à internet sem autenticação e uma camada de servidor adequada.

## Telegram opcional

Crie um bot com `@BotFather`, envie uma mensagem para ele, obtenha o chat ID e preencha `telegram_bot_token` e `telegram_chat_id` em `config.json`. Não compartilhe o token nem o inclua em controle de versão.

## Testes

Os testes não consultam a internet nem enviam notificações:

```bash
python -m unittest -v
```

## Correções desta versão

- Validação da configuração JSON, com preenchimento de campos ausentes pelos padrões.
- Tratamento de respostas inválidas, JSON malformado, timeout e falhas de rede.
- Normalização defensiva de anúncios incompletos e limpeza de entidades HTML.
- Limite de vagas aplicado ao total da busca, e não apenas a uma fonte.
- Uma única conexão SQLite por execução, com commit por consulta.
- Testes para filtros, deduplicação, limite global e configuração parcial.

## Limitações

Esta versão consulta Remotive e Arbeitnow; não monitora diretamente 99Freelas ou Workana. Pode encontrar vagas internacionais ou empregos, não apenas freelas. Confira se cada anúncio está aberto e se aceita candidatos no Brasil. Não envia candidaturas automaticamente. Respeite os termos das fontes.
