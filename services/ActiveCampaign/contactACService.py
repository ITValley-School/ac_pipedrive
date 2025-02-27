from fastapi import APIRouter, Request, UploadFile, File
import logging
import urllib.parse
import json
from io import BytesIO
import datetime
import requests



router = APIRouter()

@router.post("/api/webhook/contactAC")
async def webhook(request: Request):
    try:
        body = await request.body()
        body_str = body.decode("utf-8")  # Converte para string

        parsed_data = urllib.parse.parse_qs(body_str)
        logging.info(f"Data recebida: {parsed_data}")
        
        if not body:
            logging.warning("Corpo da requisição está vazio.")
            return {"status": "error", "message": "Corpo da requisição vazio."}
        
        # Processa os dados
        json_data = parse_webhookdata_json(body_str)

        # Cria JSON na memória
        filename, json_file = create_json_in_memory(json_data)

        # Envia para o Data Lake
        response = send_to_datalake(filename, json_file)

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
    Cria um JSON na memória e retorna um BytesIO com o conteúdo.
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    json_bytes = BytesIO(json_str.encode('utf-8'))  # Cria um BytesIO

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contact_{timestamp}.json"

    return filename, json_bytes  # Retorna nome e conteúdo em bytes

def send_to_datalake(filename: str, file: BytesIO):
    """
    Envia um arquivo JSON para a API do Data Lake no formato multipart/form-data.
    """
    url = "https://app-orion-dev.azurewebsites.net/api/azure-datalake/uploadfile"
    params = {
        "storage_account_name": "saactivecampaign",
        "file_system_name": "bronze",
        "directory_name": "source_ac"
    }
    headers = {
        "accept": "application/json"
    }

    # Move o ponteiro para o início do arquivo
    file.seek(0)

    files = {
        "file": (filename, file.read(), "application/json")  # Corrige envio
    }

    response = requests.post(url, params=params, headers=headers, files=files)

    return response.json()