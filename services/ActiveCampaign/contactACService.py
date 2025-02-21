from fastapi import APIRouter, Request
import logging
import urllib.parse
import json
import io
import datetime
import requests


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


def create_json_in_memory(data):
    """
    Cria um arquivo JSON na memória usando BytesIO.
    """
    json_bytes = io.BytesIO()
    json.dump(data, json_bytes, ensure_ascii=False, indent=4)
    json_bytes.seek(0)  # Reseta o ponteiro para o início do arquivo

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contact_{timestamp}.json"

    return filename, json_bytes.getvalue() # Retorna o nome do arquivo e os bytes do JSON

def send_to_datalake(filename, json_bytes):
    """
    Envia o arquivo JSON para a API do Data Lake no formato multipart/form-data.
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

    # 🔥 Certifica que o arquivo é enviado como binário
    files = {"file": (filename, io.BytesIO(json_bytes), "application/json")}

    response = requests.post(url, headers=headers, params=params, files=files)

    if response.status_code == 200:
        response_json = response.json()
        logging.info(f"Arquivo enviado com sucesso para o Data Lake: {response_json}")
        return response_json  # Retorna a resposta real da API do Data Lake
    else:
        logging.error(f"Erro ao enviar arquivo para o Data Lake: {response.status_code}, {response.text}")
        return {
            "status": "error",
            "code": response.status_code,
            "message": response.text
        }