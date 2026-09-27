# 🏫 Carômetro Escolar (Projeto Integrador II)

Este é o repositório do sistema de Carômetro Escolar, desenvolvido para facilitar a identificação visual de alunos na portaria e agilizar a rotina dos professores. 

O projeto utiliza uma arquitetura modular:
- **Backend (API + Servidor Web):** Python com Django e Django REST Framework.
- **Frontend (Web/Mobile):** Angular.

---

## 🛠️ 1. Pré-requisitos

Antes de baixar o projeto, certifique-se de ter as seguintes ferramentas instaladas na sua máquina:

1. **Python (3.10 ou superior):** [Baixar Python](https://www.python.org/downloads/) (No Windows, lembre-se de marcar a caixa "Add Python to PATH" durante a instalação).
2. **Node.js (versão LTS):** [Baixar Node.js](https://nodejs.org/) (Ele inclui o gerenciador de pacotes `npm` e o executor `npx`).
3. **Git:** [Baixar Git](https://git-scm.com/downloads).

---

## 🚀 2. Como clonar o repositório

Abra o terminal na pasta onde deseja salvar o projeto e rode:

```bash
git clone https://github.com/Na4ttan/carometro-escolar.git
cd carometro-escolar
```

---

## 🐍 3. Configurando o Backend (Django)
Abra um terminal, acesse a pasta do backend e crie o ambiente virtual para isolar as dependências do Python.

1. Acesse a pasta:

```bash
cd backend
```

2. Crie o ambiente virtual:

```bash
python -m venv venv
```

3. Ative o ambiente virtual:

No Windows (Command Prompt / PowerShell):

```bash
venv\Scripts\activate
```

No Linux / Mac:

```bash
source venv/bin/activate
```
*(Você saberá que deu certo se aparecer um `(venv)` no início da linha do terminal)*

4. Instale as dependências:

```bash
pip install django djangorestframework django-cors-headers pillow
```

5. Aplique as migrações no banco de dados:

```bash
python manage.py migrate
```

---

## 🅰️ 4. Configurando e Compilando o Frontend (Angular)
Abra um terminal na pasta do frontend:

1. Acesse a pasta:

```bash
cd frontend
```

2. Instale as dependências locais:

```bash
npm install
```

3. Compile a versão de distribuição para o Django servir:

```bash
npm run build
```

---

## 🔒 5. Como iniciar a Aplicação Completa com HTTPS para Celular e PC

O script inicializador sobe **todos os serviços necessários automaticamente**: o Backend (Django na porta 8000), o Frontend (Angular na porta 4200) e o túnel seguro HTTPS do Localtunnel.

### No Debian / Ubuntu / Linux:
Execute o script na raiz do projeto:
```bash
./iniciar.sh
```
Ou simplesmente digite o alias no seu terminal:
```bash
carometro
```

### No Windows:
Dê duplo clique no arquivo `iniciar.bat` na raiz do projeto ou execute no terminal:
```cmd
iniciar.bat
```
*(Para criar o alias no PowerShell do Windows, execute: `Set-Alias carometro .\iniciar.bat`)*.

---

### 💻 Acesso no Computador:
- **Frontend (Angular):** http://localhost:4200/
- **Backend / Django Admin:** http://localhost:8000/admin/

---

### 📱 Acesso no Celular (Mesmo Wi-Fi da Escola):

1. Conecte o celular na mesma rede Wi-Fi do computador.
2. Abra o navegador do celular e acesse o link seguro:
   👉 **`https://sweet-hounds-flash.loca.lt/`**
3. **Primeira abertura (Tela de liberação do Localtunnel):**
   - O Localtunnel exibe uma tela com o título *"Tunnel website ahead!"* solicitando o IP público (*Endpoint IP*).
   - O número exato do IP aparece impresso no seu terminal quando você roda o `./iniciar.sh` (ou consulte em https://loca.lt/mytunnelpassword).
   - Digite esse número no campo **IP Address** e clique em **Continue**.
   - Pronto! O Carômetro abre com cadeado verde HTTPS e permissão total para a câmera.

---

## ⚡ 6. Como rodar apenas em rede local (HTTP na Porta 8000)

Se quiser rodar apenas no computador sem usar o túnel da internet:

1. No terminal do backend (com o ambiente virtual ativo):
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py runserver 0.0.0.0:8000
   ```
2. Acesse no navegador do PC: **http://127.0.0.1:8000/**

---

## 🧑‍🏫 7. Passo a Passo: Configuração Inicial do Banco de Dados

Para que o sistema funcione do zero, é necessário criar primeiro o **administrador** e a **estrutura base da escola** no Django Admin. A partir disso, o restante da operação (cadastro de professores e alunos) é feito diretamente na interface visual do sistema.

### Passo 1: Criar o Administrador Geral do Sistema

Abra o terminal na pasta `backend` com o ambiente virtual ativo e execute:

```bash
cd backend
source venv/bin/activate    # No Windows: venv\Scripts\activate
python manage.py createsuperuser
```

O terminal solicitará:
- **Nome de usuário (Username):** ex: `admin`
- **Endereço de e-mail:** ex: `admin@escola.com`
- **Senha e confirmação:** digite sua senha de administrador (os caracteres não aparecem na tela por segurança).

---

### Passo 2: Cadastrar as Entidades Estruturais no Django Admin

Com a aplicação rodando, acesse no navegador: **http://127.0.0.1:8000/admin/** e faça login com a conta de administrador criada no Passo 1.

No Django Admin, cadastre as informações na seguinte ordem:

#### 1. Criar o Usuário da Escola:
1. Vá em **Usuários** (Users) ➔ **Adicionar usuário** (+).
2. Informe um nome de usuário (ex: `escola_central`) e defina uma senha.
3. Clique em **Salvar**.

#### 2. Cadastrar a Escola:
1. Vá em **Escolas** ➔ **Adicionar escola** (+).
2. Preencha:
   - **Nome:** ex: `Escola Municipal Santos Dumont`.
   - **Código INEP:** (opcional).
   - **Usuário:** selecione o usuário criado no passo anterior (`escola_central`).
3. Clique em **Salvar**.

#### 3. Cadastrar o Ano Letivo:
1. Vá em **Anos Letivos** ➔ **Adicionar ano letivo** (+).
2. Preencha:
   - **Ano:** ex: `2026`.
   - **Data de início** e **Data de término**.
   - **Ativo:** marque a caixa como ativo.
   - **Escola:** selecione a escola cadastrada.
3. Clique em **Salvar**.

#### 4. Cadastrar as Turmas:
1. Vá em **Turmas** ➔ **Adicionar turma** (+).
2. Preencha:
   - **Nome:** ex: `1º Ano A`, `9º Ano B`, `3º Colegial`.
   - **Série / Etapa:** ex: `1º Ano`, `9º Ano`.
   - **Turno:** selecione `Manhã`, `Tarde` ou `Noite`.
   - **Ano letivo:** selecione o ano letivo ativo.
   - **Escola:** selecione a sua escola.
3. Clique em **Salvar**. Cadastre quantas turmas desejar.

---

### Passo 3: Cadastrar Professores e Alunos na Aplicação Web/Mobile

Agora que a estrutura está pronta no Django Admin, **não é mais necessário usar o painel do Django para o dia a dia**.

1. Acesse o sistema pelo navegador:
   - No computador: **http://localhost:4200/**
   - No celular: **https://sweet-hounds-flash.loca.lt/**
2. Faça o login utilizando o **usuário e senha da escola** criados no Passo 2.1 (ex: `escola_central`).
3. No **Painel da Escola**:
   - **Cadastrar Alunos:** preencha nome, data de nascimento, selecione a turma e tire a foto diretamente pela câmera do celular/webcam ou selecione um arquivo de imagem.
   - **Cadastrar Professores:** preencha nome, e-mail (que será o login do professor), defina a **senha de acesso com confirmação**, selecione as turmas às quais ele leciona e tire a foto.
   - **Consultar / Carômetro Geral:** pesquise alunos e professores em tempo real por nome ou filtre por turma.

---

### Passo 4: Acesso do Professor ao Carômetro

1. No mesmo formulário de login inicial da aplicação (http://localhost:4200/ ou https://sweet-hounds-flash.loca.lt/):
2. O professor entra usando seu **e-mail** e a **senha** que a escola cadastrou para ele.
3. O professor é direcionado automaticamente para o **Carômetro**, onde pode:
   - Selecionar suas turmas atribuídas.
   - Ver a lista com fotos e nomes dos alunos matriculados nas suas turmas para identificação e acompanhamento diário.
   - O professor tem acesso somente de consulta, garantindo a segurança dos dados.

---

### 🔑 Gestão e Redefinição de Senhas no Django Admin (Suporte)

Se algum professor esquecer a senha, o administrador pode redefini-la facilmente:
1. Acesse **http://127.0.0.1:8000/admin/** ➔ **Professores**.
2. Abra o cadastro do professor.
3. Preencha os campos **Nova senha de acesso** e **Confirmar nova senha** (mínimo 6 caracteres).
4. Clique em **Salvar**. A senha será criptografada e sincronizada imediatamente com o login do professor.
