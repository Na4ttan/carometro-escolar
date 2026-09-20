# 🏫 Carômetro Escolar (Projeto Integrador II)

Este é o repositório do sistema de Carômetro Escolar, desenvolvido para facilitar a identificação visual de alunos na portaria e agilizar a rotina dos professores. 

O projeto utiliza uma arquitetura separada (Headless):
- **Backend (API):** Python com Django e Django REST Framework.
- **Frontend (Web/Mobile):** Angular.

---

## 🛠️ 1. Pré-requisitos

Antes de baixar o projeto, certifique-se de ter as seguintes ferramentas instaladas na sua máquina:

1. **Python (3.10 ou superior):** [Baixar Python](https://www.python.org/downloads/) (No Windows, lembre-se de marcar a caixa "Add Python to PATH" durante a instalação).
2. **Node.js (versão LTS):** [Baixar Node.js](https://nodejs.org/) (Ele inclui o gerenciador de pacotes `npm`).
3. **Git:** [Baixar Git](https://git-scm.com/downloads).

---

## 🚀 2. Como clonar o repositório

Abra o terminal na pasta onde deseja salvar o projeto e rode:


git clone [https://github.com/Na4ttan/carometro-escolar.git](https://github.com/Na4ttan/carometro-escolar.git)
cd carometro-escolar

## 🐍 3. Configurando e rodando o Backend (Django)
Abra um terminal, acesse a pasta do backend e crie o ambiente virtual para isolar as dependências do Python.

1. Acesse a pasta:

Bash
cd backend
2. Crie o ambiente virtual:

Bash
python -m venv venv
3. Ative o ambiente virtual:

No Windows (Command Prompt / PowerShell):

Bash
venv\Scripts\activate
No Linux / Mac:

Bash
source venv/bin/activate
(Você saberá que deu certo se aparecer um (venv) no início da linha do terminal)

4. Instale as dependências:

Bash
pip install django djangorestframework django-cors-headers Pillow
5. Crie as tabelas no banco de dados e rode o servidor:

Bash
python manage.py migrate
python manage.py runserver
O backend estará rodando em: http://127.0.0.1:8000/

## 🅰️ 4. Configurando e rodando o Frontend (Angular)
Abra um NOVO terminal (mantenha o terminal do Django rodando em segundo plano) e acesse a pasta do frontend.

1. Acesse a pasta:

Bash
cd frontend
2. Instale o Angular CLI globalmente na sua máquina (só precisa fazer isso uma vez):

Bash
npm install -g @angular/cli
3. Instale as dependências locais do projeto:

Bash
npm install
4. Rode o servidor de desenvolvimento do Angular:

Bash
ng serve
O frontend estará rodando em: http://localhost:4200/

## ✅ 5. Como testar se tudo deu certo
Com os dois terminais rodando (um com o Django e outro com o Angular), abra o seu navegador e acesse http://localhost:4200/.

Se a tela exibir a mensagem "API do Carômetro funcionando!", significa que o frontend conseguiu se conectar ao banco de dados com sucesso e o seu ambiente está 100% pronto para desenvolvimento.


fotos dos alunos e professores.
