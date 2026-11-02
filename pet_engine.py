# pet_engine.py
import sqlite3
import time
from datetime import datetime
from config import DATABASE_NAME, PET_CATALOG
from database import fetch_user_record, get_or_create_boss

BOSS_NAMES = [
    "Syntax Error Hydra",
    "NullPointer Golem",
    "Merge Conflict Dragon",
    "Segmentation Fault Kraken",
    "Infinite Loop Leviathan"
]


def apply_passive_hunger_decay(user_id: str, guild_id: str, username: str = "Coder") -> dict:
    user = fetch_user_record(user_id, guild_id, username)
    now = time.time()
    elapsed_seconds = now - float(user["last_updated_timestamp"])

    decay_points = int(elapsed_seconds // 1200)

    if decay_points > 0:
        new_hunger = user["hunger"] - decay_points
        if new_hunger < 0:
            new_hunger = 0

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET hunger = ?, last_updated_timestamp = ?
            WHERE user_id = ?
        """, (new_hunger, now, str(user_id)))
        conn.commit()
        conn.close()

        user["hunger"] = new_hunger
        user["last_updated_timestamp"] = now

    return user


def process_code_sync(user_id: str, guild_id: str, username: str, today_total_sec: int) -> dict:
    """
    Converts newly tracked Hackatime seconds into Pet XP, Hunger recovery,
    and Server Boss Raid damage.

    Returns a dict with:
        synced (bool), reason (str, only if not synced),
        minutes_added, xp_gained, xp_after (post level-up XP),
        hunger_restored, levels_gained, new_level,
        boss_damage, boss_defeated, boss_name, boss_hp, boss_max_hp
    """
    user = apply_passive_hunger_decay(user_id, guild_id, username)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Only reset the daily baseline when Hackatime itself clearly reset
    # (today_total < previously_synced_today). Otherwise keep the old
    # baseline and compute a normal delta.
    previously_synced_today = int(user["last_synced_today_seconds"])
    date_changed = user["last_sync_date"] != today_str

    if date_changed and today_total_sec < previously_synced_today:
        previously_synced_today = 0

    if today_total_sec > previously_synced_today:
        delta_sec = today_total_sec - previously_synced_today
    else:
        delta_sec = 0

    new_min = int(delta_sec // 60)

    if new_min < 1:
        return {
            "synced": False,
            "reason": "You need at least 1 new minute of coding in VS Code since your last sync!"
        }

    # Total pet stat gain
    xp_gained = new_min * 5
    hunger_restored = int(new_min * 1.5)
    if hunger_restored < 1:
        hunger_restored = 1

    update_hunger = user["hunger"] + hunger_restored
    if update_hunger > 100:
        update_hunger = 100

    current_level = int(user["level"])
    if current_level < 1:
        current_level = 1

    current_xp = int(user["xp"]) + xp_gained
    levels_gained = 0

    while True:
        xp_required = current_level * 100
        if current_xp >= xp_required:
            current_xp = current_xp - xp_required
            current_level = current_level + 1
            levels_gained = levels_gained + 1
        else:
            break

    newlife_sec = int(user["total_seconds_coded"]) + delta_sec
    now = time.time()

    species_key = user["pet_species"]
    pet_meta = PET_CATALOG.get(species_key, PET_CATALOG["cat"])
    atk_stat = pet_meta["base_atk"] + (current_level * 2)
    boss_damage = new_min * atk_stat

    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM server_boss WHERE guild_id = ?", (str(guild_id),))
    boss_row = cursor.fetchone()

    if boss_row is None:
        cursor.execute("""
            INSERT OR IGNORE INTO server_boss
                (guild_id, boss_name, boss_level, current_hp, max_hp)
            VALUES (?, 'Syntax Error Hydra', 1, 600, 600)
        """, (str(guild_id),))
        cursor.execute("SELECT * FROM server_boss WHERE guild_id = ?", (str(guild_id),))
        boss_row = cursor.fetchone()

    remaining_hp = int(boss_row["current_hp"]) - boss_damage
    boss_defeated = False
    new_boss_level = int(boss_row["boss_level"])
    new_boss_max_hp = int(boss_row["max_hp"])
    new_boss_name = boss_row["boss_name"]

    if remaining_hp <= 0:
        boss_defeated = True
        new_boss_level = new_boss_level + 1
        new_boss_max_hp = new_boss_level * 600
        remaining_hp = new_boss_max_hp
        name_index = (new_boss_level - 1) % len(BOSS_NAMES)
        new_boss_name = BOSS_NAMES[name_index]

    # Save everything atomically in SQLite
    cursor.execute("""
        UPDATE users
        SET username = ?,
            level = ?,
            xp = ?,
            hunger = ?,
            total_seconds_coded = ?,
            last_synced_today_seconds = ?,
            last_sync_date = ?,
            last_updated_timestamp = ?
        WHERE user_id = ?
    """, (
        username,
        current_level,
        current_xp,
        update_hunger,
        newlife_sec,
        today_total_sec,
        today_str,
        now,
        str(user_id)
    ))

    cursor.execute("""
        UPDATE server_boss
        SET boss_name = ?, boss_level = ?, current_hp = ?, max_hp = ?
        WHERE guild_id = ?
    """, (new_boss_name, new_boss_level, remaining_hp, new_boss_max_hp, str(guild_id)))

    cursor.execute("""
        INSERT INTO sync_logs (user_id, guild_id, minutes_synced, timestamp)
        VALUES (?, ?, ?, ?)
    """, (str(user_id), str(guild_id), new_min, now))

    conn.commit()
    conn.close()

    return {
        "synced": True,
        "minutes_added": new_min,
        "xp_gained": xp_gained,
        "xp_after": current_xp,
        "hunger_restored": hunger_restored,
        "levels_gained": levels_gained,
        "new_level": current_level,
        "boss_damage": boss_damage,
        "boss_defeated": boss_defeated,
        "boss_name": new_boss_name,
        "boss_hp": remaining_hp,
        "boss_max_hp": new_boss_max_hp,
    }