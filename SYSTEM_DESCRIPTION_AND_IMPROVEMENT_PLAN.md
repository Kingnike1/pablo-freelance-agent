# Pablo Freelance Agent — descrição do sistema e modelo de melhorias

**Versão documentada:** commit `5bc4ace`  
**Repositório:** [Kingnike1/pablo-freelance-agent](https://github.com/Kingnike1/pablo-freelance-agent)  
**Status:** MVP funcional com agente de monitoramento, painel web local, relatórios e diagnóstico de configuração.

---

## 1. Objetivo do sistema

O Pablo Freelance Agent ajuda a descobrir oportunidades remotas na área de tecnologia. Ele consulta fontes públicas, aplica filtros configuráveis, evita duplicatas e apresenta as vagas no terminal ou em um painel web local.

O sistema é uma ferramenta de apoio à busca. Ele **não envia candidaturas automaticamente**, não negocia com clientes e não substitui a avaliação manual da oportunidade.

---

## 2. Funcionalidades existentes

### Monitoramento de vagas

- Consulta a fonte **Remotive**.
- Consulta a fonte **Arbeitnow**.
- Busca periódica com intervalo configurável.
- Filtragem por palavras-chave.
- Exclusão por termos indesejados, como `senior`, `lead` e `principal`.
- Limite de novas oportunidades por ciclo.
- Tratamento de respostas inválidas e falhas de rede.

### Controle de duplicidade

- Armazena oportunidades em um banco SQLite local.
- Usa um identificador combinado de fonte e vaga.
- Não exibe novamente uma vaga já registrada.

### Notificações

- Exibição no terminal.
- Notificação no desktop, quando disponível.
- Telegram opcional, caso `telegram_bot_token` e `telegram_chat_id` sejam configurados.

### Painel web local

Arquivo: `web_app.py`

Endereço padrão:

```text
http://127.0.0.1:5000
```

O painel permite:

- visualizar oportunidades salvas;
- pesquisar por título, empresa ou localização;
- filtrar por fonte e localização;
- atualizar a busca manualmente;
- editar as configurações;
- abrir os links originais das oportunidades;
- baixar relatórios nos formatos HTML, CSV e JSON.

### Relatórios

Rotas disponíveis:

```text
/reports/html
/reports/csv
/reports/json
```

Os relatórios respeitam os filtros enviados na URL, por exemplo:

```text
/reports/csv?q=python&source=Remotive&location=remote
```

### Diagnóstico e execução simplificada

Arquivo: `start.py`

```bash
python start.py          # abre o painel web
python start.py web      # abre o painel web explicitamente
python start.py agent    # inicia o monitor no terminal
python start.py check    # mostra a configuração preenchida ou faltante
```

O comando `check` não mostra tokens ou outros valores sensíveis.

---

## 3. Estrutura atual do projeto

```text
pablo_freelance_agent/
├── agent.py                         # núcleo do monitoramento e filtros
├── web_app.py                       # servidor Flask e rotas web/API
├── start.py                         # lançador e diagnóstico de configuração
├── config.json                      # configuração do usuário
├── requirements.txt                 # dependências Python
├── opportunities.sqlite3            # banco local gerado em execução
├── templates/
│   ├── index.html                   # painel principal
│   ├── config.html                  # tela de configuração
│   └── report.html                  # relatório HTML imprimível
├── test_agent.py                    # testes do núcleo
├── test_web.py                      # testes da interface e relatórios
├── test_start.py                    # testes do lançador e diagnóstico
├── README.md                        # instruções rápidas
└── .gitignore                       # proteção contra banco, caches e segredos
```

O arquivo `opportunities.sqlite3` é criado automaticamente e não deve ser enviado ao GitHub. Ele está protegido pelo `.gitignore`.

---

## 4. Fluxo de funcionamento

```text
1. O usuário inicia start.py, agent.py ou web_app.py
2. O sistema carrega e valida config.json
3. O agente consulta Remotive e Arbeitnow
4. Cada anúncio é normalizado para um formato comum
5. Título e descrição são comparados com os filtros
6. Termos excluídos removem anúncios incompatíveis
7. O SQLite verifica se a oportunidade já foi registrada
8. Novas oportunidades são salvas
9. O resultado é exibido no terminal, painel ou relatório
10. O ciclo se repete após o intervalo configurado
```

---

## 5. Configuração atual

Arquivo: `config.json`

| Campo | Função | Estado padrão |
|---|---|---:|
| `check_every_minutes` | Intervalo entre consultas | `30` |
| `max_results_per_check` | Máximo de novas vagas por ciclo | `15` |
| `keywords_any` | Termos que tornam a vaga elegível | 12 termos |
| `exclude_keywords` | Termos que eliminam a vaga | 4 termos |
| `telegram_bot_token` | Token do bot Telegram | vazio/opcional |
| `telegram_chat_id` | Destino das mensagens Telegram | vazio/opcional |
| `desktop_notifications` | Alertas no computador | `true` |

O diagnóstico atual indica que a configuração básica está pronta. O Telegram é a única parte opcional ainda não configurada.

---

## 6. Como executar

### Instalação

```bash
python3 -m pip install -r requirements.txt
```

No Windows:

```bash
py -m pip install -r requirements.txt
```

### Painel web

```bash
python start.py
```

### Monitor no terminal

```bash
python start.py agent
```

### Diagnóstico

```bash
python start.py check
```

### Testes

```bash
python3 -m unittest -v
```

---

## 7. Estado de qualidade atual

Validações já realizadas:

- **10 testes automatizados aprovados**.
- Compilação dos módulos Python aprovada.
- APIs públicas verificadas com resposta JSON válida.
- Painel web validado com HTTP 200.
- Rotas HTML, CSV, JSON, API e saúde verificadas.
- Repositório GitHub privado sincronizado com a branch `main`.
- Tokens do Telegram ausentes da configuração versionada.

---

## 8. Limitações conhecidas

1. O sistema depende da disponibilidade e do formato das APIs públicas.
2. Não há garantia de que todas as vagas disponíveis sejam encontradas.
3. O filtro atual usa correspondência simples de texto, sem pontuação de compatibilidade.
4. O sistema não diferencia perfeitamente freelance, emprego fixo, contrato e projeto pontual.
5. Não existem filtros específicos por orçamento, moeda, idioma ou país.
6. O painel é local e não possui autenticação.
7. O banco SQLite é local e não possui sincronização entre computadores.
8. Não há histórico de status como `nova`, `revisada`, `favorita`, `candidatada` ou `descartada`.
9. Não existe agendamento como serviço do sistema operacional.
10. O Telegram só funciona quando as duas credenciais são preenchidas corretamente.

---

# Modelo para registrar melhorias do sistema

Use o modelo abaixo para descrever cada nova melhoria antes de implementá-la. A ideia é explicar **o problema**, **o comportamento desejado**, **como saberemos que funcionou** e **qual será o impacto**.

## Modelo curto

```markdown
# Melhoria: [nome curto]

## Problema
[O que está difícil, incompleto ou causando perda de tempo?]

## Objetivo
[Qual resultado concreto a melhoria deve produzir?]

## Usuário afetado
[Quem usará ou será beneficiado pela mudança?]

## Comportamento esperado
- [Comportamento 1]
- [Comportamento 2]
- [Comportamento 3]

## Arquivos ou áreas envolvidas
- `[arquivo ou módulo]` — [responsabilidade]

## Critérios de aceitação
- [ ] [Condição observável 1]
- [ ] [Condição observável 2]
- [ ] [Condição observável 3]

## Riscos e cuidados
- [Risco, dependência ou dado sensível]

## Testes necessários
- [Teste que deve ser executado]

## Status
- [ ] Planejada
- [ ] Em desenvolvimento
- [ ] Testada
- [ ] Publicada no GitHub
```

## Exemplo preenchido

```markdown
# Melhoria: pontuação de compatibilidade das vagas

## Problema
Hoje as vagas são filtradas por palavras-chave, mas aparecem sem ordem de prioridade. O usuário precisa ler muitas oportunidades para encontrar as mais adequadas.

## Objetivo
Calcular uma pontuação de 0 a 100 para ordenar as vagas por compatibilidade com o perfil configurado.

## Usuário afetado
Pessoa que busca trabalhos freelance ou remotos em desenvolvimento web e Python.

## Comportamento esperado
- Cada palavra-chave encontrada soma pontos à vaga.
- Termos presentes no título valem mais do que termos presentes apenas na descrição.
- Termos excluídos continuam removendo a oportunidade.
- O painel mostra a pontuação e permite ordenar da maior para a menor.
- O relatório CSV inclui uma coluna `score`.

## Arquivos ou áreas envolvidas
- `agent.py` — cálculo da pontuação durante a normalização.
- `web_app.py` — ordenação e filtro por pontuação.
- `templates/index.html` — exibição visual do score.
- `test_agent.py` — testes do cálculo.
- `test_web.py` — teste de ordenação no painel.

## Critérios de aceitação
- [ ] Toda nova vaga recebe uma pontuação entre 0 e 100.
- [ ] Uma vaga com termo no título pontua acima de uma vaga com o mesmo termo apenas na descrição.
- [ ] O filtro por termos excluídos continua funcionando.
- [ ] O score aparece no painel e nos relatórios.
- [ ] Os testes antigos continuam passando.

## Riscos e cuidados
- A pontuação é uma indicação, não uma garantia de qualidade.
- A regra deve ser documentada para evitar falsa precisão.
- Nenhum dado privado deve ser enviado para serviços externos.

## Testes necessários
- Testar vaga sem palavras-chave.
- Testar vaga com termo no título.
- Testar vaga com vários termos.
- Testar vaga com termo excluído.
- Testar relatório CSV com a nova coluna.

## Status
- [x] Planejada
- [ ] Em desenvolvimento
- [ ] Testada
- [ ] Publicada no GitHub
```

---

## 9. Melhorias recomendadas por prioridade

### Prioridade alta

1. **Persistência de status das vagas**: favorita, revisada, descartada e candidata.
2. **Pontuação de compatibilidade** para ordenar as melhores oportunidades.
3. **Filtros por país, idioma, orçamento e tipo de contrato**.
4. **Melhor tratamento de falhas de API**, incluindo registro de logs e retentativas controladas.

### Prioridade média

5. Histórico de consultas e quantidade de vagas por fonte.
6. Exportação de relatórios com resumo e estatísticas.
7. Configuração de fontes diretamente pelo painel.
8. Paginação e ordenação avançada no painel.
9. Backup e restauração do banco SQLite.

### Prioridade baixa

10. Autenticação para acesso remoto seguro.
11. Serviço para iniciar automaticamente com o sistema operacional.
12. Integração com novas fontes, respeitando os termos de uso.
13. Rascunhos de propostas personalizados, sempre exigindo revisão manual.

---

## 10. Regra para futuras alterações

Toda nova melhoria deve:

1. ter um problema claramente descrito;
2. definir comportamento observável;
3. incluir critérios de aceitação;
4. possuir testes quando alterar lógica ou dados;
5. evitar o envio de credenciais para o repositório;
6. atualizar o `README.md` ou este documento quando mudar o uso do sistema;
7. ser publicada em um commit identificado no GitHub privado.
