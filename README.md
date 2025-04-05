# Backend de Processamento de Mensagens entre LLMs 
 
Este projeto implementa um backend em Python com FastAPI que atua como intermediário entre um frontend React e duas LLMs (Large Language Models) distintas, responsáveis por codificação e decodificação de mensagens. 
 
## Arquitetura 
 
O sistema implementa a seguinte arquitetura de comunicação: 
 
- **Frontend (React)**: Interface para o usuário enviar mensagens 
- **Backend (Python/FastAPI)**: Coordena o fluxo de processamento 
- **LLM A (lua_a)**: Responsável por codificar mensagens 
- **LLM B (lua_b)**: Responsável por decodificar mensagens e gerar respostas 
 
O fluxo de processamento segue estas etapas: 
 
1. O frontend envia uma mensagem ao backend 
2. O backend encaminha a mensagem para a LLM A 
3. A LLM A codifica a mensagem e retorna: 
   - A mensagem codificada 
   - A instrução de codificação (não codificada) 
4. O backend encaminha ambas para a LLM B 
5. A LLM B decodifica, processa e responde usando a mesma técnica de codificação 
6. O backend retorna a resposta codificada ao frontend 
 
## Requisitos 
 
- Python 3.8+ 
- FastAPI 
- Uvicorn 
- HTTPX 
- Python-dotenv 
 
## Instalação 
 
1. Clone o repositório: 
```bash 
git clone https://github.com/seu-usuario/backend-llm-processor.git 
cd backend-llm-processor 
``` 
 
2. Crie e ative um ambiente virtual: 
```bash 
python -m venv venv 
source venv/bin/activate  # No Windows: venv\Scripts\activate 
``` 
 
3. Instale as dependências: 
```bash 
pip install -r requirements.txt 
``` 
 
4. Configure as variáveis de ambiente: 
```bash 
cp .env.sample .env 
``` 
Edite o arquivo `.env` com as URLs e chaves de API corretas. 
 
## Execução 
 
Para iniciar o servidor: 
 
```bash 
uvicorn main:app --reload --host 0.0.0.0 --port 8000 
``` 
 
Ou simplesmente: 
 
```bash 
python main.py 
``` 
 
Para testar com os mocks de LLM: 
 
```bash 
cd mock 
python mock_llms.py 
``` 
 
## Licença 
 
MIT 
