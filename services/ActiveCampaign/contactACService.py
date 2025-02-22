from fastapi import APIRouter, Request, UploadFile, File
import logging
import urllib.parse
import json
from io import BytesIO
import datetime
import requests
import httpx


router = APIRouter()

@router.post("/api/webhook/contactAC")
async def webhook(request: Request):
    try:
        body = await request.body()
        body_str = body.decode("utf-8")  # Converte para string

        #decodificacao da url-encoded
        parsed_data = urllib.parse.parse_qs(body_str)

        logging.info(f"Data recebida: {parsed_data}")
        
        if not body:
            logging.warning("Corpo da requisição está vazio.")
            return {"status": "error", "message": "Corpo da requisição vazio."}
        
        #  Processa os dados usando a função separada
        json_data = parse_webhookdata_json(body_str)

        #  Cria JSON na memória
        filename, json_bytes = create_json_in_memory(json_data)

        # Envia o JSON para a API do Data Lake
        response = send_to_datalake(filename, json_bytes)

        return {"status": "success", "received_body": response}

    except Exception as e:
        logging.error(f"Erro inesperado ao processar webhook: {e}")
        return {"status": "error", "message": str(e)}
    
    
def parse_webhookdata_json(body_str: str):
    """
    Função para decodificar os dados URL-encoded do ActiveCampaign e convertê-los para um JSON válido.
    """
    # Decodifica URL-encoded para um dicionário Python
    parsed_data = urllib.parse.parse_qs(body_str)

    # Remove listas, mantendo apenas o primeiro valor
    cleaned_data = {key: values[0] if len(values) == 1 else values for key, values in parsed_data.items()}

    return cleaned_data


def create_json_in_memory(data: dict):
    """
    Cria um arquivo JSON na memória usando BytesIO. #apenas para fins de demonstração
    """
    
    # Converte o dicionário para um JSON string
    json_str = json.dumps(data, ensure_ascii=False, indent=4)

    # Cria um objeto BytesIO e escreve o JSON nele
    json_io = BytesIO(json_str.encode('utf-8'))

    # Cria um objeto BytesIO e escreve o JSON nele
    json_io = BytesIO(json_str.encode('utf-8'))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define um nome para o arquivo (opcional, mas útil em Uploads)
    json_io.name = f"contact_{timestamp}.json"

    return json_io

async def send_to_datalake(filename: str, file: UploadFile):
    """
    Envia um arquivo JSON para a API do Data Lake no formato multipart/form-data.
    """
    url = "https://app-orion-dev.azurewebsites.net/api/azure-datalake/uploadfile"
    params = {
        "storage_account_name": "saactivecampaign",
        "file_system_name": "bronze",
        "directory_name": "contacts"
    }
    headers = {
        "accept": "application/json"
    }

    # Lê o conteúdo do arquivo enviado pelo FastAPI
    file_content = await file.read()

    async with httpx.AsyncClient() as client:
        files = {
            "file": (filename, file_content, "application/json")
        }
        response = await client.post(url, params=params, headers=headers, files=files)

    return response.json()
