<!-- Cabeçalho -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=100&color=0:000000,100:8323b5&section=header&text=%E2%8B%86%CB%9A%CB%96%C2%B0Bot%20de%20Vagas%20TI%E2%8B%86%CB%9A%CB%96%C2%B0&fontSize=18&fontColor=deaaf9&fontAlignY=34" alt="Bot de Vagas TI"/>

<!-- Seção: Visão Geral -->
<div align="center">
  <font size="4" color="#8323B5"><b>⋆.˚✮𖹭✮˚.⋆ VISÃO GERAL ⋆.˚✮𖹭✮˚.⋆</b></font>
</div>

<br>

<div align="center">
  <samp>
    Monitoramento de vagas de estágio e de início de carreira em TI em fontes públicas,<br>
    com filtro por perfil, classificação de 1 a 5 estrelas<br>
    e notificação no Telegram separada por tipo de vaga.
  </samp>
</div>

<br>

<!-- Ferramentas utilizadas (imagem) -->
<div align="center">
  <img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=deaaf9" alt="Python" />
  <img src="https://img.shields.io/badge/GitHub_Actions-000000?style=for-the-badge&logo=githubactions&logoColor=deaaf9" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/Telegram_Bot_API-000000?style=for-the-badge&logo=telegram&logoColor=deaaf9" alt="Telegram Bot API" />
  <img src="https://img.shields.io/badge/status-em_produção-8323B5?style=for-the-badge" alt="Status: em produção" />
</div>

<br>

## ⋆˚✮ Contexto

Vagas de estágio em TI ficam distribuídas em vários portais, cada um com a sua
própria busca, e muitas encerram as inscrições em poucos dias. O Bot de Vagas TI
consulta essas fontes a cada 30 minutos durante o dia, aplica os critérios de área, nível,
local e modalidade, e envia pelo Telegram apenas as vagas novas, já ordenadas
por relevância e prazo de inscrição.

## ⋆˚✮ Funcionalidades
| Funcionalidade | Descrição |
| :--- | :--- |
| Coleta em várias fontes | Vitrine do CIEE, portal da Gupy, busca pública do LinkedIn e site de carreiras de uma empresa prioritária caso tenha preferências |
| Filtro por perfil | Área desejada, nível de entrada e exclusão de vagas indesejadas |
| Regra de local | Vagas remotas de qualquer cidade, respeitando exigência de residência; híbridas apenas na cidade base |
| Prazo de inscrição | Mantém somente processos com inscrição aberta e informa quantos dias faltam |
| Classificação | Nota de 1 a 5 estrelas por empresa, aderência ao perfil e nível da vaga |
| Três canais | Bots separados para estágios, empresa prioritária e vagas de TI que não são estágio |
| Resumo diário | Vagas do dia agrupadas por estrelas e lembrete das que encerram em até 3 dias |
| Aviso único | Cada vaga é notificada uma vez; anúncios duplicados são unificados |

## ⋆˚✮ Destaques técnicos
- **Coleta por APIs públicas** — as fontes são consultadas pelas mesmas APIs
  JSON que os próprios portais utilizam, em vez de automação de navegador,
  o que torna cada execução leve e rápida.
- **Validação de prazo pelo cronograma** — a data de fim da inscrição é
  conferida diretamente no cronograma de cada processo seletivo, além do
  status informado pela fonte.
- **Filtro com pesos distintos** — termos amplos contam apenas no título;
  na descrição, a vaga precisa citar vários termos técnicos diferentes.
  O casamento é feito por palavra, com termos curtos exigindo palavra inteira.
- **Histórico fora do repositório** — as vagas já avisadas ficam no cache do
  GitHub Actions, e os logs públicos registram apenas contagens.
- **Configuração sensível isolada** — tokens, cidade base e empresa
  prioritária ficam em variáveis de ambiente e nos Secrets do GitHub.
- **Envio resiliente** — retentativa com espera progressiva em quedas de
  conexão, respeito ao limite de taxa do Telegram e divisão automática de
  mensagens longas.
- **Frequência controlada por fonte** — pausa entre requisições em todas as
  fontes e intervalo mínimo de 3 horas entre buscas no LinkedIn.

## ⋆˚✮ Aprofundamento do Projeto

### ✮ Como funciona

```text
Dispara a cada 30 minutos, das 7h às 18h, pelo GitHub Actions
│
├─ Restaura o histórico de vagas já avisadas
│
├─ Coleta as vagas abertas em cada fonte ativa
│
├─ Aplica os critérios de perfil
│   ├─ Empresa bloqueada ou vaga exclusiva  → descarta
│   ├─ Vaga remota                          → aceita, exceto se exigir residir em outra cidade
│   ├─ Vaga híbrida                         → aceita apenas na cidade base
│   ├─ Vaga presencial                      → descarta, exceto da empresa prioritária
│   └─ Área fora do perfil                  → descarta
│
├─ Atribui de 1 a 5 estrelas e ordena por estrelas e prazo
│
├─ Envia as vagas ainda não avisadas ao bot correspondente
│   ├─ Empresa prioritária  → bot de prioridade
│   ├─ Estágio              → bot de estágios
│   └─ Trainee e júnior     → bot de vagas de TI
│
├─ Salva o histórico atualizado
│
└─ Às 18h, executa a última busca e envia a cada bot o resumo do dia e as vagas que encerram em até 3 dias
```

### ✮ Pré-Requisitos

⋆˚✮ Antes de começar, você vai precisar de:

| Ferramenta | Motivo |
| :--- | :--- |
| Conta no GitHub | Execução agendada pelo GitHub Actions |
| Bot do Telegram | Criado pelo @BotFather, para receber as notificações |
| Python 3.10+ e Git | Apenas para execução local |

### ✮ Configuração

#### ⋆ Passo a passo para usar

⋆˚✮ A busca e o resumo são executados pelo GitHub Actions, sem depender de uma
máquina ligada:

| Passo | Ação |
| :--- | :--- |
| 1 | Fazer um fork deste repositório |
| 2 | Cadastrar cada variável da tabela de Configuração ENV em **Settings → Secrets and variables → Actions** |
| 3 | Na aba **Actions**, habilitar os workflows do fork e executar o workflow manualmente com a opção `marcar_atuais_como_vistas`, que registra as vagas já abertas sem enviá-las |
| 4 | A partir daí, a busca é executada a cada 30 minutos entre 7h e 18h, seguida do resumo diário |

#### ⋆ Horários de execução

⋆˚✮ O GitHub Actions agenda em UTC. Os horários do workflow
`.github/workflows/vagas.yml` correspondem a:

| Horário de Brasília | Horário no workflow (UTC) | Ação |
| :--- | :--- | :--- |
| 7h às 17h30, a cada 30 minutos | `*/30 10-20 * * *` | Busca de vagas novas |
| 18h05 | `5 21 * * *` | Última busca do dia, seguida do resumo diário |
| 18h às 7h | — | Sem execução; vagas publicadas nesse intervalo são avisadas às 7h |

Para alterar os horários, some 3 horas ao horário de Brasília e edite as
linhas `cron` do workflow.

#### ⋆ Execução local (opcional)

⋆˚✮ Para testar e ajustar os filtros antes de ativar o agendamento:

```bash
# Clone este repositório
$ git clone https://github.com/Rhebecca-Taih/vagas-bot.git

# Acesse a pasta do projeto no terminal
$ cd vagas-bot

# Instale as dependências
$ python -m venv .venv
$ .venv/bin/pip install -r requirements.txt

# Execute uma busca de vagas
$ .venv/bin/python executar/buscar_vagas.py

# Envie o resumo do dia
$ .venv/bin/python executar/enviar_resumo.py
```

#### ⋆ Configuração ENV

⋆˚✮ No GitHub Actions, cada variável é cadastrada como Secret. Na execução local,
copie `configuracao/env.exemplo` para `configuracao/sensivel/.env` e preencha com
os dados reais.

| Variável | O que controla |
| :--- | :--- |
| `TELEGRAM_ESTAGIO_BOT_TOKEN` / `_CHAT_ID` | Bot que recebe as vagas de estágio (obrigatório) |
| `TELEGRAM_PRIORIDADE_BOT_TOKEN` / `_CHAT_ID` | Bot da empresa prioritária (opcional) |
| `TELEGRAM_TI_BOT_TOKEN` / `_CHAT_ID` | Bot das vagas que não são estágio (opcional) |
| `CIDADE_BASE` / `UF_BASE` | Cidade aceita para vagas híbridas e estado aceito quando uma vaga remota exige residência |
| `AREA_TERMOS` / `AREA_TERMOS_TITULO` | Área desejada: termos procurados no título e na descrição, ou apenas no título |
| `AREA_EXCLUIR` / `AREA_EXCLUIR_TITULO` | Área indesejada: termos que descartam a vaga |
| `ESTRELAS_TERMOS_AREA` / `ESTRELAS_TERMOS_PERFIL` | Termos no título que somam estrelas |
| `EMPRESAS_PRIORITARIAS` | Empresas sempre exibidas, separadas por vírgula |
| `EMPRESAS_BLOQUEADAS` | Empresas nunca exibidas, separadas por vírgula |
| `PRIORIDADE_NOME_EMPRESA` | Nome exibido nas vagas do site da empresa prioritária |
| `PRIORIDADE_FIRESTORE_PROJETO` / `_CHAVE` | Acesso público ao site de carreiras da empresa prioritária |
| `PRIORIDADE_URL_VAGAS` | Página de vagas da empresa prioritária |

Os bots de prioridade e de TI são opcionais: quando não configurados, as vagas
seguem para o bot de estágios. As listas de empresas que somam estrelas e os
pesos da classificação ficam em `configuracao/ajustavel/criterios.yaml`.

## ⋆˚✮ Stack

`Python 3.10+` · `requests` · `PyYAML` · `python-dotenv` ·
`Telegram Bot API` · `GitHub Actions`

## ⋆˚✮ Autora

Feito por [Rhebecca Tainara](https://www.linkedin.com/in/rhebecca-tainara)

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=100&color=0:8323b5,100:000000&section=footer" alt=""/>
