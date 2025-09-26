import os
import json
import discord
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "config.json"

# Load or create config
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

HERO_TCG_ID = 1357752818068357330  # Hero TCG bot

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# ---- Slash Commands ----
@client.tree.command(name="setchannel", description="Set the spawn announcement channel")
@app_commands.describe(channel="The channel to send spawn messages")
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cfg = load_config()
    cfg[str(interaction.guild.id)] = cfg.get(str(interaction.guild.id), {})
    cfg[str(interaction.guild.id)]["channel"] = channel.id
    save_config(cfg)
    await interaction.response.send_message(f"Spawn channel set to {channel.mention}", ephemeral=True)

@client.tree.command(name="setrole_nomu", description="Set the role for Nomu spawns")
@app_commands.describe(role="Role to ping for Nomu")
async def setrole_nomu(interaction: discord.Interaction, role: discord.Role):
    cfg = load_config()
    cfg[str(interaction.guild.id)] = cfg.get(str(interaction.guild.id), {})
    cfg[str(interaction.guild.id)]["role_nomu"] = role.id
    save_config(cfg)
    await interaction.response.send_message(f"Nomu role set to {role.mention}", ephemeral=True)

@client.tree.command(name="setrole_shop", description="Set the role for Shop spawns")
@app_commands.describe(role="Role to ping for Shop")
async def setrole_shop(interaction: discord.Interaction, role: discord.Role):
    cfg = load_config()
    cfg[str(interaction.guild.id)] = cfg.get(str(interaction.guild.id), {})
    cfg[str(interaction.guild.id)]["role_shop"] = role.id
    save_config(cfg)
    await interaction.response.send_message(f"Shop role set to {role.mention}", ephemeral=True)

# ---- Event Listener ----
@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return
    if message.author.id != HERO_TCG_ID:
        return

    cfg = load_config()
    guild_cfg = cfg.get(str(message.guild.id), {})
    channel_id = guild_cfg.get("channel")
    if not channel_id:
        return

    channel = message.guild.get_channel(channel_id)
    if not channel:
        return

    # Nomu spawn detection
    if "nomu" in message.content.lower():
        role_id = guild_cfg.get("role_nomu")
        rarity = None
        for r in ["common", "rare", "epic", "super", "legendary"]:
            if r in message.content.lower():
                rarity = r.capitalize()
                break
        if rarity and role_id:
            role = message.guild.get_role(role_id)
            embed = discord.Embed(
                title=f"{rarity} Nomu Spawned!",
                description=f"{role.mention}, prepare for battle!",
                color=discord.Color.red()
            )
            await channel.send(content=f"{role.mention}", embed=embed)

    # Shop spawn detection (check embeds)
    if message.embeds:
        for e in message.embeds:
            if "welcome" in (e.title or "").lower() or "welcome" in (e.description or "").lower():
                role_id = guild_cfg.get("role_shop")
                if role_id:
                    role = message.guild.get_role(role_id)
                    embed = discord.Embed(
                        title="Shop Spawned!",
                        description=f"{role.mention}, check the shop now!",
                        color=discord.Color.green()
                    )
                    await channel.send(content=f"{role.mention}", embed=embed)

# ---- Run Bot ----
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("Error: DISCORD_TOKEN not found in environment variables")
else:
    client.run(TOKEN)