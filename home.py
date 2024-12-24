from fastapi import FastAPI, HTTPException

#Библиотека на валидацию параметров
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime
import uvicorn
import re
import socket

app = FastAPI()

users = []


#Запрос на получение списка пользователей
@app.get("/users", summary="Получение списка пользователей", tags=["Основные ручки"])
def read_users():
    return users


#Запрос на получение информации  конкретном пользователе
@app.get("/users/{user_id}", summary="Получение пользователя", tags=["Основные ручки"])
def get_user(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Пользователь не найден!!!")


#Валидация параметров запроса
class UserSchema(BaseModel):
    lastName: str = Field(min_length=2, max_length=25)
    firstName: str = Field(min_length=2, max_length=25)
    middleName: str = Field(min_length=3, max_length=25)
    birthDay: str
    email: EmailStr
    phone: str

    #Запрещать передавать дополнительные параметры
    model_config = ConfigDict(extra="forbid")

    @field_validator('birthDay')
    def validate_birth_day(cls, value):
        # Проверка формата даты
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            raise ValueError('Дата рождения должна быть в формате DD/MM/YYYY')
        # Попытка преобразовать строку в дату
        try:
            datetime.strptime(value, '%d/%m/%Y')
        except ValueError:
            raise ValueError('Неверная дата. Убедитесь, что дата существует.')
        return value

#Запрос на создание пользователя
@app.post("/create/user", summary="Создание участника", tags=["Основные ручки"])
def create_user(new_user: UserSchema):
    new_id = len(users) + 1  # Генерация нового ID
    users.append({
        "id": new_id,
        "lastName": new_user.lastName,
        "firstName": new_user.firstName,
        "middleName": new_user.middleName,
        "birthDay": new_user.birthDay,
        "email": new_user.email,
        "phone": new_user.phone
    })

    return {"success": True, "message": "Пользователь успешно добавлен"}


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))  # Привязка к любому доступному порту
    port = s.getsockname()[1]  # Получение номера порта
    s.close()
    return port


free_port = find_free_port()

if __name__ == "__main__":
    import uvicorn
    host = "127.0.0.1"  # или ваш доступный хост
    port = free_port  # или ваш найденный доступный порт
    uvicorn.run("home:app", host=host, port=port, reload=True)
