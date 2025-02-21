from fastapi import APIRouter, Request


router = APIRouter()

async def webhook(request: Request):
    data = await request.json()
    # Processa os dados recebidos do ActiveCampaign
    print(f"Received webhook data: {data}")
    # Adicione sua lógica aqui para manipular os dados
    return {"status": "success"}
