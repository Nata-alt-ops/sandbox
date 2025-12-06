from fastapi import FastAPI, HTTPException
import sqlite3
app = FastAPI()

# Создание базы данных и таблиц
def create_db():
    conn = sqlite3.connect("parfume.db")
    cursor = conn.cursor()
    # Включаем поддержку внешних ключей
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Parfumes (
            parfume_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            price REAL NOT NULL,
            size TEXT NOT NULL,
            description TEXT,
            country TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK (user_type IN ('user', 'admin')),
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Favorites (
            favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            parfume_id INTEGER NOT NULL,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (parfume_id) REFERENCES Parfumes(parfume_id) ON DELETE CASCADE
        )
    ''')   
    conn.commit()
    conn.close()
create_db()

# Подключение к базе данных
def connect_to_db():
    conn = sqlite3.connect("parfume.db")
    # Включаем внешние ключи при каждом подключении
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Регистрация
@app.post("/register")
def register_user(username: str, password: str, email: str, full_name: str):
    """Регистрация нового пользователя (автоматически ставит user_type='user')"""
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
        cursor.execute(
            "INSERT INTO Users (username, password, email, full_name, user_type) VALUES (?, ?, ?, ?, ?)", 
            (username, password, email, full_name, "user")
        )
        conn.commit()
        conn.close()
        return {"message": "Вы успешно зарегистрировались"}
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Не удалось зарегистрироваться: {str(e)}")

# Авторизация 
@app.post("/login")
def login_user(username: str, password: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if not user:
            raise HTTPException(status_code=401, detail="Такого пользователя не существует")
        if user[2] == password:
            return {"message": "Вы успешно вошли в аккаунт"}
        else:
            raise HTTPException(status_code=401, detail="Неверный пароль")  
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Ошибка при авторизации: {str(e)}")

# Парфюм
@app.get("/see_parfumes")
def get_parfumes():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Parfumes")
    parfumes = cursor.fetchall()
    conn.close()
    return [
        {
            "id": p[0], 
            "brand": p[1], 
            "name": p[2], 
            "gender": p[3], 
            "price": p[4], 
            "size": p[5], 
            "description": p[6], 
            "country": p[7]
        } for p in parfumes]

@app.get("/see_parfumes_user/{parfume_id}")
def get_parfume(parfume_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Parfumes WHERE parfume_id = ?", (parfume_id,))
    parfume = cursor.fetchone()
    conn.close()
    if not parfume:
        raise HTTPException(status_code=404, detail="Не удалось найти парфюм")
    return {
        "id": parfume[0], 
        "brand": parfume[1], 
        "name": parfume[2], 
        "gender": parfume[3], 
        "price": parfume[4], 
        "size": parfume[5], 
        "description": parfume[6], 
        "country": parfume[7]
    }

@app.post("/new_parfume")
def create_parfume(brand: str, name: str, gender: str, price: float, size: str, country: str, description: str = ""):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Parfumes (brand, name, gender, price, size, country, description) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (brand, name, gender, price, size, country, description))
        conn.commit()
        return {"message": "Новый парфюм добавлен"}
    except Exception:
        return {"message": "Не удалось добавить парфюм"}
    finally:
        conn.close()

@app.delete("/delete_parfume/{parfume_id}")
def delete_parfume(parfume_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Parfumes WHERE parfume_id = ?", (parfume_id,))
        conn.commit()
        return {"message": "Парфюм удален"}
    except Exception:
        return {"message": "Не удалось удалить парфюм"}
    finally:
        conn.close()

@app.put("/update_parfume/{parfume_id}")
def update_parfume(parfume_id: int, brand: str, name: str, gender: str, price: float, size: str, country: str, description: str = ""):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Parfumes SET brand = ?, name = ?, gender = ?, price = ?, size = ?, country = ?, description = ? WHERE parfume_id = ?", 
                       (brand, name, gender, price, size, country, description, parfume_id))
        conn.commit()
        return {"message": "Информация о парфюме обновлена"}
    except Exception:
        return {"message": "Не удалось обновить информацию о парфюме"}
    finally:
        conn.close()

# Пользователи
@app.get("/see_users")
def get_users():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, full_name, user_type, created_date FROM Users")
    users = cursor.fetchall()
    conn.close()
    return [
        {
            "id": u[0], 
            "username": u[1], 
            "email": u[2], 
            "full_name": u[3], 
            "user_type": u[4], 
            "created_date": u[5]
        } for u in users]

@app.get("/see_user/{user_id}")
def get_user(user_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, full_name, user_type, created_date FROM Users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user[0], 
        "username": user[1], 
        "email": user[2], 
        "full_name": user[3], 
        "user_type": user[4], 
        "created_date": user[5]
    }

@app.post("/new_user")
def create_user(username: str, password: str, email: str, full_name: str, user_type: str = "user"):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, password, email, full_name, user_type) VALUES (?, ?, ?, ?, ?)", 
                       (username, password, email, full_name, user_type))
        conn.commit()
        return {"message": "Новый пользователь создан"}
    except Exception as e:
        return {"message": f"Не удалось создать нового пользователя: {str(e)}"}
    finally:
        conn.close()

@app.delete("/delete_user/{user_id}")
def delete_user(user_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
        conn.commit()
        return {"message": "Пользователь удален"}
    except Exception:
        return {"message": "Не удалось удалить пользователя"}
    finally:
        conn.close()

@app.put("/update_user/{user_id}")
def update_user(user_id: int, username: str, password: str, email: str, full_name: str, user_type: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET username = ?, password = ?, email = ?, full_name = ?, user_type = ? WHERE user_id = ?", 
                       (username, password, email, full_name, user_type, user_id))
        conn.commit()
        return {"message": "Информация о пользователе обновлена"}
    except Exception:
        return {"message": "Не удалось обновить информацию о пользователе"}
    finally:
        conn.close()

# Избранное
@app.get("/see_favorites_user/{user_id}")
def get_favorites(user_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.favorite_id, p.parfume_id, p.brand, p.name, p.gender, p.price, p.size, p.description, p.country
        FROM Favorites f 
        JOIN Parfumes p ON f.parfume_id = p.parfume_id 
        WHERE f.user_id = ?
    """, (user_id,))
    favorites = cursor.fetchall()
    conn.close()
    return [{
        "favorite_id": f[0], 
        "parfume_id": f[1], 
        "brand": f[2],
        "name": f[3],
        "gender": f[4],
        "price": f[5],
        "size": f[6],
        "description": f[7],
        "country": f[8]
    } for f in favorites]

@app.post("/new_favorites_user")
def add_favorite(user_id: int, parfume_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Favorites (user_id, parfume_id) VALUES (?, ?)", (user_id, parfume_id))
        conn.commit()
        return {"message": "Добавлен в Избранное"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Не удалось добавить в избранное")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.delete("/delete_favorites_user/{favorite_id}")
def delete_favorite(favorite_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Favorites WHERE favorite_id = ?", (favorite_id,))
        conn.commit()
        return {"message": "Запись о избранном у пользователя удалена"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.delete("/delete_favorites/user/{user_id}/parfume/{parfume_id}")
def delete_favorite_by_user_parfume(user_id: int, parfume_id: int):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Favorites WHERE user_id = ? AND parfume_id = ?", (user_id, parfume_id))
        conn.commit()
        return {"message": "Парфюм удален из избранного"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)