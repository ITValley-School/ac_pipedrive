import requests
from config.settings import ACTIVE_CAMPAIGN_API_KEY, ACTIVE_CAMPAIGN_API_URL, UTM_FIELDS

def fetch_field_values(field_url):
    """Busca os valores dos campos personalizados de um contato no ActiveCampaign."""
    headers = {
        "Api-Token": ACTIVE_CAMPAIGN_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(field_url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar fieldValues: {response.status_code} - {response.text}")
        return {}

    field_values = response.json().get("fieldValues", [])
    return {fv["field"]: fv["value"] for fv in field_values}

def get_contacts_by_list(list_id: int):
    """Busca contatos do ActiveCampaign e extrai as UTMs corretamente."""
    headers = {
        "Api-Token": ACTIVE_CAMPAIGN_API_KEY,
        "Content-Type": "application/json"
    }

    url = f"{ACTIVE_CAMPAIGN_API_URL}?listid={list_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Erro ao buscar contatos: {response.status_code}", "details": response.text}

    contacts = response.json().get("contacts", [])
    formatted_contacts = []

    for contact in contacts:
        print(f"\n🔍 Contato Bruto Recebido: {contact}\n")

        email = contact.get("email", "")
        phone = contact.get("phone", "")
        first_name = contact.get("firstName", "")
        last_name = contact.get("lastName", "")
        created_at = contact.get("created_timestamp", "")

        utm_campaign = utm_medium = utm_content = utm_source = ""
        field_values_url = contact.get("links", {}).get("fieldValues")

        if field_values_url:
            field_values = fetch_field_values(field_values_url)
            utm_campaign = field_values.get(UTM_FIELDS["utm_campaign"], "")
            utm_medium = field_values.get(UTM_FIELDS["utm_medium"], "")
            utm_content = field_values.get(UTM_FIELDS["utm_content"], "")
            utm_source = field_values.get(UTM_FIELDS["utm_source"], "")

        formatted_contacts.append({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "created_at": created_at,
            "utm_campaign": utm_campaign,
            "utm_medium": utm_medium,
            "utm_content": utm_content,
            "utm_source": utm_source
        })

    return {"contacts": formatted_contacts}