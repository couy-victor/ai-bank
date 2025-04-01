# AI-Bank 🏦

Um agente bancário inteligente desenvolvido em Python que utiliza processamento de linguagem natural para fornecer informações sobre serviços bancários, com foco em empréstimos consignados.

## 📋 Sobre o Projeto

O AI-Bank é um sistema inteligente que processa e responde perguntas sobre serviços bancários utilizando documentos FAQ como base de conhecimento. O sistema utiliza técnicas avançadas de processamento de linguagem natural para entender as perguntas dos usuários e fornecer respostas precisas.

## 🚀 Funcionalidades

- Processamento inteligente de perguntas sobre serviços bancários
- Respostas baseadas em documentos FAQ oficiais
- Sistema de estados para manter contexto das conversas
- Processamento de grafos para navegação contextual
- Armazenamento vetorial para busca semântica eficiente

## 🏗️ Estrutura do Projeto

```
fourbank/
├── agent/                  # Núcleo do agente inteligente
│   ├── graph.py           # Implementação de navegação em grafo
│   ├── nodes.py           # Definição dos nós de processamento
│   ├── services.py        # Serviços do agente
│   └── states.py          # Gerenciamento de estados
├── data/                   # Base de conhecimento
│   ├── faq_bancario_emprestimo_consig.pdf
│   └── FAQ-APP-FOLHA-v06.pdf
├── utils/                  # Utilitários
│   └── vectorstore.py     # Implementação de armazenamento vetorial
├── app.py                 # Aplicação principal
└── requirements.txt       # Dependências do projeto
```

## 🛠️ Tecnologias Utilizadas

- Python
- LangGraph para orquestração de agentes e fluxos conversacionais
- Processamento de Linguagem Natural (NLP)
- Armazenamento Vetorial para busca semântica
- Grafos para navegação contextual
- Gerenciamento de estados para manter contexto

## ⚙️ Como Executar

1. Clone o repositório
```bash
git clone [url-do-repositorio]
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Execute a aplicação
```bash
python app.py
```

## 📄 Licença

Este projeto está sob a licença [inserir tipo de licença].

## 👥 Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter um Pull Request.

---

Victor Aarão Couy
