import psycopg2

def create_db(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phones (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                phone VARCHAR(20) NOT NULL
            )
        """)
        conn.commit()

def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, email)
            VALUES (%s, %s, %s) RETURNING id
        """, (first_name, last_name, email))
        client_id = cursor.fetchone()[0]
        
        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)
        
        conn.commit()
        return client_id

def add_phone(conn, client_id, phone):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO phones (client_id, phone)
            VALUES (%s, %s)
        """, (client_id, phone))
        conn.commit()

def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cursor:
        if first_name:
            cursor.execute("UPDATE clients SET first_name = %s WHERE id = %s", (first_name, client_id))
        if last_name:
            cursor.execute("UPDATE clients SET last_name = %s WHERE id = %s", (last_name, client_id))
        if email:
            cursor.execute("UPDATE clients SET email = %s WHERE id = %s", (email, client_id))
        if phones is not None:
            cursor.execute("DELETE FROM phones WHERE client_id = %s", (client_id,))
            for phone in phones:
                add_phone(conn, client_id, phone)
        
        conn.commit()

def delete_phone(conn, client_id, phone):
    with conn.cursor() as cursor:
        cursor.execute("""
            DELETE FROM phones WHERE client_id = %s AND phone = %s
        """, (client_id, phone))
        conn.commit()

def delete_client(conn, client_id):
    with conn.cursor() as cursor:cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
    conn.commit()

def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    query = "SELECT c.id, c.first_name, c.last_name, c.email, p.phone FROM clients c LEFT JOIN phones p ON c.id = p.client_id WHERE"
    conditions = []
    params = []
    
    if first_name:
        conditions.append(" c.first_name ILIKE %s")
        params.append(f"%{first_name}%")
    if last_name:
        conditions.append(" c.last_name ILIKE %s")
        params.append(f"%{last_name}%")
    if email:
        conditions.append(" c.email ILIKE %s")
        params.append(f"%{email}%")
    if phone:
        conditions.append(" p.phone ILIKE %s")
        params.append(f"%{phone}%")
    
    if not conditions:
        return []  # No conditions provided
    
    query += " AND".join(conditions)
    
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()

# Пример использования
with psycopg2.connect(database="clients_db", user="postgres", password="postgres") as conn:
    create_db(conn)
    
    client_id = add_client(conn, 'Иван', 'Иванов', 'ivan@example.com', ['1234567890', '0987654321'])
    print(f'Добавлен клиент с ID: {client_id}')
    
    add_phone(conn, client_id, '1122334455')
    print('Добавлен новый телефон для клиента.')
    
    change_client(conn, client_id, first_name='Иван', last_name='Петров')
    print('Данные клиента изменены.')
    
    clients = find_client(conn, first_name='Иван')
    print('Найденные клиенты:', clients)
    
    delete_phone(conn, client_id, '1234567890')
    print('Телефон удален.')
    
    delete_client(conn, client_id)
    print('Клиент удален.')

conn.close()