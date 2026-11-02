import random
import sqlite3
import discord

from config import (
    DATABASE_NAME, PET_CATALOG, get_evolution_title,
    get_mood_status, render_progress_bar
)
from database import (
    fetch_user_record, update_pet_customization, get_or_create_boss
)
from hackatime_client import fetch_today_coding_data
from pet_engine import apply_passive_hunger_decay, process_code_sync


def create_pet_embed(user_data: dict, discord_user: discord.abc.User) -> discord.Embed:
    """Builds the rich Discord Embed for a user's companion pet."""
    species_key = user_data.get("pet_species", "cat")
    pet_info = PET_CATALOG.get(species_key, PET_CATALOG["cat"])
    level = int(user_data.get("level", 1))
    xp = int(user_data.get("xp", 0))
    xp_needed = level * 100
    hunger = int(user_data.get("hunger", 100))
    total_hours = round(int(user_data.get("total_seconds_coded", 0)) / 3600, 2)

    evo_title = get_evolution_title(level)
    mood_text = get_mood_status(hunger)

    if hunger >= 50:
        embed_color = discord.Color.teal()
    elif hunger >= 25:
        embed_color = discord.Color.gold()
    else:
        embed_color = discord.Color.red()

    embed = discord.Embed(
        title=f"{pet_info['species_name']} - {user_data['pet_name']} - Lvl {level}",
        description=f"**Trainer:** {discord_user.mention}\n**Rank:** `{evo_title}`\n*{pet_info['description']}*",
        color=embed_color
    )
    embed.set_thumbnail(url=pet_info["sprite_url"])
    embed.add_field(
        name="Satiety (Hunger)",
        value=render_progress_bar(hunger, 100),
        inline=False
    )
    embed.add_field(
        name="Experience (XP)",
        value=render_progress_bar(xp, xp_needed),
        inline=False
    )
    embed.add_field(name="Current Mood", value=mood_text, inline=False)
    embed.add_field(name="Verified Code Time", value=f"`{total_hours} hrs`", inline=True)

    has_key = "Linked" if user_data.get("hackatime_key") else "Not Linked (/link_hackatime)"
    embed.add_field(name="Hackatime Status", value=f"`{has_key}`", inline=True)
    embed.set_footer(text="Code in VS Code & click 'Sync Hackatime Code' to feed your pet & fight the Server Boss!")
    return embed


class CompanionDropdown(discord.ui.Select):
    """Dropdown menu allowing players to select one of the 5 companion animals."""
    def __init__(self, owner_id: str):
        self.owner_id = str(owner_id)
        options = []
        for key, info in PET_CATALOG.items():
            options.append(
                discord.SelectOption(
                    label=info["species_name"],
                    value=key,
                    description=f"Base ATK: {info['base_atk']} | {info['description'][:50]}"
                )
            )
        super().__init__(
            placeholder="Select your coding companion species...",
            min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message(
                "Run `/choose_companion` to pick your own pet!", ephemeral=True
            )
            return
        selected_species = self.values[0]
        update_pet_customization(self.owner_id, species=selected_species)
        chosen_info = PET_CATALOG[selected_species]
        await interaction.response.send_message(
            f"You chose **{chosen_info['species_name']}** as your coding companion! "
            f"Run `/pet` to see your dashboard.",
            ephemeral=True
        )


class CompanionSelectView(discord.ui.View):
    def __init__(self, owner_id: str):
        super().__init__(timeout=120)
        self.add_item(CompanionDropdown(owner_id))


class PetDashboardView(discord.ui.View):
    """Interactive button bar attached to the /pet status card."""
    def __init__(self, owner_id: str, guild_id: str):
        super().__init__(timeout=None)
        self.owner_id = str(owner_id)
        self.guild_id = str(guild_id)

    @discord.ui.button(label="Sync Hackatime Code", style=discord.ButtonStyle.success)
    async def sync_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message(
                "This is not your pet card! Type `/pet` to open yours.", ephemeral=True
            )
            return
        await interaction.response.defer()
        user_record = fetch_user_record(
            self.owner_id, self.guild_id, interaction.user.display_name
        )
        if not user_record.get("hackatime_key"):
            await interaction.followup.send(
                "You haven't linked your Hackatime API key yet! Use `/link_hackatime` first.",
                ephemeral=True
            )
            return

        api_result = await fetch_today_coding_data(user_record["hackatime_key"])
        if not api_result["ok"]:
            await interaction.followup.send(
                f"Hackatime Sync Error: {api_result['error']}", ephemeral=True
            )
            return

        sync_outcome = process_code_sync(
            self.owner_id, self.guild_id,
            interaction.user.display_name, api_result["total_seconds"]
        )
        if not sync_outcome["synced"]:
            await interaction.followup.send(
                f"Today's total on Hackatime: `{api_result.get('human_readable', '0 mins')}`\n"
                f"{sync_outcome['reason']}",
                ephemeral=True
            )
            return

        refreshed_user = fetch_user_record(
            self.owner_id, self.guild_id, interaction.user.display_name
        )
        new_embed = create_pet_embed(refreshed_user, interaction.user)
        await interaction.edit_original_response(embed=new_embed, view=self)

        msg = (
            f"**Synced {sync_outcome['minutes_added']} new mins of code!**\n"
            f"**+{sync_outcome['xp_gained']} XP** | **+{sync_outcome['hunger_restored']}% Satiety**\n"
            f"**Dealt {sync_outcome['boss_damage']} DMG** to the Server Boss!"
        )
        if sync_outcome["levels_gained"] > 0:
            msg += f"\n**LEVEL UP!** Your pet reached **Level {sync_outcome['new_level']}**"
        if sync_outcome["boss_defeated"]:
            msg += (
                f"\n**SERVER BOSS DEFEATED!** A stronger boss "
                f"**{sync_outcome['boss_name']}** has spawned!"
            )
        await interaction.followup.send(msg)

    @discord.ui.button(label="Train Pet (-10 Hunger)", style=discord.ButtonStyle.primary)
    async def train_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message(
                "Only the pet's trainer can run drills!", ephemeral=True
            )
            return

        user = apply_passive_hunger_decay(
            self.owner_id, self.guild_id, interaction.user.display_name
        )
        if user["hunger"] < 15:
            await interaction.response.send_message(
                "Your pet is too hungry to train! Write some code in VS Code and click "
                "**Sync Hackatime Code** first.",
                ephemeral=True
            )
            return

        bonus_xp = random.randint(12, 25)
        new_hunger = user["hunger"] - 10
        new_xp = user["xp"] + bonus_xp
        new_level = user["level"]
        xp_needed = new_level * 100

        if new_xp >= xp_needed:
            new_xp = new_xp - xp_needed
            new_level = new_level + 1

        conn = sqlite3.connect(DATABASE_NAME)
        conn.execute(
            "UPDATE users SET hunger = ?, xp = ?, level = ? WHERE user_id = ?",
            (new_hunger, new_xp, new_level, self.owner_id)
        )
        conn.commit()
        conn.close()

        updated_user = fetch_user_record(
            self.owner_id, self.guild_id, interaction.user.display_name
        )
        await interaction.response.edit_message(
            embed=create_pet_embed(updated_user, interaction.user), view=self
        )
        await interaction.followup.send(
            f"**{updated_user['pet_name']}** completed a debugging obstacle course "
            f"and gained **{bonus_xp} XP**!",
            ephemeral=True
        )

    @discord.ui.button(label="Server Boss Status", style=discord.ButtonStyle.secondary)
    async def boss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        boss = get_or_create_boss(self.guild_id)
        hp_bar = render_progress_bar(boss["current_hp"], boss["max_hp"], 12)
        embed = discord.Embed(
            title=f"Raid Boss: {boss['boss_name']} (Stage {boss['boss_level']})",
            description=(
                "Every minute of coding synced by anyone in this server deals "
                "damage to the Raid Boss!\n\n"
                f"**Boss HP:**\n{hp_bar}"
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


