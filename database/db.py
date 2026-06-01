
import os

import aiosqlite

DB_NAME = "data/database.db"


async def create_tables():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            surname TEXT,
            city TEXT,
            age INTEGER,
            education TEXT,
            university TEXT,
            status TEXT DEFAULT 'new',
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS rooms(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dormitory_name TEXT,
            room_number TEXT,
            price INTEGER,
            status TEXT DEFAULT 'available'
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reservations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        DELETE FROM rooms
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM rooms
            GROUP BY dormitory_name, room_number
        )
        """)

        await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_unique
        ON rooms(dormitory_name, room_number)
        """)

        await db.execute("""
        INSERT OR IGNORE INTO rooms(dormitory_name, room_number, price)
        VALUES
            ('Akademik A', '101', 700),
            ('Akademik A', '102', 650),
            ('Akademik A', '103', 680),
            ('Akademik A', '104', 720),
            ('Akademik B', '201', 750),
            ('Akademik B', '202', 770),
            ('Akademik B', '203', 800),
            ('Akademik B', '204', 790),
            ('Akademik C', '301', 800),
            ('Akademik C', '302', 850),
            ('Akademik C', '303', 820),
            ('Akademik D', '401', 900),
            ('Akademik D', '402', 950),
            ('Akademik D', '403', 920),
            ('Akademik E', '501', 600),
            ('Akademik E', '502', 620)
        """)

        await db.commit()

        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]

        if "status" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'new'")
            await db.commit()

        if "is_admin" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            await db.commit()

        if "is_blocked" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
            await db.commit()

        if "age" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN age INTEGER")
            await db.commit()

        if "education" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN education TEXT")
            await db.commit()

        if "university" not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN university TEXT")
            await db.commit()

        cursor = await db.execute("PRAGMA table_info(reservations)")
        columns = await cursor.fetchall()
        reservation_columns = [column[1] for column in columns]

        if "created_at" not in reservation_columns:
            # SQLite does not allow adding a column with a non-constant default via ALTER TABLE
            # Add the column without default, then backfill existing rows with CURRENT_TIMESTAMP
            await db.execute("ALTER TABLE reservations ADD COLUMN created_at TEXT")
            await db.execute("UPDATE reservations SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            await db.commit()


async def add_user(telegram_id, name=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users(telegram_id, name)
            VALUES (?, ?)
            """,
            (telegram_id, name)
        )
        await db.commit()


async def update_user(telegram_id, name, surname, city, age=None, education=None, university=None):
    async with aiosqlite.connect(DB_NAME) as db:
        # Mark user as pending approval after they fill registration data
        await db.execute(
            """
            UPDATE users
            SET name=?, surname=?, city=?, age=?, education=?, university=?, status = 'pending'
            WHERE telegram_id=?
            """,
            (name, surname, city, age, education, university, telegram_id)
        )
        await db.commit()


async def set_user_status(telegram_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET status = ?
            WHERE telegram_id = ?
            """,
            (status, telegram_id)
        )
        await db.commit()


async def get_user_by_telegram_id(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )
        return await cursor.fetchone()


async def get_dormitories():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT DISTINCT dormitory_name
            FROM rooms
            ORDER BY dormitory_name
            """
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_rooms_by_dormitory(dormitory_name):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rooms
            WHERE dormitory_name = ?
            ORDER BY room_number
            """,
            (dormitory_name,)
        )
        return await cursor.fetchall()


async def get_room_by_number(room_number):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rooms
            WHERE room_number = ?
            """,
            (room_number,)
        )
        return await cursor.fetchone()


async def get_room_by_id(room_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rooms
            WHERE id = ?
            """,
            (room_id,)
        )
        return await cursor.fetchone()


async def get_reservations_by_user_id(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.id, r.status, r.created_at, rooms.dormitory_name, rooms.room_number, rooms.price
            FROM reservations AS r
            JOIN rooms ON rooms.id = r.room_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
            """,
            (user_id,)
        )
        return await cursor.fetchall()


async def get_all_reservations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.id, r.status, r.created_at, u.id AS user_id, u.name, u.surname, u.telegram_id, rooms.id AS room_id, rooms.dormitory_name, rooms.room_number, rooms.price
            FROM reservations AS r
            JOIN users AS u ON u.id = r.user_id
            JOIN rooms ON rooms.id = r.room_id
            ORDER BY r.created_at DESC
            """
        )
        return await cursor.fetchall()


async def get_pending_reservations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.id, r.status, r.created_at, u.id AS user_id, u.name, u.surname, u.telegram_id, rooms.id AS room_id, rooms.dormitory_name, rooms.room_number, rooms.price
            FROM reservations AS r
            JOIN users AS u ON u.id = r.user_id
            JOIN rooms ON rooms.id = r.room_id
            WHERE r.status = 'pending'
            ORDER BY r.created_at ASC
            """
        )
        return await cursor.fetchall()


async def get_reservation_by_id(reservation_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                r.id,
                r.user_id,
                r.room_id,
                r.status,
                r.created_at,
                u.telegram_id,
                u.name,
                u.surname,
                rooms.dormitory_name,
                rooms.room_number,
                rooms.price
            FROM reservations AS r
            JOIN users AS u ON u.id = r.user_id
            JOIN rooms ON rooms.id = r.room_id
            WHERE r.id = ?
            """,
            (reservation_id,)
        )
        return await cursor.fetchone()


async def update_user_profile_field(telegram_id, field, value):
    allowed_fields = {"city", "age", "education", "university"}
    if field not in allowed_fields:
        raise ValueError("Unsupported profile field")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"""
            UPDATE users
            SET {field} = ?
            WHERE telegram_id = ?
            """,
            (value, telegram_id)
        )
        await db.commit()


async def update_reservation_status(reservation_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (status, reservation_id)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, telegram_id, name, surname, city, age, education, university, status, is_admin, is_blocked
            FROM users
            ORDER BY id
            """
        )
        return await cursor.fetchall()


async def set_user_blocked(telegram_id, is_blocked):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET is_blocked = ?
            WHERE telegram_id = ?
            """,
            (1 if is_blocked else 0, telegram_id)
        )
        await db.commit()


async def is_user_blocked(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT is_blocked
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return bool(row[0]) if row else False


async def set_user_admin(telegram_id, is_admin):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET is_admin = ?
            WHERE telegram_id = ?
            """,
            (1 if is_admin else 0, telegram_id)
        )
        await db.commit()


async def get_user_by_id(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        return await cursor.fetchone()


async def set_room_available(room_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE rooms
            SET status = 'available'
            WHERE id = ?
            """,
            (room_id,)
        )
        await db.commit()


async def set_room_reserved(room_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE rooms
            SET status = 'reserved'
            WHERE id = ?
            """,
            (room_id,)
        )
        await db.commit()


async def add_reservation(user_id, room_id, status="pending"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO reservations(user_id, room_id, status)
            VALUES (?, ?, ?)
            """,
            (user_id, room_id, status)
        )
        await db.commit()


async def get_registered_users():
    """Get all users with status 'registered' for admin view."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, telegram_id, name, surname, city, age, education, university, status, is_admin, is_blocked
            FROM users
            WHERE status = 'registered'
            ORDER BY name
            """
        )
        return await cursor.fetchall()
