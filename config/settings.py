import os
from dotenv import load_dotenv

load_dotenv()

# Configuração das APIs
ACTIVE_CAMPAIGN_API_URL = os.getenv("AC_API_URL") + "/api/3/contacts"
ACTIVE_CAMPAIGN_API_KEY = os.getenv("AC_API_KEY")
AC_LIST_ID = os.getenv("AC_LIST_ID")

PIPEDRIVE_API_URL = os.getenv("PIPEDRIVE_API_URL") + "/persons"
PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")
PIPEDRIVE_API_URL_deal = 'https://suaempresa.pipedrive.com/api/v1/deals'

PIPELINE_STAGE_ID = 1

# Mapeamento de listas para funis
LIST_TO_PIPELINE = {
    "61": {"pipeline_id": 3, "stage_id": 31},  # Lista 61 → Funil Pós IA (estágio: Lead Frio)
    "70": {"pipeline_id": 2, "stage_id": 30}   # Lista 70 → Funil Escola IA (estágio: Lead Frio)
}

UTM_FIELDS = {
    "utm_campaign": "16",
    "utm_medium": "18",
    "utm_content": "19",
    "utm_source": "17",
}

CUSTOM_FIELDS = {
    "utm_campaign": "0722ce86e5e4d808c95f3c164aff5d396761222d",
    "utm_source": "98b877f5c8ed5d7a0e6aae18b9dfb290380181ea",
    "utm_medium": "288859c4fdfcbbf7d50a5e0a036f5d0d8013f0b0",
    "utm_content": "ec5ea0971fbca9f9250d4cf2ccb7ba5b11e59fde",
    "email_personalizado": "cbcda7fdd568ebeb951bf22f08196489546cd038",
    "telefone_personalizado": "25b40c8ab005c52701d02831eafe90429b2f139a",
}
