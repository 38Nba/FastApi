from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime
import uvicorn
import re
import socket
import csv
from fastapi.responses import FileResponse
import logging
import io

app = FastAPI()

users = []

logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Запрос на получение списка пользователей
@app.get("/users", summary="Получение списка пользователей", tags=["Основные ручки"])
def read_users():
    return users

# Запрос на получение информации о конкретном пользователе
@app.get("/users/{user_id}", summary="Получение пользователя", tags=["Основные ручки"])
def get_user(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Пользователь не найден!!!")

# Валидация параметров запроса
class UserSchema(BaseModel):
    lastName: str
    firstName: str
    middleName: str
    birthDay: str
    email: EmailStr
    phone: str

    model_config = ConfigDict(extra="forbid")

    @field_validator('birthDay')
    def validate_birth_day(cls, value):
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            raise ValueError('Дата рождения должна быть в формате DD/MM/YYYY')
        try:
            datetime.strptime(value, '%d/%m/%Y')
        except ValueError:
            raise ValueError('Неверная дата. Убедитесь, что дата существует.')
        return value

# Запрос на создание пользователя
@app.post("/create/user", summary="Создание участника", tags=["Основные ручки"])
def create_user(new_user: UserSchema):
    new_id = len(users) + 1
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

# Запрос на удаление пользователя
@app.delete("/users/{user_id}", summary="Удаление пользователя", tags=["Основные ручки"])
def delete_user(user_id: int):
    global users
    user_to_delete = next((user for user in users if user["id"] == user_id), None)
    if user_to_delete:
        users = [user for user in users if user["id"] != user_id]
        return {"success": True, "message": "Пользователь успешно удалён"}
    raise HTTPException(status_code=404, detail="Пользователь не найден")

# Запрос на редактирование пользователя
@app.put("/users/{user_id}", summary="Редактирование пользователя", tags=["Основные ручки"])
def update_user(user_id: int, updated_user: UserSchema):
    for user in users:
        if user["id"] == user_id:
            user.update({
                "lastName": updated_user.lastName,
                "firstName": updated_user.firstName,
                "middleName": updated_user.middleName,
                "birthDay": updated_user.birthDay,
                "email": updated_user.email,
                "phone": updated_user.phone
            })
            return {"success": True, "message": "Пользователь успешно обновлён", "user": user}
    raise HTTPException(status_code=404, detail="Пользователь не найден")

# Поиск пользователей
@app.get("/users/search", summary="Поиск пользователей", tags=["Основные ручки"])
def search_users(name: str = None, email: str = None):
    if not name and not email:
        raise HTTPException(status_code=422, detail="Необходимо указать хотя бы один параметр для поиска")
    results = users
    if name:
        results = [user for user in results if name.lower() in user["firstName"].lower()]
    if email:
        results = [user for user in results if email.lower() in user["email"].lower()]
    return results or {"message": "Ни одного пользователя не найдено"}

# Пагинация пользователей
@app.get("/users/paginated", summary="Пагинация списка пользователей", tags=["Основные ручки"])
def get_paginated_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    if skip < 0 or limit < 1:
        raise HTTPException(status_code=422, detail="Invalid skip or limit values")
    return users[skip:skip + limit]

# Экспорт пользователей в CSV
@app.get("/users/export", summary="Экспорт пользователей в CSV", tags=["Дополнительные функции"])
def export_users():
    file_path = "users.csv"
    try:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["id", "lastName", "firstName", "middleName", "birthDay", "email", "phone"])
            writer.writeheader()
            writer.writerows(users)
        return FileResponse(file_path, media_type="text/csv", filename="users.csv")
    except Exception as e:
        logging.error(f"Ошибка при экспорте данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при экспорте данных")

# Статистика пользователей
@app.get("/users/statistics", summary="Статистика пользователей", tags=["Дополнительные функции"])
def user_statistics():
    total_users = len(users)
    ages = []
    for user in users:
        try:
            birth_date = datetime.strptime(user["birthDay"], "%d/%m/%Y")
            age = datetime.now().year - birth_date.year
            ages.append(age)
        except ValueError:
            logging.error(f"Некорректная дата рождения для {user['firstName']} {user['lastName']}")
            continue
    return {
        "total_users": total_users,
        "average_age": sum(ages) / len(ages) if ages else 0,
        "min_age": min(ages) if ages else None,
        "max_age": max(ages) if ages else None
    }

# Логирование запросов
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    logging.info(f"{request.method} {request.url} - {response.status_code}")
    return response

# Поиск свободного порта
def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

free_port = find_free_port()

if __name__ == "__main__":
    import uvicorn
    host = "127.0.0.1"
    port = free_port
    uvicorn.run("home:app", host=host, port=port, reload=True)
