from datetime import datetime
from uuid import uuid4

import aiosqlite

from data import SCHEDULE_GROUPS


CREATE_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    client_name TEXT NOT NULL,
    service TEXT NOT NULL,
    desired_date TEXT NOT NULL,
    desired_time TEXT NOT NULL,
    contact TEXT NOT NULL,
    schedule_group TEXT,
    slot_id INTEGER,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL
);
"""

CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
"""

CREATE_SLOTS_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    slot_date TEXT NOT NULL,
    slot_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'free',
    application_id INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE(group_id, slot_date, slot_time)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(CREATE_APPLICATIONS_TABLE)
            await db.execute(CREATE_GROUPS_TABLE)
            await db.execute(CREATE_SLOTS_TABLE)
            await self._ensure_application_columns(db)
            await self._seed_schedule_groups(db)
            await db.commit()

    async def _ensure_application_columns(self, db: aiosqlite.Connection) -> None:
        columns = await self._table_columns(db, "applications")
        if "schedule_group" not in columns:
            await db.execute("ALTER TABLE applications ADD COLUMN schedule_group TEXT")
        if "slot_id" not in columns:
            await db.execute("ALTER TABLE applications ADD COLUMN slot_id INTEGER")

    async def _table_columns(self, db: aiosqlite.Connection, table_name: str) -> set[str]:
        cursor = await db.execute(f"PRAGMA table_info({table_name})")
        rows = await cursor.fetchall()
        return {row[1] for row in rows}

    async def _seed_schedule_groups(self, db: aiosqlite.Connection) -> None:
        for group in SCHEDULE_GROUPS:
            await db.execute(
                """
                INSERT INTO schedule_groups (id, name)
                VALUES (?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (group["id"], group["name"]),
            )

    async def get_schedule_groups(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM schedule_groups ORDER BY name")
            return [dict(row) for row in await cursor.fetchall()]

    async def get_schedule_group(self, group_id: str) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM schedule_groups WHERE id = ?", (group_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_schedule_group(self, name: str) -> dict:
        group_id = f"group_{uuid4().hex[:10]}"
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO schedule_groups (id, name) VALUES (?, ?)",
                (group_id, name),
            )
            await db.commit()
        return {"id": group_id, "name": name}

    async def update_schedule_group(self, group_id: str, name: str) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "UPDATE schedule_groups SET name = ? WHERE id = ?",
                (name, group_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_schedule_group(self, group_id: str) -> tuple[bool, str]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM schedule_slots
                WHERE group_id = ? AND status != 'free'
                """,
                (group_id,),
            )
            locked_count = (await cursor.fetchone())[0]
            if locked_count:
                return False, "У цього графіка є заявки. Спочатку завершіть або скасуйте їх."

            await db.execute("DELETE FROM schedule_slots WHERE group_id = ? AND status = 'free'", (group_id,))
            cursor = await db.execute("DELETE FROM schedule_groups WHERE id = ?", (group_id,))
            await db.commit()
            if cursor.rowcount <= 0:
                return False, "Графік не знайдено."
            return True, ""

    async def add_slots(self, group_id: str, slot_date: str, times: list[str]) -> int:
        created = 0
        async with aiosqlite.connect(self.path) as db:
            for slot_time in times:
                cursor = await db.execute(
                    """
                    INSERT OR IGNORE INTO schedule_slots (
                        group_id, slot_date, slot_time, created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        group_id,
                        slot_date,
                        slot_time,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
                created += cursor.rowcount
            await db.commit()
        return created

    async def add_slots_bulk(self, group_id: str, slots_by_date: dict[str, list[str]]) -> int:
        created = 0
        created_at = datetime.now().isoformat(timespec="seconds")
        async with aiosqlite.connect(self.path) as db:
            await db.execute("BEGIN")
            for slot_date, times in slots_by_date.items():
                for slot_time in times:
                    cursor = await db.execute(
                        """
                        INSERT OR IGNORE INTO schedule_slots (
                            group_id, slot_date, slot_time, created_at
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (group_id, slot_date, slot_time, created_at),
                    )
                    created += cursor.rowcount
            await db.commit()
        return created

    async def get_available_dates(self, group_id: str) -> list[str]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT DISTINCT slot_date
                FROM schedule_slots
                WHERE group_id = ? AND status = 'free'
                ORDER BY slot_date
                """,
                (group_id,),
            )
            return [row[0] for row in await cursor.fetchall()]

    async def get_available_slots(self, group_id: str, slot_date: str) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT *
                FROM schedule_slots
                WHERE group_id = ? AND slot_date = ? AND status = 'free'
                ORDER BY slot_time
                """,
                (group_id, slot_date),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_slot(self, slot_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT s.*, g.name AS group_name
                FROM schedule_slots s
                LEFT JOIN schedule_groups g ON g.id = s.group_id
                WHERE s.id = ?
                """,
                (slot_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_upcoming_slots(self, limit: int = 20) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT s.*, g.name AS group_name
                FROM schedule_slots s
                LEFT JOIN schedule_groups g ON g.id = s.group_id
                WHERE s.slot_date >= ?
                ORDER BY s.slot_date, s.slot_time
                LIMIT ?
                """,
                (datetime.now().date().isoformat(), limit),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def delete_slot(self, slot_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "DELETE FROM schedule_slots WHERE id = ? AND status = 'free'",
                (slot_id,),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def update_slot_time(self, slot_id: int, new_time: str) -> bool:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM schedule_slots WHERE id = ?", (slot_id,))
            slot = await cursor.fetchone()
            if not slot or slot["status"] != "free":
                return False

            cursor = await db.execute(
                """
                UPDATE OR IGNORE schedule_slots
                SET slot_time = ?
                WHERE id = ? AND status = 'free'
                """,
                (new_time, slot_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def create_application_for_slot(
        self,
        user_id: int,
        username: str | None,
        client_name: str,
        service: str,
        contact: str,
        slot_id: int,
    ) -> int | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")

            cursor = await db.execute(
                """
                SELECT s.*, g.name AS group_name
                FROM schedule_slots s
                LEFT JOIN schedule_groups g ON g.id = s.group_id
                WHERE s.id = ? AND s.status = 'free'
                """,
                (slot_id,),
            )
            slot = await cursor.fetchone()
            if not slot:
                await db.rollback()
                return None

            cursor = await db.execute(
                """
                INSERT INTO applications (
                    user_id, username, client_name, service,
                    desired_date, desired_time, contact, schedule_group,
                    slot_id, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (
                    user_id,
                    username,
                    client_name,
                    service,
                    slot["slot_date"],
                    slot["slot_time"],
                    contact,
                    slot["group_name"],
                    slot_id,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            application_id = int(cursor.lastrowid)
            await db.execute(
                """
                UPDATE schedule_slots
                SET status = 'blocked', application_id = ?
                WHERE id = ?
                """,
                (application_id, slot_id),
            )
            await db.commit()
            return application_id

    async def get_application(self, application_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_recent_applications(self, limit: int = 10) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT *
                FROM applications
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def update_status(self, application_id: int, status: str) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,),
            )
            application = await cursor.fetchone()
            if not application:
                return None

            await db.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (status, application_id),
            )

            slot_id = application["slot_id"]
            if slot_id and status == "confirmed":
                await db.execute(
                    "UPDATE schedule_slots SET status = 'booked' WHERE id = ?",
                    (slot_id,),
                )
            elif slot_id and status == "cancelled":
                await db.execute(
                    """
                    UPDATE schedule_slots
                    SET status = 'free', application_id = NULL
                    WHERE id = ?
                    """,
                    (slot_id,),
                )

            await db.commit()

        return await self.get_application(application_id)
