import requests
from fastapi import HTTPException
from config.settings import (
    PIPEDRIVE_API_KEY, 
    PIPEDRIVE_API_URL, 
    PIPEDRIVE_API_URL_deal,
    CUSTOM_FIELDS,
    LIST_TO_PIPELINE
)

def get_first_stage_id(pipeline_id):
    """Obtém o primeiro estágio disponível para o funil especificado."""
    url = f"https://api.pipedrive.com/v1/stages?pipeline_id={pipeline_id}&api_token={PIPEDRIVE_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar estágios do Pipedrive: {response.status_code} - {response.text}")
        return None

    stages = response.json().get("data", [])
    if not stages:
        print(f"❌ Erro: Nenhum estágio encontrado para o funil {pipeline_id}.")
        return None

    return stages[0]["id"]

def create_deal(person_id, utm_campaign, utm_source, pipeline_id):
    """Cria um negócio (deal) no Pipedrive vinculado ao contato (person) no funil correto."""
    stage_id = get_first_stage_id(pipeline_id)
    
    if not stage_id:
        print(f"❌ Erro: Não foi possível encontrar um estágio para o funil {pipeline_id}.")
        return None

    url = f"{PIPEDRIVE_API_URL_deal}/deals?api_token={PIPEDRIVE_API_KEY}"

    custom_fields = {
        CUSTOM_FIELDS.get("utm_campaign"): utm_campaign if utm_campaign else None,
        CUSTOM_FIELDS.get("utm_source"): utm_source if utm_source else None
    }

    filtered_custom_fields = {k: v for k, v in custom_fields.items() if v}

    data = {
        "title": f"Negócio com {utm_campaign if utm_campaign else 'Lead'}",
        "person_id": person_id,  
        "value": 0,
        "pipeline_id": pipeline_id,
        "stage_id": stage_id,  
        "visible_to": 3,  
        **filtered_custom_fields
    }

    print(f"🔹 Enviando negócio para Pipedrive: {data}")

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 201 and response.status_code != 200:
        print(f"❌ Erro ao criar negócio no Pipedrive: {response.status_code} - {response.text}")
        return None

    deal_id = response.json().get("data", {}).get("id")
    print(f"✅ Negócio criado! ID: {deal_id}")
    return deal_id

def create_person(contact_data):
    """Cria uma pessoa no Pipedrive com os dados do contato."""
    data = {
        "name": f"{contact_data['first_name']} {contact_data['last_name']}".strip(),
        "visible_to": 3,
        CUSTOM_FIELDS["email_personalizado"]: contact_data["email"],
        CUSTOM_FIELDS["telefone_personalizado"]: contact_data["phone"],
        CUSTOM_FIELDS["utm_campaign"]: contact_data["utm_campaign"],
        CUSTOM_FIELDS["utm_source"]: contact_data["utm_source"],
        CUSTOM_FIELDS["utm_medium"]: contact_data["utm_medium"],
        CUSTOM_FIELDS["utm_content"]: contact_data["utm_content"]
    }

    url = f"{PIPEDRIVE_API_URL}/persons?api_token={PIPEDRIVE_API_KEY}"
    response = requests.post(url, json=data)

    if response.status_code != 201 and response.status_code != 200:
        return None, response.text

    return response.json().get("data", {}).get("id"), None





# Função para o webhoook
def create_contact_with_custom_fields(contact_data: dict):
    """
    Cria um contato no Pipedrive com campos personalizados.
    """
    contact_payload = {
        "name": f"{contact_data['first_name']} {contact_data['last_name']}".strip(),
        "visible_to": 3,
        CUSTOM_FIELDS["email_personalizado"]: contact_data["email"],
        CUSTOM_FIELDS["telefone_personalizado"]: contact_data["phone"],
        CUSTOM_FIELDS["utm_campaign"]: contact_data["utm_campaign"],
        CUSTOM_FIELDS["utm_source"]: contact_data["utm_source"],
        CUSTOM_FIELDS["utm_medium"]: contact_data["utm_medium"],
        CUSTOM_FIELDS["utm_content"]: contact_data["utm_content"]
    }

    url = f"{PIPEDRIVE_API_URL}/persons?api_token={PIPEDRIVE_API_KEY}"
    response = requests.post(
        url, 
        json=contact_payload, 
        headers={"Content-Type": "application/json"}
    )

    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar contato no Pipedrive: {response.text}"
        )

    return response.json().get("data", {}).get("id")

def create_deal_with_pipeline(person_id: int, pipeline_info: dict, title: str):
    """
    Cria um negócio (Deal) no Pipedrive com pipeline e estágio específicos.
    """
    deal_payload = {
        "title": title,
        "person_id": person_id,
        "value": 0,
        "pipeline_id": pipeline_info["pipeline_id"],
        "stage_id": pipeline_info["stage_id"],
        "visible_to": 3
    }

    url = f"{PIPEDRIVE_API_URL}/deals?api_token={PIPEDRIVE_API_KEY}"
    response = requests.post(
        url, 
        json=deal_payload, 
        headers={"Content-Type": "application/json"}
    )

    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar Deal no Pipedrive: {response.text}"
        )

    return response.json().get("data", {}).get("id")