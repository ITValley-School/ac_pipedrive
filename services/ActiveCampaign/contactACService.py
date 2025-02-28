from fastapi import APIRouter, Request, UploadFile, File, HTTPException
import logging
import urllib.parse
import json
from io import BytesIO
import datetime
import requests
import os
from typing import Optional


router = APIRouter()

# ActiveCampaign API configuration
AC_API_URL = os.getenv("AC_API_URL")
AC_API_KEY = os.getenv("AC_API_KEY")

# Define UTM custom field names to look for
UTM_FIELDS = [
    'UTM Campaign',
    'UTM Medium',
    'UTM Content',
    'UTM Source',
    'UTM Term'
]

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


@router.get("/api/contact/{contact_id}")
async def get_contact_with_utm_fields(contact_id: str):
    """
    Fetch contact details from ActiveCampaign including custom UTM fields
    
    :param contact_id: The ActiveCampaign contact ID
    :return: Contact details with UTM custom fields
    """
    try:
        if not AC_API_KEY:
            raise HTTPException(status_code=500, detail="ActiveCampaign API key not configured")
        
        # Get basic contact data
        contact_url = f"{AC_API_URL}/api/3/contacts/{contact_id}"
        headers = {"Api-Token": AC_API_KEY}
        
        contact_response = requests.get(contact_url, headers=headers)
        contact_response.raise_for_status()
        
        contact_data = contact_response.json().get('contact')
        if not contact_data:
            raise HTTPException(status_code=404, detail="Contact not found")
        
#apenas para saber quais dados ele me manda
        #print(contact_data)

        #apenas para saber quais dados ele me manda
        #print(contact_data)

        # Get all field values for this contact
        field_values_url = f"{AC_API_URL}/api/3/contacts/{contact_id}/fieldValues"
        field_values_response = requests.get(field_values_url, headers=headers)
        field_values_response.raise_for_status()
        
        #apenas para saber quais dados ele me manda
        #print(field_values_response.json())

        
        # Get all custom fields to match IDs with names
        fields_url = f"{AC_API_URL}/api/3/fields"
        fields_response = requests.get(fields_url, headers=headers)
        fields_response.raise_for_status()
        
        custom_fields = fields_response.json().get('fields', [])
        
        # Correctly access the fieldValues from the response
        field_values = field_values_response.json().get('fieldValues', [])
        
        # Create a dictionary to map field IDs to field information
        field_id_to_info = {}
        for field in custom_fields:
            field_id_to_info[field.get('id')] = field
        
        # Map field values to their names for UTM fields
        utm_fields = {}
        all_custom_fields = {}
        
        for field_value in field_values:
            field_id = field_value.get('field')
            if field_id in field_id_to_info:
                field_info = field_id_to_info[field_id]
                field_title = field_info.get('title')
                
                # Add to UTM fields if it matches our list
                if field_title in UTM_FIELDS:
                    utm_fields[field_title] = field_value.get('value')
                
                # Also collect all custom fields for reference
                all_custom_fields[field_title] = field_value.get('value')
        
        # Create result with contact data and UTM fields
        result = {
            "contact": contact_data,
            "utmFields": utm_fields,
            "allCustomFields": all_custom_fields
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ActiveCampaign contact: {str(e)}")
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
        raise HTTPException(status_code=status_code, detail=f"Failed to fetch contact details: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error when fetching contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    
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