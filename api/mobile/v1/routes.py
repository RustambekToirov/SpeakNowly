from fastapi import APIRouter
from api.mobile.v1.views import SomeView  # Импортируйте ваши представления

router = APIRouter()

@router.get("/some-endpoint")
async def get_some_data():
    return await SomeView.get_data()  # Пример вызова метода из представления

@router.post("/some-endpoint")
async def create_some_data(data: dict):
    return await SomeView.create_data(data)  # Пример вызова метода из представления

# Добавьте другие маршруты по мере необходимости
