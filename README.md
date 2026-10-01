# API IA Anônima — Controle de Acesso e Proteção de Dados

API feita em **FastAPI** para autenticação segura e armazenamento de dados
pessoais criptografados, com auditoria de logs e um módulo de **detecção de
anomalias por IA** (Isolation Forest) que varre os logs em busca de
possíveis ataques de força bruta.

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
- **Detecção de anomalias com IA**: a rota `/siem/analise` treina um modelo
  `IsolationForest` (scikit-learn) em cima dos logs recentes e aponta quais
  eventos fogem do padrão normal de uso — com peso extra para falhas de
  login, o que ajuda a sinalizar possíveis ataques.
- **Banco de dados via Prisma ORM**, usando SQLite por padrão (fácil de
  trocar para PostgreSQL/MySQL depois).

## Como funciona por dentro

| Arquivo / pasta | Responsabilidade |
|---|---|
| `main.py` | Cria a aplicação FastAPI e registra as rotas (routers). |
| `config.py` | Configurações de segurança: chave JWT, chave Fernet, contexto de hash de senha. |
| `database.py` | Conexão com o banco via Prisma (abre/fecha junto com a API). |
| `schemas.py` | Formatos de entrada/saída da API (Pydantic). |
| `security.py` | Funções compartilhadas: gravar log de auditoria e validar o usuário logado a partir do token. |
| `routers/auth.py` | Rotas `/registrar` e `/login`. |
| `routers/dados.py` | Rotas `/dados` (salvar e listar dado criptografado). |
| `routers/auditoria.py` | Rotas `/logs` e `/siem/analise`. |
| `ai_detector.py` | Modelo de IA (Isolation Forest) usado pelo `/siem/analise`. |
| `prisma/schema.prisma` | Definição das tabelas do banco (usuários, dados, logs, tentativas de login). |

### Fluxo típico de uso

1. `POST /registrar` — cria um usuário (username + senha).
2. `POST /login` — valida usuário e senha e devolve um token JWT.
3. Usa o token nas próximas requisições, no cabeçalho
   `Authorization: Bearer <token>`:
   - `POST /dados` — salva uma informação (ela é criptografada antes de ir pro banco).
   - `GET /dados` — lista as informações salvas, já decriptografadas.
   - `GET /logs` — mostra os últimos 50 eventos de auditoria.
   - `GET /siem/analise` — roda a IA de detecção de anomalias sobre os logs
     (apenas o usuário `admin_master` tem acesso a essa rota).

Toda a documentação interativa da API (pra testar as rotas direto do
navegador) fica disponível em `/docs` assim que o servidor estiver rodando.

## Pré-requisitos

- **Python 3.12 ou 3.13** instalado. *(Evite o Python 3.14 por enquanto —
  algumas bibliotecas científicas usadas aqui, como pandas/numpy/scikit-learn,
  ainda não têm pacotes prontos para ele em todos os sistemas, o que pode
  travar a instalação.)*
- **Node.js** instalado — o Prisma usa o Node por baixo dos panos para
  baixar seu motor de banco de dados na primeira execução.
- Conexão com a internet na primeira instalação (para baixar as
  dependências Python e o motor do Prisma).

## Como instalar em outro computador

1. **Copie a pasta do projeto** para o computador de destino (ou clone o
   repositório, se estiver usando Git).

2. **Crie um ambiente virtual** (recomendado, para não misturar com outros
   projetos Python):

   ```bash
   python -m venv venv
   ```

   Ative o ambiente:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. **Instale as dependências**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Gere o client do Prisma** (necessário sempre que o projeto é copiado
   para uma máquina nova, pois o client gerado é específico do sistema
   operacional):

   ```bash
   prisma generate
   ```

5. **Crie o banco de dados** a partir do `schema.prisma`:

   ```bash
   prisma db push
   ```

   Isso cria o arquivo `prisma/ia_anonima.db` (SQLite) já com as tabelas
   `usuarios`, `dados_pessoais`, `logs` e `tentativas_login`.

6. **Suba a API**:

   ```bash
   uvicorn main:app --reload
   ```
Ou usa esse se o primeiro não funcionar

   ```bash
   python -m uvicorn main:app --reload
   ```

7. Acesse **http://127.0.0.1:8000/docs** no navegador para ver e testar
   todas as rotas pela interface interativa (Swagger).

### Variáveis de ambiente opcionais (recomendado em produção)

Por padrão, a API já funciona sem nenhuma configuração extra: na primeira
execução ela gera sozinha uma chave de criptografia e a salva em
`fernet.key`, na pasta do projeto. Em produção, o recomendado é definir essa
chave (e a chave do JWT) manualmente, via variável de ambiente, em vez de
depender do arquivo gerado automaticamente:

| Variável | Para que serve |
|---|---|
| `FERNET_KEY` | Chave usada para criptografar/decriptografar os dados pessoais. Se não for definida, a API gera uma e guarda no arquivo `fernet.key`. |

> **Atenção:** se o arquivo `fernet.key` for perdido (ou a variável de
> ambiente mudar) sem backup, **todos os dados já salvos em `/dados` ficam
> permanentemente ilegíveis**, pois dependem exatamente da mesma chave usada
> para cifrá-los. Guarde essa chave com cuidado.

A chave do token JWT (`SECRET_KEY`, em `config.py`) também está fixa no
código por padrão — em produção, o ideal é movê-la para uma variável de
ambiente também, em vez de deixá-la hardcoded no arquivo.

## Testando rapidamente

Com a API rodando, um teste rápido pela própria interface `/docs`:

1. Abra `POST /registrar`, clique em "Try it out" e cadastre um usuário.
2. Abra `POST /login`, informe o mesmo usuário/senha e copie o
   `access_token` da resposta.
3. Clique no botão **Authorize** (cadeado, no topo da página) e cole o
   token para autenticar as próximas chamadas.
4. Teste `POST /dados`, `GET /dados` e `GET /logs` normalmente.
5. Para testar o `/siem/analise`, cadastre um usuário chamado
   `admin_master`, gere algum tráfego (alguns logins errados, por exemplo)
   e chame a rota autenticado como esse usuário.
