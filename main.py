from fastapi import FastAPI, HTTPException, Form, Request
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
async def activecampaign_webhook(
    request: Request,
    url: str = Form(None),
    type: str = Form(None),
    date_time: str = Form(None),
    initiated_by: str = Form(None),
    initiated_from: str = Form(None),
    list: str = Form(None),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    contact_first_name: str = Form(None),
    contact_last_name: str = Form(None),
    contact_utm_campaign: str = Form(None),
    contact_utm_source: str = Form(None),
    contact_utm_medium: str = Form(None),
    contact_utm_content: str = Form(None)
):
    """
    Webhook do ActiveCampaign que recebe leads e os cria no Pipedrive automaticamente.
    Agora aceita JSON e application/x-www-form-urlencoded.
    """
    try:
        # 🔍 Verificar se os dados vieram como JSON ou como Form URL Encoded
        payload = {}
        if request.headers.get("content-type") == "application/json":
            payload = await request.json()
        else:
            # Construindo um dicionário dos dados recebidos via Form
            payload = {
                "contact": {
                    "email": contact_email,
                    "phone": contact_phone,
                    "firstName": contact_first_name or "Desconhecido",
                    "lastName": contact_last_name or "",
                    "utm_campaign": contact_utm_campaign or "",
                    "utm_source": contact_utm_source or "",
                    "utm_medium": contact_utm_medium or "",
                    "utm_content": contact_utm_content or "",
                    "list_id": list
                }
            }

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



# 🔹 Criamos dois webhooks específicos para cada lista do ActiveCampaign
@app.post("/webhook/pos_ia")
async def webhook_pos_ia(
    request: Request,
    url: str = Form(None),
    type: str = Form(None),
    date_time: str = Form(None),
    initiated_by: str = Form(None),
    initiated_from: str = Form(None),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    contact_first_name: str = Form(None),
    contact_last_name: str = Form(None),
    contact_utm_campaign: str = Form(None),
    contact_utm_source: str = Form(None),
    contact_utm_medium: str = Form(None),
    contact_utm_content: str = Form(None)
):
    """Webhook para leads da lista Pós IA."""
    return await process_webhook(
        request=request,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_first_name=contact_first_name,
        contact_last_name=contact_last_name,
        contact_utm_campaign=contact_utm_campaign,
        contact_utm_source=contact_utm_source,
        contact_utm_medium=contact_utm_medium,
        contact_utm_content=contact_utm_content,
        pipeline_id=3,  # Funil Pós IA
        stage_id=11  # Estágio: Lead Frio
    )


@app.post("/webhook/escola_ia")
async def webhook_escola_ia(
    request: Request,
    url: str = Form(None),
    type: str = Form(None),
    date_time: str = Form(None),
    initiated_by: str = Form(None),
    initiated_from: str = Form(None),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    contact_first_name: str = Form(None),
    contact_last_name: str = Form(None),
    contact_utm_campaign: str = Form(None),
    contact_utm_source: str = Form(None),
    contact_utm_medium: str = Form(None),
    contact_utm_content: str = Form(None)
):
    """Webhook para leads da lista Escola IA."""
    return await process_webhook(
        request=request,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_first_name=contact_first_name,
        contact_last_name=contact_last_name,
        contact_utm_campaign=contact_utm_campaign,
        contact_utm_source=contact_utm_source,
        contact_utm_medium=contact_utm_medium,
        contact_utm_content=contact_utm_content,
        pipeline_id=2,  # Funil Escola IA
        stage_id=6  # Estágio: Lead Frio
    )

# 🔹 Função genérica para processar os dados recebidos
async def process_webhook(
    request: Request,
    contact_email: str,
    contact_phone: str,
    contact_first_name: str,
    contact_last_name: str,
    contact_utm_campaign: str,
    contact_utm_source: str,
    contact_utm_medium: str,
    contact_utm_content: str,
    pipeline_id: int,
    stage_id: int
):
    """
    Processa o webhook recebido e cria o contato e o negócio no Pipedrive.
    """
    try:
        # 🔍 Debug: Ver o que está chegando
        payload = {}
        if request.headers.get("content-type") == "application/json":
            payload = await request.json()
        else:
            payload = {
                "contact": {
                    "email": contact_email,
                    "phone": contact_phone,
                    "firstName": contact_first_name or "Desconhecido",
                    "lastName": contact_last_name or "",
                    "utm_campaign": contact_utm_campaign or "",
                    "utm_source": contact_utm_source or "",
                    "utm_medium": contact_utm_medium or "",
                    "utm_content": contact_utm_content or "",
                }
            }

        print(f"🔍 Payload Recebido: {json.dumps(payload, indent=4)}")

        # Extrair informações do contato
        contact_data = payload.get("contact", {})

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

        # Criar dicionário correto para o pipeline
        pipeline_info = {
            "pipeline_id": pipeline_id,
            "stage_id": stage_id
        }

        # Criar deal no funil correto
        deal_title = f"Negócio com {contact_info['utm_campaign'] if contact_info['utm_campaign'] else 'Lead'}"
        pipedrive.create_deal_with_pipeline(
            person_id=person_id,
            pipeline_info=pipeline_info,  # ✅ Passando o dicionário corretamente
            title=deal_title
        )

        return {"message": "Contato e negócio criados com sucesso!", "contact_id": person_id}

    except Exception as e:
        print(f"❌ Erro no Webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))