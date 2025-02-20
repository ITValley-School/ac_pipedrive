from fastapi import FastAPI, HTTPException
from services import activecampaign, pipedrive
from config.settings import LIST_TO_PIPELINE
import json

app = FastAPI()

@app.get("/contacts/{list_id}")
def get_activecampaign_contacts(list_id: int):
    return activecampaign.get_contacts_by_list(list_id)

@app.post("/sync_contacts/{list_id}/{pipeline_id}")
def sync_contacts(list_id: int, pipeline_id: int):
    contacts_response = activecampaign.get_contacts_by_list(list_id)
    
    if "error" in contacts_response:
        return contacts_response
        
    contacts = contacts_response.get("contacts", [])
    if not contacts:
        return {"message": "Nenhum contato novo encontrado."}

    results = []

    for contact in contacts:
        person_id, error = pipedrive.create_person(contact)
        
        if error:
            results.append({"email": contact["email"], "error": error})
            continue

        if person_id:
            deal_response = pipedrive.create_deal(
                person_id, 
                contact["utm_campaign"], 
                contact["utm_source"], 
                pipeline_id
            )
            results.append({
                "email": contact["email"], 
                "person_id": person_id, 
                "deal": deal_response
            })

    return {"message": "Sincronização concluída", "results": results}

@app.post("/webhook/activecampaign")
async def activecampaign_webhook(payload: dict):
    """
    Webhook do ActiveCampaign que recebe leads e os cria no Pipedrive automaticamente.
    """
    try:

        # 🔍 Debug: Ver o que está chegando
        print(f"🔍 Payload Recebido: {json.dumps(payload, indent=4)}")

        # Extrair informações do webhook
        contact_data = payload.get("contact", {})
        list_id = str(contact_data.get("list_id"))

        print(f"📌 List ID Recebido: {list_id}")  # Debug para ver se está pegando certo

        if not list_id or list_id not in LIST_TO_PIPELINE:
            return {"error": "Lista não configurada para sincronização."}

        # Preparar dados do contato
        contact_info = {
            "email": contact_data.get("email", ""),
            "phone": contact_data.get("phone", ""),
            "first_name": contact_data.get("firstName", "Desconhecido"),
            "last_name": contact_data.get("lastName", ""),
            "utm_campaign": contact_data.get("utm_campaign", ""),
            "utm_source": contact_data.get("utm_source", ""),
            "utm_medium": contact_data.get("utm_medium", ""),
            "utm_content": contact_data.get("utm_content", "")
        }

        # Criar contato no Pipedrive
        person_id = pipedrive.create_contact_with_custom_fields(contact_info)

        # Criar deal no pipeline correto
        pipeline_info = LIST_TO_PIPELINE[list_id]
        deal_title = f"Negócio com {contact_info['utm_campaign'] if contact_info['utm_campaign'] else 'Lead'}"
        
        pipedrive.create_deal_with_pipeline(
            person_id=person_id,
            pipeline_info=pipeline_info,
            title=deal_title
        )

        return {"message": "Contato e negócio criados com sucesso!", "contact_id": person_id}

    except Exception as e:
        print(f"❌ Erro no Webhook: {str(e)}")  # Debug
        raise HTTPException(status_code=500, detail=str(e))