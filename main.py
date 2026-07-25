import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Konfiguration laden
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Bot-Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

# DJ-Liste laden/speichern
DJ_FILE = 'dj_list.json'

def load_dj_list():
    if os.path.exists(DJ_FILE):
        with open(DJ_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_dj_list(dj_list):
    with open(DJ_FILE, 'w', encoding='utf-8') as f:
        json.dump(dj_list, f, ensure_ascii=False, indent=2)

dj_list = load_dj_list()

# Musik-Warteschlange
music_queue = []
current_music = None
is_playing = False

@bot.event
async def on_ready():
    print(f'Bot angemeldet als {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="auf Befehle"))
    
    # Sende die Abmeldungs-Embeds beim Start
    await send_abmeldungs_embeds()

# ==================== Abmeldungs-Embeds ====================
async def send_abmeldungs_embeds():
    """Sendet die Abmeldungs-Embeds in die entsprechenden Channels"""
    
    # Discord-Team Abmeldung
    discord_channel = bot.get_channel(config['CHANNELS']['discordTeamAbmelden'])
    if discord_channel:
        try:
            # Lösche alte Nachrichten
            async for msg in discord_channel.history(limit=100):
                if msg.author == bot.user:
                    await msg.delete()
            
            embed = discord.Embed(
                title="🔔 Discord-Team Abmeldung",
                description="Klicke auf den Button um dich abzumelden!",
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.set_footer(text="Abmeldungssystem")
            
            view = AbmeldungsView(team_type="discord")
            await discord_channel.send(embed=embed, view=view)
            print("✅ Discord-Team Abmeldungs-Embed gesendet")
        except Exception as e:
            print(f"❌ Fehler beim Senden des Discord-Team Embeds: {e}")
    
    # Twitch-Team Abmeldung
    twitch_channel = bot.get_channel(config['CHANNELS']['twitchTeamAbmelden'])
    if twitch_channel:
        try:
            # Lösche alte Nachrichten
            async for msg in twitch_channel.history(limit=100):
                if msg.author == bot.user:
                    await msg.delete()
            
            embed = discord.Embed(
                title="🔔 Twitch-Team Abmeldung",
                description="Klicke auf den Button um dich abzumelden!",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            embed.set_footer(text="Abmeldungssystem")
            
            view = AbmeldungsView(team_type="twitch")
            await twitch_channel.send(embed=embed, view=view)
            print("✅ Twitch-Team Abmeldungs-Embed gesendet")
        except Exception as e:
            print(f"❌ Fehler beim Senden des Twitch-Team Embeds: {e}")

# ==================== Abmeldungs-Modal ====================
class AbmeldungsModal(discord.ui.Modal, title="Team Abmeldung"):
    von = discord.ui.TextInput(
        label="Von (z.B. 14:00)",
        placeholder="HH:MM",
        required=True,
        min_length=5,
        max_length=5
    )
    bis = discord.ui.TextInput(
        label="Bis (z.B. 18:00)",
        placeholder="HH:MM",
        required=True,
        min_length=5,
        max_length=5
    )
    grund = discord.ui.TextInput(
        label="Grund (optional)",
        placeholder="Dein Grund hier...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    team_type = None
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validierung der Zeiten
            try:
                von_h, von_m = map(int, self.von.value.split(':'))
                bis_h, bis_m = map(int, self.bis.value.split(':'))
                
                if not (0 <= von_h <= 23 and 0 <= von_m <= 59):
                    await interaction.response.send_message("❌ Ungültige Von-Zeit! Format: HH:MM", ephemeral=True)
                    return
                if not (0 <= bis_h <= 23 and 0 <= bis_m <= 59):
                    await interaction.response.send_message("❌ Ungültige Bis-Zeit! Format: HH:MM", ephemeral=True)
                    return
            except ValueError:
                await interaction.response.send_message("❌ Ungültiges Zeitformat! Verwende HH:MM", ephemeral=True)
                return
            
            # Bestätige die Abmeldung dem User
            await interaction.response.send_message("✅ Deine Abmeldung wurde registriert!", ephemeral=True)
            
            # Sende Log-Embed
            if self.team_type == "discord":
                info_role_id = config['ROLES']['discordInfoRole']
                log_channel_id = config['CHANNELS']['discordTeamAbmelden']
                team_name = "Discord-Team"
            else:
                info_role_id = config['ROLES']['twitchInfoRole']
                log_channel_id = config['CHANNELS']['twitchTeamAbmelden']
                team_name = "Twitch-Team"
            
            embed = discord.Embed(
                title=f"📋 {team_name} - Neue Abmeldung",
                description=f"**User:** {interaction.user.mention}\n**Von:** {self.von.value}\n**Bis:** {self.bis.value}",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            
            if self.grund.value:
                embed.add_field(name="Grund", value=self.grund.value, inline=False)
            
            embed.set_footer(text=f"User-ID: {interaction.user.id}")
            embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
            
            # Finde und sende an den Info-Channel
            info_channel = bot.get_channel(log_channel_id)
            if info_channel:
                # Mention der Role
                info_role = interaction.guild.get_role(info_role_id)
                if info_role:
                    await info_channel.send(f"{info_role.mention}", embed=embed)
                else:
                    await info_channel.send(embed=embed)
                print(f"✅ Abmeldung geloggt für {team_name}")
            
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten der Abmeldung: {e}")
            await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {e}", ephemeral=True)

# ==================== Abmeldungs-View (Button) ====================
class AbmeldungsView(discord.ui.View):
    def __init__(self, team_type="discord"):
        super().__init__(persistent=True)
        self.team_type = team_type
    
    @discord.ui.button(label="Abmelden", style=discord.ButtonStyle.danger, emoji="🔔", custom_id="abmeldungs_button")
    async def abmelden_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Erstelle Modal
        modal = AbmeldungsModal()
        modal.team_type = self.team_type
        await interaction.response.send_modal(modal)

# ==================== MangoGPT ====================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.channel.id == config['CHANNELS']['mangoGPT']:
        async with message.channel.typing():
            # Hier würde die AI-Integration stattfinden (z.B. mit OpenAI API)
            response = f"🤖 MangoGPT antwortet auf: {message.content[:50]}..."
            await message.reply(response, mention_author=False)
    
    await bot.process_commands(message)

# ==================== DJ-Befehle ====================
@bot.tree.command(name="dj-add", description="Fügt einen User zur DJ-Liste hinzu")
async def dj_add(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != config['OWNER_ID']:
        await interaction.response.send_message("❌ Nur der Bot-Besitzer kann DJs hinzufügen!", ephemeral=True)
        return
    
    if user.id not in dj_list:
        dj_list.append(user.id)
        save_dj_list(dj_list)
        await interaction.response.send_message(f"✅ {user.mention} wurde zur DJ-Liste hinzugefügt!")
        
        # Log
        embed = discord.Embed(title="DJ hinzugefügt", description=f"{user.mention} wurde hinzugefügt", color=discord.Color.green())
        await log_mod(embed)
    else:
        await interaction.response.send_message(f"⚠️ {user.mention} ist bereits in der DJ-Liste!", ephemeral=True)

@bot.tree.command(name="dj-remove", description="Entfernt einen User aus der DJ-Liste")
async def dj_remove(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != config['OWNER_ID']:
        await interaction.response.send_message("❌ Nur der Bot-Besitzer kann DJs entfernen!", ephemeral=True)
        return
    
    if user.id in dj_list:
        dj_list.remove(user.id)
        save_dj_list(dj_list)
        await interaction.response.send_message(f"✅ {user.mention} wurde aus der DJ-Liste entfernt!")
        
        # Log
        embed = discord.Embed(title="DJ entfernt", description=f"{user.mention} wurde entfernt", color=discord.Color.red())
        await log_mod(embed)
    else:
        await interaction.response.send_message(f"⚠️ {user.mention} ist nicht in der DJ-Liste!", ephemeral=True)

def can_play_music(user_id, user_roles):
    if user_id == config['OWNER_ID']:
        return True
    if user_id in dj_list:
        return True
    for role_id in [config['ROLES']['djAccessRole1'], config['ROLES']['djAccessRole2']]:
        if discord.utils.get(user_roles, id=role_id):
            return True
    return False

# ==================== Musik-Befehle ====================
@bot.tree.command(name="musik-play", description="Spielt eine URL oder Radio Bollerwagen ab")
async def musik_play(interaction: discord.Interaction, url: str = None):
    if not can_play_music(interaction.user.id, interaction.user.roles):
        await interaction.response.send_message("❌ Du hast keine Berechtigung, Musik zu spielen!", ephemeral=True)
        return
    
    musik_channel = bot.get_channel(config['CHANNELS']['musik'])
    if not musik_channel:
        await interaction.response.send_message("❌ Musik-Channel nicht gefunden!", ephemeral=True)
        return
    
    url = url or config['MUSIC']['defaultStreamUrl']
    
    global current_music
    current_music = url
    
    embed = discord.Embed(
        title="🎵 Musik wird abgespielt",
        description=f"**URL:** {url[:100]}...",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)
    
    # Log
    embed_log = discord.Embed(
        title="Musik gestartet",
        description=f"{interaction.user.mention} hat Musik gestartet",
        color=discord.Color.blue()
    )
    await log_mod(embed_log)

@bot.tree.command(name="musik-stop", description="Stoppt die aktuelle Musik")
async def musik_stop(interaction: discord.Interaction):
    if not can_play_music(interaction.user.id, interaction.user.roles):
        await interaction.response.send_message("❌ Du hast keine Berechtigung!", ephemeral=True)
        return
    
    global current_music, is_playing
    current_music = None
    is_playing = False
    
    await interaction.response.send_message("⏹️ Musik gestoppt!")
    
    # Log
    embed = discord.Embed(
        title="Musik gestoppt",
        description=f"{interaction.user.mention} hat Musik gestoppt",
        color=discord.Color.orange()
    )
    await log_mod(embed)

# ==================== Logging-Funktionen ====================
async def log_messages(before, after):
    """Logged Nachrichten (gesendet, bearbeitet, gelöscht)"""
    embed = discord.Embed(
        title="📝 Nachricht bearbeitet",
        description=f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}",
        color=discord.Color.yellow(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Vorher", value=before.content[:1024] or "*(leer)*", inline=False)
    embed.add_field(name="Nachher", value=after.content[:1024] or "*(leer)*", inline=False)
    
    log_channel = bot.get_channel(config['CHANNELS']['messagesLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return
    
    embed = discord.Embed(
        title="🗑️ Nachricht gelöscht",
        description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Inhalt", value=message.content[:1024] or "*(leer)*", inline=False)
    
    log_channel = bot.get_channel(config['CHANNELS']['messagesLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author == bot.user:
        return
    
    if before.content == after.content:
        return
    
    await log_messages(before, after)

# ==================== Member-Logging ====================
@bot.event
async def on_user_update(before, after):
    embed = discord.Embed(
        title="👤 User aktualisiert",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    changes = []
    
    if before.name != after.name:
        changes.append(f"**Name:** {before.name} → {after.name}")
    if before.avatar != after.avatar:
        changes.append("**Profilbild:** Geändert")
    if before.banner != after.banner:
        changes.append("**Banner:** Geändert")
    
    if changes:
        embed.description = "\n".join(changes)
        embed.set_author(name=f"{after} ({after.id})", icon_url=after.avatar.url if after.avatar else None)
        
        log_channel = bot.get_channel(config['CHANNELS']['memberLog'])
        if log_channel:
            await log_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    embed = discord.Embed(
        title="👤 Member aktualisiert",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_author(name=f"{after} ({after.id})", icon_url=after.avatar.url if after.avatar else None)
    
    changes = []
    
    if before.nick != after.nick:
        changes.append(f"**Nickname:** {before.nick} → {after.nick}")
    if before.roles != after.roles:
        removed = [r for r in before.roles if r not in after.roles]
        added = [r for r in after.roles if r not in before.roles]
        if removed:
            changes.append(f"**Rollen entfernt:** {', '.join([r.mention for r in removed])}")
        if added:
            changes.append(f"**Rollen hinzugefügt:** {', '.join([r.mention for r in added])}")
    
    if changes:
        embed.description = "\n".join(changes)
        
        log_channel = bot.get_channel(config['CHANNELS']['memberLog'])
        if log_channel:
            await log_channel.send(embed=embed)

# ==================== Rollen-Logging ====================
@bot.event
async def on_guild_role_create(role):
    embed = discord.Embed(
        title="➕ Rolle erstellt",
        description=f"**Name:** {role.name}\n**ID:** {role.id}",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Farbe", value=str(role.color), inline=True)
    embed.add_field(name="Mentionierbar", value=str(role.mentionable), inline=True)
    
    log_channel = bot.get_channel(config['CHANNELS']['rolesLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    embed = discord.Embed(
        title="❌ Rolle gelöscht",
        description=f"**Name:** {role.name}\n**ID:** {role.id}",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    
    log_channel = bot.get_channel(config['CHANNELS']['rolesLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_update(before, after):
    embed = discord.Embed(
        title="✏️ Rolle bearbeitet",
        description=f"**Name:** {after.name}\n**ID:** {after.id}",
        color=discord.Color.yellow(),
        timestamp=datetime.now()
    )
    
    changes = []
    if before.name != after.name:
        changes.append(f"**Name:** {before.name} → {after.name}")
    if before.color != after.color:
        changes.append(f"**Farbe:** Geändert")
    if before.permissions != after.permissions:
        changes.append("**Berechtigungen:** Geändert")
    
    if changes:
        embed.add_field(name="Änderungen", value="\n".join(changes), inline=False)
    
    log_channel = bot.get_channel(config['CHANNELS']['rolesLog'])
    if log_channel:
        await log_channel.send(embed=embed)

# ==================== Server-Logging ====================
@bot.event
async def on_guild_channel_create(channel):
    embed = discord.Embed(
        title="➕ Channel erstellt",
        description=f"**Name:** {channel.name}\n**Typ:** {channel.type}",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    log_channel = bot.get_channel(config['CHANNELS']['serverLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    embed = discord.Embed(
        title="❌ Channel gelöscht",
        description=f"**Name:** {channel.name}\n**Typ:** {channel.type}",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    
    log_channel = bot.get_channel(config['CHANNELS']['serverLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_update(before, after):
    embed = discord.Embed(
        title="✏️ Channel bearbeitet",
        description=f"**Name:** {after.name}",
        color=discord.Color.yellow(),
        timestamp=datetime.now()
    )
    
    changes = []
    if before.name != after.name:
        changes.append(f"**Name:** {before.name} → {after.name}")
    if before.topic != after.topic:
        changes.append(f"**Thema:** Geändert")
    
    if changes:
        embed.add_field(name="Änderungen", value="\n".join(changes), inline=False)
    
    log_channel = bot.get_channel(config['CHANNELS']['serverLog'])
    if log_channel:
        await log_channel.send(embed=embed)

# ==================== Voice-Logging ====================
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = bot.get_channel(config['CHANNELS']['voiceLog'])
    if not log_channel:
        return
    
    embed = discord.Embed(timestamp=datetime.now())
    embed.set_author(name=f"{member} ({member.id})", icon_url=member.avatar.url if member.avatar else None)
    
    if before.channel is None and after.channel is not None:
        embed.title = "✅ Voice Channel betreten"
        embed.description = f"**Channel:** {after.channel.mention}"
        embed.color = discord.Color.green()
    elif before.channel is not None and after.channel is None:
        embed.title = "❌ Voice Channel verlassen"
        embed.description = f"**Channel:** {before.channel.mention}"
        embed.color = discord.Color.red()
    elif before.channel != after.channel:
        embed.title = "🔄 Voice Channel gewechselt"
        embed.description = f"**Von:** {before.channel.mention}\n**Zu:** {after.channel.mention}"
        embed.color = discord.Color.blue()
    else:
        return
    
    await log_channel.send(embed=embed)

# ==================== Mod-Logging ====================
async def log_mod(embed):
    log_channel = bot.get_channel(config['CHANNELS']['modLog'])
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    embed = discord.Embed(
        title="🚫 Member gebannt",
        description=f"**User:** {user.mention}\n**ID:** {user.id}",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    await log_mod(embed)

@bot.event
async def on_member_unban(guild, user):
    embed = discord.Embed(
        title="✅ Member entbannt",
        description=f"**User:** {user.mention}\n**ID:** {user.id}",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    await log_mod(embed)

# ==================== Bot starten ====================
TOKEN = os.getenv('DISCORD_TOKEN') or config.get('TOKEN')
if TOKEN == "DEIN_BOT_TOKEN_HIER":
    print("❌ Bitte TOKEN in der config.json oder als Umgebungsvariable setzen!")
    exit(1)

bot.run(TOKEN)
