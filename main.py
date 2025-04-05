# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("message_processor")

# Inicialização do FastAPI
app = FastAPI(title="LLM Message Processor API")

# Configuração de CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados
class MessageRequest(BaseModel):
    message: str
    mode: str = "coded"  # "native" ou "coded"

class MessageResponse(BaseModel):
    original_message: str
    processed_message: Optional[str] = None
    coding_instruction: Optional[str] = None
    final_response: str

# Configurações das APIs LLM
LLM_A_API_URL = os.getenv("LLM_A_API_URL", "http://localhost:8001/api/llm-a")
LLM_B_API_URL = os.getenv("LLM_B_API_URL", "http://localhost:8001/api/llm-b")
LLM_A_API_KEY = os.getenv("LLM_A_API_KEY", "")
LLM_B_API_KEY = os.getenv("LLM_B_API_KEY", "")

# Cliente HTTP assíncrono
async def get_httpx_client():
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

# Função para chamar a LLM A (codificadora ou processamento nativo)
async def call_llm_a(message: str, client: httpx.AsyncClient, mode="coded"):
    """
    Função para enviar a mensagem original para a LLM A.
    No modo 'coded', retorna a mensagem codificada e a instrução de codificação.
    No modo 'native', processa a mensagem diretamente e retorna uma resposta.
    """
    try:
        # Instrução para a LLM A
        if mode == "coded":
            prompt = f"""
            Por favor, codifique a mensagem abaixo usando uma técnica de codificação criativa.
            Forneça tanto a mensagem codificada quanto a instrução precisa de como decodificá-la.
            A instrução de decodificação deve ser clara o suficiente para que outra LLM possa
            entender como reverter a codificação.
            
            Mensagem original: {message}
            
            Responda no formato JSON com:
            - 'coded_message': a mensagem codificada
            - 'coding_instruction': instrução clara de como decodificar (não codificada)
            """
        else:  # modo "native"
            prompt = f"""
            Por favor, responda à seguinte mensagem de forma direta e natural:
            
            Mensagem: {message}
            
            Forneça uma resposta útil e informativa.
            """
        
        payload = {
            "prompt": prompt,
            "api_key": LLM_A_API_KEY
        }
        
        logger.info(f"Enviando mensagem para LLM A (modo {mode}): {message[:50]}...")
        
        response = await client.post(LLM_A_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Resposta recebida da LLM A: {str(result)[:100]}...")
        
        if mode == "coded":
            # Verifica se os campos necessários estão presentes
            if "coded_message" not in result or "coding_instruction" not in result:
                logger.error(f"Resposta da LLM A não contém os campos necessários: {result}")
                raise HTTPException(status_code=500, detail="Resposta da LLM A em formato inválido")
                
            return {
                "coded_message": result.get("coded_message", ""),
                "coding_instruction": result.get("coding_instruction", "")
            }
        else:  # modo "native"
            # No modo nativo, a LLM A retorna diretamente uma resposta
            return {
                "response": result.get("response", f"Resposta da Lua A para: '{message}'")
            }
    
    except Exception as e:
        logger.error(f"Erro ao chamar LLM A: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento da LLM A: {str(e)}")

# Função para chamar a LLM B (decodificadora/respondedora)
async def call_llm_b(coded_message: str, coding_instruction: str, client: httpx.AsyncClient):
    """
    Função para enviar a mensagem codificada e a instrução de decodificação
    para a LLM B, que retornará uma resposta codificada usando a mesma técnica.
    """
    try:
        # Instrução para a LLM B - Formatada claramente para ser reconhecida pelo mock
        prompt = f"Mensagem codificada: {coded_message}\nInstrução de decodificação: {coding_instruction}\n\nPor favor:\n1. Decodifique a mensagem de acordo com a instrução\n2. Responda à mensagem de forma apropriada\n3. Codifique sua resposta usando exatamente a mesma técnica de codificação"
        
        payload = {
            "prompt": prompt,
            "api_key": LLM_B_API_KEY
        }
        
        logger.info(f"Enviando mensagem codificada para LLM B: {coded_message[:50]}...")
        
        response = await client.post(LLM_B_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Resposta recebida da LLM B: {str(result)[:100]}...")
        
        # Verifica se os campos necessários estão presentes
        if "decoded_message" not in result or "coded_response" not in result:
            logger.error(f"Resposta da LLM B não contém os campos necessários: {result}")
            raise HTTPException(status_code=500, detail="Resposta da LLM B em formato inválido")
            
        return {
            "decoded_message": result.get("decoded_message", ""),
            "response": result.get("response", ""),
            "coded_response": result.get("coded_response", "")
        }
    
    except Exception as e:
        logger.error(f"Erro ao chamar LLM B: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento da LLM B: {str(e)}")

# Endpoint principal para processar mensagens
@app.post("/api/process-message", response_model=MessageResponse)
async def process_message(
    request: MessageRequest, 
    client: httpx.AsyncClient = Depends(get_httpx_client)
):
    """
    Endpoint principal que recebe mensagens do frontend e coordena o fluxo de processamento.
    Suporta dois modos:
    - "native": processa a mensagem diretamente com a LLM A
    - "coded": processa a mensagem através do fluxo completo (LLM A -> LLM B)
    """
    try:
        logger.info(f"Recebida requisição para processar mensagem em modo: {request.mode}")
        
        # Inicializa a resposta
        response = {
            "original_message": request.message,
            "processed_message": None,
            "coding_instruction": None,
            "final_response": "",
        }
        
        if request.mode == "native":
            # Modo nativo: processamento direto pela LLM A
            result = await call_llm_a(request.message, client, mode="native")
            response["final_response"] = result["response"]
            
        else:  # modo "coded" (padrão)
            # Passo 1: Enviar para LLM A para codificação
            llm_a_result = await call_llm_a(request.message, client, mode="coded")
            
            response["processed_message"] = llm_a_result["coded_message"]
            response["coding_instruction"] = llm_a_result["coding_instruction"]
            
            # Passo 2: Enviar mensagem codificada e instrução para LLM B
            llm_b_result = await call_llm_b(
                llm_a_result["coded_message"],
                llm_a_result["coding_instruction"],
                client
            )
            
            # Passo 3: Retornar a resposta codificada
            response["final_response"] = llm_b_result["coded_response"]
        
        logger.info("Mensagem processada com sucesso")
        return response
    
    except Exception as e:
        logger.error(f"Erro no processamento da mensagem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

# Endpoint para verificação de saúde da API
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Execução da aplicação
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)