from datetime import datetime

import aiosqlite


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
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(CREATE_APPLICATIONS_TABLE)
            await db.commit()

    async def create_application(
        self,
        user_id: int,
        username: str | None,
        client_name: str,
        service: str,
        desired_date: str,
        desired_time: str,
        contact: str,
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO applications (
                    user_id, username, client_name, service,
                    desired_date, desired_time, contact, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    client_name,
                    service,
                    desired_date,
                    desired_time,
                    contact,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def get_application(self, application_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_status(self, application_id: int, status: str) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (status, application_id),
            )
            await db.commit()

        return await self.get_application(application_id)
