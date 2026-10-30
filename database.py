from sqlite3 import connect
import sqlite3
import time 
from config import DATABASE_NAME

# Setup the SQLite tables so we actually save user data
def initialize_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Table 1: User profile
    # Stores all the pet stats, XP, hunger, and the Hackatime API key
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
               user_id TEXT PRIMARY KEY,
               guild_id TEXT NOT NULL,
               username TEXT DEFAULT 'Coder',
               hackatime_key TEXT DEFAULT NULL,
               pet_species TEXT DEFAULT 'cat',
               pet_name TEXT DEFAULT 'Pixel',
               level INTEGER DEFAULT 1,
               xp INTEGER DEFAULT 0,
               hunger INTEGER DEFAULT 100,
               total_seconds_coded INTEGER DEFAULT 0,
               last_synced_today_seconds INTEGER DEFAULT 0,
               last_sync_date TEXT DEFAULT '',
               last_updated_timestamp REAL DEFAULT 0
               )
     """)

    # Table 2: Server boss
    # Tracks the current raid boss HP and level for each server
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_boss (
            guild_id TEXT PRIMARY KEY,
            boss_name TEXT DEFAULT 'The Infinite Loop Leviathan',
            boss_level INTEGER DEFAULT 1,
            current_hp INTEGER DEFAULT 1000,
            max_hp INTEGER DEFAULT 1000
        )
    """)

    # Table 3: Sync logs
    # Keeps a history of when people sync so we can track minutes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            minutes_synced INTEGER NOT NULL,
            timestamp REAL NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Check if a user exists in the database. If not, create a default profile for them.
def fetch_user_record(user_id: str, guild_id: str, username: str = "Coder") -> dict:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # I fixed the missing ? placeholder here so it doesn't throw a syntax error
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    now = time.time()

    # If the user isn't in the db yet, insert a new row with default pet stats
    if row is None:
        cursor.execute("""
            INSERT INTO users (
                user_id, guild_id, username, pet_species, pet_name,
                level, xp, hunger, total_seconds_coded,
                last_synced_today_seconds, last_sync_date, last_updated_timestamp
            ) VALUES (?, ?, ?, 'cat', 'Byte', 1, 0, 100, 0, 0, '', ?)
        """, (str(user_id), str(guild_id), username, now))
        conn.commit()
        
        # Fetch the newly created record
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
        row = cursor.fetchone()

    result = dict(row)
    conn.close()
    return result


# Save the user's Hackatime API key to the database
def save_hackatime_key(user_id: str, guild_id: str, username: str, api_key: str):
    # Make sure the user exists before trying to update them
    fetch_user_record(user_id, guild_id, username)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET hackatime_key = ?, username = ?
        WHERE user_id = ?
    """, (api_key.strip(), username, str(user_id)))
    conn.commit()
    conn.close()


# Handle changing the pet species or giving it a new name
def update_pet_customization(user_id: str, species: str = None, new_name: str = None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # If both are provided, update both. Otherwise, update whichever one was passed in.
    if species is not None and new_name is not None:
        cursor.execute("UPDATE users SET pet_species = ?, pet_name = ? WHERE user_id = ?", (species, new_name, str(user_id)))
    elif species is not None:
        cursor.execute("UPDATE users SET pet_species = ? WHERE user_id = ?", (species, str(user_id)))
    elif new_name is not None:
        cursor.execute("UPDATE users SET pet_name = ? WHERE user_id = ?", (new_name, str(user_id)))

    conn.commit()
    conn.close()


# Get the server's boss. If the server doesn't have one yet, create a new boss.
def get_or_create_boss(guild_id: str) -> dict:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM server_boss WHERE guild_id = ?", (str(guild_id),))
    row = cursor.fetchone()

    if row is None:
        cursor.execute("""
            INSERT INTO server_boss (guild_id, boss_name, boss_level, current_hp, max_hp)
            VALUES (?, 'Syntax Error Hydra', 1, 600, 600)
        """, (str(guild_id),))
        conn.commit()
        cursor.execute("SELECT * FROM server_boss WHERE guild_id = ?", (str(guild_id),))
        row = cursor.fetchone()

    boss_data = dict(row)
    conn.close()
    return boss_data


# Fetch the top coders in a server ordered by how many seconds they coded
def fetch_guild_leaderboard(guild_id: str, limit: int = 10) -> list:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, pet_name, pet_species, level, total_seconds_coded
        FROM users
        WHERE guild_id = ?
        ORDER BY total_seconds_coded DESC
        LIMIT ?
    """, (str(guild_id), limit))

    rows = cursor.fetchall()
    leaderboard = []
    for r in rows:
        leaderboard.append(dict(r))

    conn.close()
    return leaderboard