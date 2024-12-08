import aiosqlite
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, bot_number):
        # Set the database path based on the bot number
        self.db_path = os.path.join('GoslingDKPbot', '3330', 'data', 'DKP3330.db')        
        self.conn = None

    async def setup(self):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        await self.connect()
        await self.create_tables()

    async def connect(self):
        if self.conn is None:
            try:
                self.conn = await aiosqlite.connect(self.db_path)
                logger.info(f"Connected to database {self.db_path}")
            except Exception as e:
                logger.error(f"Error connecting to database: {e}")

    async def is_connected(self):
        if self.conn:
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute('SELECT 1')
                    return True
            except Exception as e:
                logger.error(f"Database connection check failed: {e}")
                return False
        return False

    async def create_tables(self):
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_time TIMESTAMP NOT NULL,
                notify_time TIMESTAMP NOT NULL,
                channel_id INTEGER NOT NULL
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_user_id INTEGER PRIMARY KEY,
                main_id INTEGER,
                alt1_id INTEGER,
                alt2_id INTEGER,
                alt3_id INTEGER,
                farm1_id INTEGER,
                farm2_id INTEGER,
                farm3_id INTEGER,
                farm4_id INTEGER,
                farm5_id INTEGER
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS DKP (
                "Name" TEXT DEFAULT NULL,
                "ID" INTEGER PRIMARY KEY,
                "Discord_profile" TEXT DEFAULT NULL,
                "Kvk_fight_group" INTEGER DEFAULT 0,
                "Power_before_matchmaking" INTEGER DEFAULT 0,
                "Goal_KP" INTEGER DEFAULT 0,
                "Goal_Deads" INTEGER DEFAULT 0,
                "Goal_DKP" INTEGER DEFAULT 0,
                "KP_before_z5" INTEGER DEFAULT 0,
                "Deads_before_z5" INTEGER DEFAULT 0,
                "KP_after_z5" INTEGER DEFAULT 0,
                "Deads_after_z5" INTEGER DEFAULT 0,
                "KP_gained_z5" INTEGER DEFAULT 0,
                "Deads_gained_z5" INTEGER DEFAULT 0,
                "Altars_gained_KP" INTEGER DEFAULT 0,
                "KP_before_7_pass" INTEGER DEFAULT 0,
                "Deads_before_7_pass" INTEGER DEFAULT 0,
                "KP_after_7_pass" INTEGER DEFAULT 0,
                "Deads_after_7_pass" INTEGER DEFAULT 0,
                "KP_gained_7_pass" INTEGER DEFAULT 0,
                "Deads_gained_7_pass" INTEGER DEFAULT 0,
                "KP_before_Kingsland" INTEGER DEFAULT 0,
                "Deads_before_Kingsland" INTEGER DEFAULT 0,
                "KP_after_Kingsland" INTEGER DEFAULT 0,
                "Deads_after_Kingsland" INTEGER DEFAULT 0,
                "KP_gained_Kingsland" INTEGER DEFAULT 0,
                "Deads_gained_Kingsland" INTEGER DEFAULT 0,
                "Changed_DKP" INTEGER DEFAULT 0,
                "Reason" TEXT DEFAULT NULL,
                "Goal" TEXT DEFAULT NULL
            )
        ''')
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            logger.info(f"Connection to database {self.db_path} closed")
