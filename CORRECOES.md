# O que estava impedindo a API de funcionar

Testei o projeto do zero (instalação limpa das dependências + execução completa
do fluxo registrar → login → salvar dado → listar dado) e encontrei 2 causas
reais para o "não consigo acessar", além de 1 problema sério de perda de dados.

## 1. Faltava `python-multipart` no `requirements.txt` (causa raiz do app não subir)

A rota `/login` usa `OAuth2PasswordRequestForm`, que o FastAPI só consegue
processar se o pacote `python-multipart` estiver instalado. Sem ele, o
**próprio import do `main.py` já quebra** com:

```
RuntimeError: Form data requires "python-multipart" to be installed.
```

Ou seja: a API nunca chegava a subir — por isso "não conseguia acessar".

**Fix:** adicionado `python-multipart==0.0.6` ao `requirements.txt`.

## 2. `passlib==1.7.4` + versão nova do `bcrypt` são incompatíveis

Seu `requirements.txt` fixava a versão do `passlib`, mas não a do `bcrypt`.
Isso faz o `pip install` puxar a versão mais recente do `bcrypt` (4.1+), que
removeu um atributo interno (`__about__`) que o `passlib` 1.7.4 (não é mantido
desde 2020) depende para funcionar. Resultado, em `/registrar` e `/login`:

```
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

Ou seja: mesmo se a API subisse, cadastro e login quebravam com erro 500.

**Fix:** fixado `bcrypt==4.0.1` no `requirements.txt` (última versão totalmente
compatível com `passlib 1.7.4`).

## 3. (bônus) Chave Fernet era gerada aleatoriamente a cada reinício

Em `config.py`, `FERNET_KEY = Fernet.generate_key()` gerava uma chave nova
toda vez que o servidor subia — o próprio comentário no código já avisava
disso. Na prática, isso significa que a cada `uvicorn main:app` reiniciado,
**todos os dados anteriormente salvos em `/dados` ficam permanentemente
ilegíveis** (aparecem como `[ERRO: Não foi possível decifrar o dado]`).

**Fix:** a chave agora é lida de uma variável de ambiente `FERNET_KEY` (se
existir) ou, na primeira execução, gerada uma única vez e salva em
`fernet.key` na pasta do projeto, sendo reaproveitada nas próximas
execuções. Em produção, defina a variável de ambiente `FERNET_KEY` (e faça o
mesmo com `SECRET_KEY`, em `config.py`, que também está hardcoded).

## 4. `pip install` falhando ao instalar o `pandas` (Python 3.14)

Se você estiver no Python 3.14 (bem recente), o erro que você mandou depois
(`installing build dependencies for pandas did not run successfully` /
`Unknown compiler(s)`) acontece porque `pandas==2.1.3`, `numpy` (a versão que
ele puxa por baixo) e `scikit-learn==1.3.2` são de 2023 e **não têm wheel
pré-compilada para Python 3.14** — o pip tenta compilar tudo do zero e falha
porque não há compilador C instalado no Windows.

Isso, por sua vez, expôs mais um problema: ao atualizar o `pydantic` para uma
versão com wheel para 3.14, o `fastapi==0.104.1` (2023) quebra, porque usa
detalhes internos do `pydantic` que mudaram nas versões novas.

**Fix:** atualizei todo o "trio" para versões modernas e mutuamente
compatíveis, todas com wheel pronta pra Python 3.14 no Windows:

```
fastapi==0.118.0
uvicorn[standard]==0.34.0
pydantic==2.12.0
pandas==2.3.3
numpy==2.3.3
scikit-learn==1.7.2
```

Testei o projeto inteiro de novo com essas versões (registro, login,
bloqueio por tentativas, dado criptografado e o `/siem/analise` com o
`IsolationForest` do scikit-learn) e está tudo funcionando.

Se preferir não lidar com isso de novo no futuro (pacotes científicos como
pandas/numpy/scikit-learn sempre demoram pra ter wheel pronta pra versões
novíssimas do Python), a alternativa mais tranquila é instalar o projeto com
Python 3.12 ou 3.13 em vez do 3.14 — aí as versões antigas do
`requirements.txt` original também teriam funcionado sem drama.

## Como rodar depois de aplicar os fixes

```bash
pip install -r requirements.txt
prisma generate
prisma db push        # cria/atualiza o banco a partir do schema.prisma
uvicorn main:app --reload
```

Testei todo o fluxo (registrar, login, bloqueio após 3 tentativas erradas,
salvar/listar dado criptografado, logs de auditoria) simulando o banco via
Prisma e deu tudo certo com essas correções.
