import os

import aiosqlite

DB_NAME = "data/database.db"

STUDENT_WSG = "wsg"
NON_STUDENT_WSG = "non_wsg"

RESERVATION_PENDING = "pending"
RESERVATION_APPROVED = "approved"
RESERVATION_REJECTED = "rejected"
RESERVATION_WAITING = "waiting"
RESERVATION_CANCELLED = "cancelled"

ISSUE_NEW = "new"
ISSUE_IN_PROGRESS = "in_progress"
ISSUE_RESOLVED = "resolved"


DEFAULT_DORMITORIES = [
    (
        1,
        "Гуртожиток №1",
        "вул. Garbary 2, Бидгощ",
        650,
        80,
        12,
        "",
    ),
    (
        2,
        "Гуртожиток №2",
        "вул. Fordońska 120, Бидгощ",
        700,
        70,
        8,
        "",
    ),
    (
        3,
        "Гуртожиток №3",
        "вул. Toruńska 55, Бидгощ",
        720,
        60,
        5,
        "",
    ),
    (
        4,
        "Гуртожиток №4",
        "вул. Jagiellońska 33, Бидгощ",
        760,
        50,
        3,
        "",
    ),
    (
        5,
        "Гуртожиток №5",
        "вул. Akademicka 9, Бидгощ",
        600,
        90,
        18,
        "",
    ),
]


async def create_tables():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                surname TEXT,
                phone TEXT,
                email TEXT,
                wsg_status TEXT,
                status TEXT DEFAULT 'new',
                is_admin INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS dormitories(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                price INTEGER NOT NULL DEFAULT 0,
                total_places INTEGER NOT NULL DEFAULT 0,
                free_places INTEGER NOT NULL DEFAULT 0,
                photo_url TEXT DEFAULT ''
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dormitory_id INTEGER,
                check_in TEXT,
                check_out TEXT,
                room_type TEXT,
                applicant_status TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(dormitory_id) REFERENCES dormitories(id)
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS issues(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dormitory_id INTEGER,
                category TEXT,
                description TEXT,
                photo_file_id TEXT,
                status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(dormitory_id) REFERENCES dormitories(id)
            )
            """
        )

        await _ensure_columns(
            db,
            "users",
            {
                "phone": "TEXT",
                "email": "TEXT",
                "wsg_status": "TEXT",
                "status": "TEXT DEFAULT 'new'",
                "is_admin": "INTEGER DEFAULT 0",
                "is_blocked": "INTEGER DEFAULT 0",
            },
        )
        await _ensure_columns(
            db,
            "dormitories",
            {
                "address": "TEXT",
                "price": "INTEGER NOT NULL DEFAULT 0",
                "total_places": "INTEGER NOT NULL DEFAULT 0",
                "free_places": "INTEGER NOT NULL DEFAULT 0",
                "photo_url": "TEXT DEFAULT ''",
            },
        )
        await _ensure_columns(
            db,
            "reservations",
            {
                "dormitory_id": "INTEGER",
                "check_in": "TEXT",
                "check_out": "TEXT",
                "room_type": "TEXT",
                "applicant_status": "TEXT",
                "status": "TEXT DEFAULT 'pending'",
                "created_at": "TEXT",
            },
        )
        await _ensure_columns(
            db,
            "issues",
            {
                "photo_file_id": "TEXT",
                "updated_at": "TEXT",
            },
        )

        await db.executemany(
            """
            INSERT OR IGNORE INTO dormitories(
                id, name, address, price, total_places, free_places, photo_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_DORMITORIES,
        )
        await db.execute(
            """
            UPDATE reservations
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )
        await db.commit()


async def _ensure_columns(db, table_name: str, columns: dict[str, str]):
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {column[1] for column in await cursor.fetchall()}

    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            await db.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )


async def add_user(telegram_id, name=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users(telegram_id, name, status)
            VALUES (?, ?, 'new')
            """,
            (telegram_id, name),
        )
        await db.commit()


async def update_user_registration(
    telegram_id, name, surname, phone, email, wsg_status
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET name = ?,
                surname = ?,
                phone = ?,
                email = ?,
                wsg_status = ?,
                status = 'registered'
            WHERE telegram_id = ?
            """,
            (name, surname, phone, email, wsg_status, telegram_id),
        )
        await db.commit()


async def update_user(telegram_id, name, surname, phone, email, wsg_status):
    await update_user_registration(
        telegram_id, name, surname, phone, email, wsg_status
    )


async def set_user_status(telegram_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET status = ?
            WHERE telegram_id = ?
            """,
            (status, telegram_id),
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
            (telegram_id,),
        )
        return await cursor.fetchone()


async def get_user_by_id(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        return await cursor.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            ORDER BY id
            """
        )
        return await cursor.fetchall()


async def get_registered_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE status = 'registered'
            ORDER BY surname, name
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
            (1 if is_blocked else 0, telegram_id),
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
            (telegram_id,),
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
            (1 if is_admin else 0, telegram_id),
        )
        await db.commit()


async def update_user_profile_field(telegram_id, field, value):
    allowed_fields = {"name", "surname", "phone", "email", "wsg_status"}
    if field not in allowed_fields:
        raise ValueError("Unsupported profile field")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"""
            UPDATE users
            SET {field} = ?
            WHERE telegram_id = ?
            """,
            (value, telegram_id),
        )
        await db.commit()


async def get_dormitories():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM dormitories
            ORDER BY id
            """
        )
        return await cursor.fetchall()


async def get_dormitory_by_id(dormitory_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM dormitories
            WHERE id = ?
            """,
            (dormitory_id,),
        )
        return await cursor.fetchone()


async def update_dormitory_field(dormitory_id, field, value):
    allowed_fields = {
        "name",
        "address",
        "price",
        "total_places",
        "free_places",
        "photo_url",
    }
    if field not in allowed_fields:
        raise ValueError("Unsupported dormitory field")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"""
            UPDATE dormitories
            SET {field} = ?
            WHERE id = ?
            """,
            (value, dormitory_id),
        )
        await db.commit()


async def get_room_by_id(room_id):
    return await get_dormitory_by_id(room_id)


async def get_rooms_by_dormitory(dormitory_name):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM dormitories
            WHERE name = ?
            """,
            (dormitory_name,),
        )
        return await cursor.fetchall()


async def get_room_by_number(room_number):
    try:
        return await get_dormitory_by_id(int(room_number))
    except (TypeError, ValueError):
        return None


async def add_reservation(
    user_id, dormitory_id, check_in=None, check_out=None, room_type=None,
    applicant_status=None, status=None
):
    dormitory = await get_dormitory_by_id(dormitory_id)
    initial_status = status
    if initial_status is None:
        initial_status = (
            RESERVATION_WAITING
            if dormitory and dormitory["free_places"] <= 0
            else RESERVATION_PENDING
        )

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO reservations(
                user_id,
                dormitory_id,
                check_in,
                check_out,
                room_type,
                applicant_status,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                dormitory_id,
                check_in,
                check_out,
                room_type,
                applicant_status,
                initial_status,
            ),
        )
        await db.commit()
        return cursor.lastrowid, initial_status


async def get_reservations_by_user_id(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.*, d.name AS dormitory_name, d.price
            FROM reservations AS r
            LEFT JOIN dormitories AS d ON d.id = r.dormitory_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC, r.id DESC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_all_reservations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                r.*,
                u.telegram_id,
                u.name,
                u.surname,
                u.phone,
                u.email,
                u.wsg_status,
                d.name AS dormitory_name,
                d.price,
                d.free_places
            FROM reservations AS r
            LEFT JOIN users AS u ON u.id = r.user_id
            LEFT JOIN dormitories AS d ON d.id = r.dormitory_id
            ORDER BY r.created_at DESC, r.id DESC
            """
        )
        return await cursor.fetchall()


async def get_pending_reservations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                r.*,
                u.telegram_id,
                u.name,
                u.surname,
                u.phone,
                u.email,
                u.wsg_status,
                d.name AS dormitory_name,
                d.price,
                d.free_places
            FROM reservations AS r
            LEFT JOIN users AS u ON u.id = r.user_id
            LEFT JOIN dormitories AS d ON d.id = r.dormitory_id
            WHERE r.status = ?
            ORDER BY
                CASE
                    WHEN COALESCE(r.applicant_status, u.wsg_status) = ? THEN 0
                    ELSE 1
                END,
                r.created_at ASC,
                r.id ASC
            """,
            (RESERVATION_PENDING, STUDENT_WSG),
        )
        return await cursor.fetchall()


async def get_waiting_reservations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                r.*,
                u.telegram_id,
                u.name,
                u.surname,
                u.wsg_status,
                d.name AS dormitory_name,
                d.price
            FROM reservations AS r
            LEFT JOIN users AS u ON u.id = r.user_id
            LEFT JOIN dormitories AS d ON d.id = r.dormitory_id
            WHERE r.status = ?
            ORDER BY
                CASE
                    WHEN COALESCE(r.applicant_status, u.wsg_status) = ? THEN 0
                    ELSE 1
                END,
                r.created_at ASC,
                r.id ASC
            """,
            (RESERVATION_WAITING, STUDENT_WSG),
        )
        return await cursor.fetchall()


async def get_reservation_by_id(reservation_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                r.*,
                u.telegram_id,
                u.name,
                u.surname,
                u.phone,
                u.email,
                u.wsg_status,
                d.name AS dormitory_name,
                d.price,
                d.free_places
            FROM reservations AS r
            LEFT JOIN users AS u ON u.id = r.user_id
            LEFT JOIN dormitories AS d ON d.id = r.dormitory_id
            WHERE r.id = ?
            """,
            (reservation_id,),
        )
        return await cursor.fetchone()


async def update_reservation_status(reservation_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (status, reservation_id),
        )
        await db.commit()


async def approve_reservation(reservation_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.*, d.free_places
            FROM reservations AS r
            JOIN dormitories AS d ON d.id = r.dormitory_id
            WHERE r.id = ?
            """,
            (reservation_id,),
        )
        reservation = await cursor.fetchone()
        if not reservation:
            return "not_found"

        if reservation["status"] != RESERVATION_PENDING:
            return "not_pending"

        if reservation["free_places"] <= 0:
            await db.execute(
                """
                UPDATE reservations
                SET status = ?
                WHERE id = ?
                """,
                (RESERVATION_WAITING, reservation_id),
            )
            await db.commit()
            return "waitlisted"

        await db.execute(
            """
            UPDATE dormitories
            SET free_places = free_places - 1
            WHERE id = ? AND free_places > 0
            """,
            (reservation["dormitory_id"],),
        )
        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (RESERVATION_APPROVED, reservation_id),
        )
        await db.commit()
        return "approved"


async def reject_reservation(reservation_id):
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        return None

    async with aiosqlite.connect(DB_NAME) as db:
        if reservation["status"] == RESERVATION_APPROVED:
            await db.execute(
                """
                UPDATE dormitories
                SET free_places = free_places + 1
                WHERE id = ?
                """,
                (reservation["dormitory_id"],),
            )

        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (RESERVATION_REJECTED, reservation_id),
        )
        await db.commit()

    promoted = None
    if reservation["status"] == RESERVATION_APPROVED:
        promoted = await promote_next_waiting_reservation(reservation["dormitory_id"])

    return promoted


async def cancel_reservation(reservation_id):
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        return None

    async with aiosqlite.connect(DB_NAME) as db:
        if reservation["status"] == RESERVATION_APPROVED:
            await db.execute(
                """
                UPDATE dormitories
                SET free_places = free_places + 1
                WHERE id = ?
                """,
                (reservation["dormitory_id"],),
            )

        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (RESERVATION_CANCELLED, reservation_id),
        )
        await db.commit()

    promoted = None
    if reservation["status"] == RESERVATION_APPROVED:
        promoted = await promote_next_waiting_reservation(reservation["dormitory_id"])

    return promoted


async def promote_next_waiting_reservation(dormitory_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.id
            FROM reservations AS r
            JOIN users AS u ON u.id = r.user_id
            WHERE r.dormitory_id = ? AND r.status = ?
            ORDER BY
                CASE
                    WHEN COALESCE(r.applicant_status, u.wsg_status) = ? THEN 0
                    ELSE 1
                END,
                r.created_at ASC,
                r.id ASC
            LIMIT 1
            """,
            (dormitory_id, RESERVATION_WAITING, STUDENT_WSG),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        await db.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (RESERVATION_PENDING, row["id"]),
        )
        await db.commit()

    return await get_reservation_by_id(row["id"])


async def add_issue(user_id, dormitory_id, category, description, photo_file_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO issues(
                user_id,
                dormitory_id,
                category,
                description,
                photo_file_id,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                dormitory_id,
                category,
                description,
                photo_file_id,
                ISSUE_NEW,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_issues_by_user_id(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT i.*, d.name AS dormitory_name
            FROM issues AS i
            LEFT JOIN dormitories AS d ON d.id = i.dormitory_id
            WHERE i.user_id = ?
            ORDER BY i.created_at DESC, i.id DESC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_issue_by_id(issue_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                i.*,
                u.telegram_id,
                u.name,
                u.surname,
                u.phone,
                u.email,
                d.name AS dormitory_name
            FROM issues AS i
            LEFT JOIN users AS u ON u.id = i.user_id
            LEFT JOIN dormitories AS d ON d.id = i.dormitory_id
            WHERE i.id = ?
            """,
            (issue_id,),
        )
        return await cursor.fetchone()


async def get_issues(statuses=None):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        params = []
        where = ""
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            where = f"WHERE i.status IN ({placeholders})"
            params.extend(statuses)

        cursor = await db.execute(
            f"""
            SELECT
                i.*,
                u.telegram_id,
                u.name,
                u.surname,
                d.name AS dormitory_name
            FROM issues AS i
            LEFT JOIN users AS u ON u.id = i.user_id
            LEFT JOIN dormitories AS d ON d.id = i.dormitory_id
            {where}
            ORDER BY i.created_at DESC, i.id DESC
            """,
            params,
        )
        return await cursor.fetchall()


async def update_issue_status(issue_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE issues
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, issue_id),
        )
        await db.commit()


async def get_statistics():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM reservations WHERE status = ?",
            (RESERVATION_APPROVED,),
        )
        residents_count = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COALESCE(SUM(free_places), 0) FROM dormitories")
        free_places = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM issues")
        issues_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM issues WHERE status IN (?, ?)",
            (ISSUE_NEW, ISSUE_IN_PROGRESS),
        )
        active_issues_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM reservations WHERE status = ?",
            (RESERVATION_PENDING,),
        )
        pending_reservations_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM reservations WHERE status = ?",
            (RESERVATION_WAITING,),
        )
        waiting_reservations_count = (await cursor.fetchone())[0]

        return {
            "residents_count": residents_count,
            "free_places": free_places,
            "issues_count": issues_count,
            "active_issues_count": active_issues_count,
            "pending_reservations_count": pending_reservations_count,
            "waiting_reservations_count": waiting_reservations_count,
        }


async def set_room_available(room_id):
    dormitory = await get_dormitory_by_id(room_id)
    if not dormitory:
        return

    await update_dormitory_field(
        room_id,
        "free_places",
        min(dormitory["total_places"], dormitory["free_places"] + 1),
    )


async def set_room_reserved(room_id):
    dormitory = await get_dormitory_by_id(room_id)
    if not dormitory:
        return

    await update_dormitory_field(
        room_id,
        "free_places",
        max(0, dormitory["free_places"] - 1),
    )
