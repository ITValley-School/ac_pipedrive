from fastapi import FastAPI
from services import activecampaign, pipedrive

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