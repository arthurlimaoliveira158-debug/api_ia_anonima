# API IA Anônima — Controle de Acesso e Proteção de Dados

API feita em **FastAPI** para autenticação segura e armazenamento de dados
pessoais criptografados, com auditoria de logs e um módulo de **detecção de
anomalias por IA** (Isolation Forest) que varre os logs em busca de
possíveis ataques de força bruta, bots e comportamentos fora do padrão.

## Funcionalidades

- **Cadastro e login de usuários**, com senha protegida por hash **bcrypt**
  (a senha em texto puro nunca é salva no banco).
- **Autenticação via token JWT**: depois do login, o token é enviado no
  cabeçalho `Authorization: Bearer <token>` para acessar as rotas protegidas.
- **Bloqueio automático por força bruta**: após 3 tentativas de login
  erradas seguidas para o mesmo usuário, a conta fica bloqueada por 15
  minutos.
- **Dados pessoais criptografados**: tudo que é salvo em `/dados` é cifrado
  com **Fernet** (AES-128 + HMAC) antes de ir pro banco — mesmo quem tiver
  acesso direto ao banco não consegue ler o conteúdo sem a chave.
- **Auditoria completa**: toda ação relevante (cadastro, login, falha de
  login, bloqueio, inserção/consulta de dado) é registrada com data/hora em
  um log, consultável em `/logs`.
- **Detecção de anomalias com IA (SIEM)**: a rota `/siem/analise` executa um
  modelo `IsolationForest` (scikit-learn) treinado sobre os logs do sistema
  para isolar automaticamente vetores de ataque em tempo real.
- **Banco de dados via Prisma ORM**, usando SQLite por padrão (fácil de
  trocar para PostgreSQL/MySQL depois).

---

## Estrutura do Projeto

| Arquivo / pasta | Responsabilidade |
|---|---|
| `main.py` | Aplicação FastAPI e registro central de rotas/middlewares. |
| `config.py` | Configurações de segurança: chave JWT, chave Fernet, hash de senha. |
| `database.py` | Conexão e gerenciamento do ciclo de vida do Prisma ORM. |
| `schemas.py` | Schemas de validação de dados de entrada e saída (Pydantic). |
| `security.py` | Utilitários de gravação de auditoria e validação de sessão JWT. |
| `ai_detector.py` | Módulo de Inteligência Artificial para detecção de anomalias (SIEM). |
| `simulador_ataques.py` | Script de testes para injeção de tráfego legítimo e vetores de ataque. |
| `prisma/schema.prisma` | Modelagem das tabelas (usuários, dados, logs e tentativas de login). |

---

## Módulo de IA e SIEM (`ai_detector.py`)

A IA atua como um sistema **SIEM (Security Information and Event Management)** preventivo. Diferente de sistemas tradicionais baseados apenas em regras estáticas (`if/else`), o modelo utiliza o algoritmo **Isolation Forest** (*Machine Learning* não supervisionado) para identificar anomalias comportamentais no fluxo de logs.

### Como a IA funciona por dentro:

1. **Extração e Janela Temporal (Feature Engineering):**
   - **`frequencia_1_min_anteriores`**: Mede quantas requisições foram realizadas na mesma janela de 60 segundos. Picos repentinos indicam atuação de bots, automações ou ataques DDoS na camada de aplicação.
   - **`risco_acao`**: Converte logs de texto em um índice de severidade numérico (ex: `BLOQUEIO` = 20, `FALHA DE LOGIN` = 15, `CONSULTA` = 2).
   - **`fora_expediente`**: Avalia o horário do evento (identificando atividades atípicas executadas na madrugada).

2. **Isolamento de Ameaças:**
   - O algoritmo calcula o quão "fácil" é isolar uma observação do restante dos dados. Ações comuns (como navegação e logins com sucesso) ficam agrupadas em alta densidade. Eventos atípicos são isolados rapidamente e classificados como anomalias (`predicao = -1`).

3. **Geração de Relatório Explicável:**
   - A resposta do endpoint `/siem/analise` não entrega apenas IDs numéricos, mas interpreta os fatores que levaram à classificação da ameaça:
     ```json
     {
       "status": "Analise Concluida",
       "logs_processados": 200,
       "anomalias_detectadas": 12,
       "nivel_ameaca": "ALTO",
       "relatorio_detalhado": [
         {
           "log_id": 185,
           "acao_suspeita": "FALHA DE LOGIN: Credenciais incorretas para -> 'admin_master'",
           "indicadores": "Alta frequência (45 req/min) | Ação de alto risco de segurança"
         }
       ]
     }
     ```

---

## Testando a IA com o Simulador de Ataques (`simulador_ataques.py`)

Para validar a capacidade do detector de anomalias em um ambiente real, utilize o script de simulação automatizado.

### Step-by-Step para Execução dos Testes:

#### 1. Garanta que a API esteja rodando
Em um terminal, inicie o servidor FastAPI:
```bash
uvicorn main:app --reload
```

#### 2. Instale a biblioteca `requests` (se necessário)
```bash
pip install requests
```

#### 3. Execute o Simulador de Ataques
Em um **segundo terminal**, execute o script de testes:
```bash
python simulador_ataques.py
```

**O que o simulador faz durante a execução?**
- **Fase 1 (Tráfego Normal):** Cria usuários legítimos, realiza autenticações bem-sucedidas e insere dados cifrados com intervalos simulando comportamento humano.
- **Fase 2 (Ataque de Força Bruta):** Dispara tentativas consecutivas de login com senhas incorretas contra a conta `admin_master`, forçando o bloqueio temporário do sistema.
- **Fase 3 (Inundação de Requisições / Bot):** Dispara dezenas de consultas por segundo para simular o comportamento de um *crawler* ou ataque de negação de serviço (DDoS).

#### 4. Consulte o Relatório de IA no Postman / Insomnia

1. **Cadastre e autentique o administrador:**
   - Crie o usuário `admin_master` via `POST /registrar`.
   - Obtenha o token JWT via `POST /login`.
2. **Execute a análise SIEM:**
   - Envie uma requisição `GET` para `http://127.0.0.1:8000/siem/analise`.
   - Na aba **Authorization**, selecione **Bearer Token** e cole o token do `admin_master`.
3. **Validação dos Resultados:**
   - O campo `nivel_ameaca` deve mudar para `"ALTO"`.
   - O array `relatorio_detalhado` destacará os eventos exatos de Força Bruta e Requisições em Massa gerados pelo script, ignorando as requisições de uso humano do início da simulação.

---

## Pré-requisitos

- **Python 3.12 ou 3.13** instalado. *(Evite o Python 3.14 por enquanto — dependências como scikit-learn/pandas exigem compilação prévia).*
- **Node.js** instalado (necessário para o motor do Prisma ORM).
- Dependências do projeto instaladas via `requirements.txt`.

---

## Como Instalar e Rodar o Projeto

1. **Clone ou copie o repositório** para o diretório local.
2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Gere o cliente Prisma e sincronize o Banco de Dados:**
   ```bash
   prisma generate
   prisma db push
   ```
5. **Inicie o servidor da API:**
   ```bash
   uvicorn main:app --reload
   ```
6. Acesse a documentação interativa Swagger em: **http://127.0.0.1:8000/docs**

---

## Variáveis de Ambiente e Segurança

| Variável | Descrição |
|---|---|
| `FERNET_KEY` | Chave simétrica usada para cifrar os dados em `/dados`. Se omitida, a aplicação gera e mantém uma chave em `fernet.key`. |
| `SECRET_KEY` | Chave de assinatura dos tokens JWT em `config.py`. Em ambientes de produção, deve ser substituída por um valor secreto via `.env`. |

> **Nota de Segurança:** O arquivo `fernet.key` não deve ser deletado após o início do uso do sistema, caso contrário, as informações criptografadas na tabela `dados_pessoais` não poderão mais ser decifradas.