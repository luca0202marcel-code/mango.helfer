# MangoGPT Discord Bot 🥭

Ein vollständiger Discord-Bot mit MangoGPT KI, Musikplayer, Team-Management und umfassendem Logging-System.

## Features

### 🤖 MangoGPT
- Antwortet automatisch auf alle Nachrichten im MangoGPT-Channel
- Basis-Integration für KI-Antworten

### 🎵 Musik-System
- `/musik-play [URL]` - Spielt Musik oder Radio Bollerwagen ab
- `/musik-stop` - Stoppt die aktuelle Musik
- DJ-Berechtigung über:
  - Owner-Account
  - DJ-Liste (`/dj-add`, `/dj-remove`)
  - Rollen mit DJ-Berechtigung

### 👥 Team-Management
- Discord-Team: `/discord-team-abmelden`
- Twitch-Team: `/twitch-team-abmelden`
- Modal-Fenster mit Von/Bis Zeit und optionalem Grund

### 📊 Logging-System

| Kategorie | Channel |
|-----------|---------|
| **Messages** | Nachrichten gesendet, bearbeitet, gelöscht |
| **Members** | Profilbild, Name, Banner, Nicknames, Rollen-Änderungen |
| **Rollen** | Rollen erstellt, bearbeitet, gelöscht, vergeben, entzogen |
| **Server** | Channels erstellt, gelöscht, bearbeitet |
| **Voice** | Voice Channel beigetreten, verlassen, gewechselt |
| **Mod** | Bans, Unbans, DJ-Änderungen, Musik-Events |

## Installation

```bash
# Repository klonen
git clone https://github.com/luca0202marcel-code/mango.helfer.git
cd mango.helfer

# Abhängigkeiten installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env

# Token in .env eintragen
# DISCORD_TOKEN=dein_bot_token_hier
```

## Konfiguration

Bearbeite `config.json`:

```json
{
  "TOKEN": "DEIN_BOT_TOKEN_HIER",
  "CHANNELS": {
    "mangoGPT": 1530191358784962630,
    ...
  },
  "ROLES": {
    "discordTeamRole": 1529647541094715425,
    ...
  },
  "OWNER_ID": 1350491332413620426
}
```

## Verwendung

```bash
python main.py
```

## Befehle

### Musik
- `/musik-play [URL]` - Musik abspielen
- `/musik-stop` - Musik stoppen

### DJ-Management
- `/dj-add @User` - User zur DJ-Liste hinzufügen (nur Owner)
- `/dj-remove @User` - User entfernen (nur Owner)

### Team-Abmeldung
- `/discord-team-abmelden` - Abmeldung vom Discord-Team
- `/twitch-team-abmelden` - Abmeldung vom Twitch-Team

## Requirements

- Python 3.10+
- discord.py 2.3+
- python-dotenv
- yt-dlp

## Lizenz

MIT
