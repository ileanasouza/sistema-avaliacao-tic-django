# sistema-avaliacao-tic-django
Sistema de gestão de avaliações TIC desenvolvido em Django para controlo de notas cognitivas, atitudes e boletins por período.

# Sistema de Avaliação TIC (Django)

Sistema web desenvolvido em **Python com Django** para gestão de avaliações da disciplina de Tecnologias da Informação e Comunicação (TIC), permitindo o controlo de:

- Avaliações cognitivas (com pesos percentuais)
- Notas individuais por aluno
- Avaliação de atitudes (com tetos fixos até 20 pontos)
- Cálculo automático de média ponderada
- Geração de boletim por período
- Atualização automática via signals

---

## 📌 Objetivo do Projeto

O objetivo deste projeto foi desenvolver um sistema estruturado, automatizado e coerente para cálculo de classificações da disciplina de TIC, respeitando o seguinte modelo de avaliação:

- **Domínio Cognitivo:** 80%
- **Atitudes:** 20%
- **Nota Final:** 0 a 100 valores
- **Conversão para nível (1 a 5)**
- **Menção qualitativa automática**

O sistema foi desenvolvido com foco na organização modular, boas práticas de Django e separação clara de responsabilidades.

---

## 🛠 Tecnologias Utilizadas

- **Python 3**
- **Django**
- **SQLite3** (base de dados)
- **Django Admin (interface administrativa)**
- **Git e GitHub**
- Arquitetura modular baseada em aplicações Django

---

## 🏗 Estrutura do Projeto

ADS_GestaoAvaliacoes/
│
├── apps/
│ ├── nucleo/ # Turmas e Alunos
│ ├── tic/ # Sistema de avaliação TIC
│ │ ├── models.py
│ │ ├── admin.py
│ │ ├── signals.py
│ │ ├── services/
│ │ │ └── tic_calculator.py
│ │ └── management/commands/
│ │ └── recalcular_tic.py
│
├── config/ # Configurações do projeto Django
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
│
├── manage.py
└── README.md


---

## 🧮 Modelo de Avaliação Implementado

### 1️⃣ Avaliações Cognitivas

- Cada avaliação possui:
  - Nome
  - Período (1º, 2º ou 3º)
  - Peso percentual (0 a 100)
- Cada aluno recebe nota (0 a 100)

A média é calculada como:
  Média Ponderada = (Σ (nota × peso)) / Σ pesos


Depois convertida para:
  Cognitivo (0..80) = Média × 0.80

---

### 2️⃣ Atitudes (0 a 20 pontos)

Com tetos fixos:

| Dimensão                               | Máximo |
|----------------------------------------|--------|
| Responsabilidade e Integridade         | 3      |
| Excelência e Exigência                 | 6      |
| Curiosidade, Reflexão e Inovação       | 2      |
| Cidadania e Participação               | 4      |
| Liberdade                              | 5      |

Total máximo: **20 pontos**

---

### 3️⃣ Nota Final
  Nota Final = Cognitivo (0..80) + Atitudes (0..20)

---

### 4️⃣ Conversão para Menção e Nível

| Nota Final | Menção        | Nível |
|-------------|--------------|--------|
| < 50        | Insuficiente | 1 ou 2 |
| 50–69       | Suficiente   | 3      |
| 70–89       | Bom          | 4      |
| ≥ 90        | Muito Bom    | 5      |

---

## ⚙️ Funcionamento Automático
O sistema utiliza:

- **Signals (post_save e post_delete)**  
- Recalcula automaticamente o boletim quando:
  - Uma nota é adicionada ou alterada
  - Uma atitude é registada
  - Um peso de avaliação é alterado

O cálculo está isolado em:
  apps/tic/services/tic_calculator.py


Garantindo:
- Separação de responsabilidades
- Código reutilizável
- Ausência de recursividade
- Segurança transacional (transaction.atomic)

---

## ▶️ Instruções de Execução

### 1️⃣ Clonar o repositório
Deve-se executar os seguintes comandos:
git clone https://github.com/ileanasouza/sistema-avaliacao-tic-django.git
cd sistema-avaliacao-tic-django


2️⃣ Criar ambiente virtual (recomendado)
  python -m venv venv
  venv\Scripts\activate   # Windows

3️⃣ Instalar dependências
  pip install django

4️⃣ Aplicar migrações
  python manage.py migrate

5️⃣ Criar superutilizador
  python manage.py createsuperuser

6️⃣ Executar servidor
  python manage.py runserver

Aceder a:
  http://127.0.0.1:8000/admin

🧩 Funcionalidades Disponíveis no Admin
- Gestão de Turmas
- Gestão de Alunos
- Criação de Avaliações Cognitivas
- Registo de Notas
- Registo de Atitudes
- Visualização de Boletim por Período
- Cálculo automático da média
- Exibição da média no próprio boletim
- Visualização detalhada por período


🔄 Comando de Recalculo Manual
Caso seja necessário recalcular todos os boletins:
  python manage.py recalcular_tic

📊 Características Técnicas Relevantes
- Uso de Decimal para evitar erros de arredondamento
- Uso de ROUND_HALF_UP
- unique_together para integridade
- IntegerChoices para períodos
- OneToOneField para atitudes
- select_related para otimização de queries
- transaction.atomic para segurança
- Estrutura modular escalável


🚀 Possíveis Implementações Futuras
- Interface própria (fora do Django Admin)
- Exportação para PDF
- Exportação para Excel
- Dashboard com gráficos
- API REST com Django REST Framework
- Autenticação por perfis (professor/direção)
- Cálculo de média anual automática (3 períodos)
- Deploy em servidor cloud

👩‍💻 Autoria
Desenvolvido por:
Ileana Karla Antunes de Souza

Mestrado em Informática
Projeto desenvolvido no âmbito académico da Universidade da Maia.

📄 Licença
Uso académico.









