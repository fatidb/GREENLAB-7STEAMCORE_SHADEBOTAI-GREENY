# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import Intents, Embed
import os
import aiohttp
import json
import logging
import datetime
from collections import defaultdict
from langdetect import detect, lang_detect_exception
from trackers.cosmos_tracker import CosmosAirdropTracker
from dotenv import load_dotenv

# Configuration avancée du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\logs\\bot_{datetime.datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)

# Style terminal retro
TERMINAL_STYLE = {
    "color": 0x2C2C2C,
    "footer_icon": "https://i.imgur.com/3QZ7Jnk.png",
    "thumbnail": "https://i.imgur.com/5b4WwLp.gif"
}

# Chargement des variables d'environnement
load_dotenv('C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\.env')

# Configuration du bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Initialisation des trackers
airdrop_tracker = CosmosAirdropTracker()

# Mots-clés crypto et leurs réactions
CRYPTO_KEYWORDS = {
    "fam": ["🚀", "👊"],
    "degen": ["🎰", "💎"],
    "f": ["⚰️", "🫡"],
    "hell": ["🔥", "👿"],
    "wtf": ["😱", "❓"],
    "gm": ["☀️", "🌅"],
    "wagmi": ["💪", "✨"],
    "ngmi": ["💀", "🤡"],
    "lfg": ["🚀", "🔥"],
    "bullish": ["🐂", "📈"],
    "bearish": ["🐻", "📉"]
}

# Système de mémoire contextuelle amélioré
class PersistentMemory:
    def __init__(self):
        self.file_path = 'C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\memory.json'
        self.data = self._load_memory()
        
    def _load_memory(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {'users': {}, 'preferences': {}, 'history': {}}
        except (json.JSONDecodeError, Exception) as e:
            logging.error(f"Erreur de chargement mémoire : {str(e)}")
            return {'users': {}, 'preferences': {}, 'history': {}}
            
    def _save_memory(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Erreur de sauvegarde mémoire : {str(e)}")

    def add_memory(self, user_id: int, category: str, key: str, value: str):
        user_id = str(user_id)
        if category not in self.data:
            self.data[category] = {}
        if user_id not in self.data[category]:
            self.data[category][user_id] = {}
        self.data[category][user_id][key.lower()] = value
        self._save_memory()
        
    def get_memory(self, user_id: int, category: str, key: str = None):
        user_id = str(user_id)
        if category in self.data and user_id in self.data[category]:
            if key:
                return self.data[category][user_id].get(key.lower())
            return self.data[category][user_id]
        return None

    def remove_memory(self, user_id: int, category: str, key: str = None):
        user_id = str(user_id)
        if category in self.data and user_id in self.data[category]:
            if key:
                if key.lower() in self.data[category][user_id]:
                    del self.data[category][user_id][key.lower()]
                    self._save_memory()
                    return True
                return False
            else:
                del self.data[category][user_id]
                self._save_memory()
                return True
        return False

# Initialisation de la mémoire
memory = PersistentMemory()

# Initialisation de la mémoire de conversation
conversation_memory = PersistentMemory()

@bot.event
async def on_ready():
    print("\033[1;32mGREENY ONLINE VERT NEON\033[0m")
    logging.info(f"\n{'-'*40}")
    logging.info(f" T7STEAM - The Shader AI Bot ".center(40, ' '))
    logging.info(f" Version 7.3 | Greeny CORE ".center(40, ' '))
    logging.info(f"{'-'*40}")
    logging.info(f"Connecté en tant que {bot.user.name}")
    logging.info(f"ID: {bot.user.id}")
    logging.info(f"Serveurs: {len(bot.guilds)}")
    logging.info(f"{'-'*40}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Réactions aux mots-clés crypto
    for keyword, emojis in CRYPTO_KEYWORDS.items():
        if keyword in message.content.lower():
            for emoji in emojis:
                await message.add_reaction(emoji)

    # Commandes naturelles
    if message.content.lower().startswith('greeny'):
        content = message.content[6:].strip().lower()
        
        if 'you there' in content:
            await message.channel.send("Yes, I'm here! Version 7.3 is online.")
            return

    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('pong!')

@bot.command(name='remember')
async def remember(ctx, *, entry: str):
    """Enregistre une information utilisateur"""
    try:
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            parts = entry.split(' ', 2)
            key_part = parts[2] if len(parts) > 2 else ''
        else:
            target = ctx.author
            parts = entry.split(' ', 1)
            key_part = parts[1] if len(parts) > 1 else ''

        if ' is ' not in key_part:
            raise ValueError("Format invalide")
            
        key, value = key_part.split(' is ', 1)
        memory.add_memory(target.id, 'preferences', key.strip(), value.strip())
        
        embed = Embed(
            title="🧠 Mémoire mise à jour",
            description=f"```diff\n+ {target.display_name} : {key.strip()} → {value.strip()}\n```",
            color=TERMINAL_STYLE["color"]
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        logging.error(f"Erreur mémoire : {str(e)}")
        embed = Embed(
            title="❌ Erreur de format",
            description="Utilisez : `!remember [@user] [clé] is [valeur]`\nExemple : `!remember @user fav_color is vert`",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='forget')
async def forget(ctx, *, entry: str):
    """Oublie une information utilisateur"""
    try:
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            parts = entry.split(' ', 2)
            key_part = parts[2] if len(parts) > 2 else ''
        else:
            target = ctx.author
            parts = entry.split(' ', 1)
            key_part = parts[1] if len(parts) > 1 else ''

        if not key_part:
            raise ValueError("Format invalide")
            
        success = memory.remove_memory(target.id, 'preferences', key_part.strip())
        
        if success:
            embed = Embed(
                title="🧠 Mémoire effacée",
                description=f"```diff\n- {target.display_name} : {key_part.strip()}\n```",
                color=TERMINAL_STYLE["color"]
            )
        else:
            embed = Embed(
                title="❌ Erreur",
                description=f"Aucune information trouvée pour {key_part.strip()}",
                color=0xff0000
            )
        await ctx.send(embed=embed)
        
    except Exception as e:
        logging.error(f"Erreur mémoire : {str(e)}")
        embed = Embed(
            title="❌ Erreur de format",
            description="Utilisez : `!forget [@user] [clé]`\nExemple : `!forget @user fav_color`",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="🤖 Aide SHADEBOT",
        description="Voici les commandes disponibles:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!ping",
        value="Vérifie si le bot est en ligne",
        inline=False
    )
    embed.add_field(
        name="!ask [question]",
        value="Pose une question à l'IA\nExemple: !ask Comment vas-tu?",
        inline=False
    )
    embed.add_field(
        name="!remember [@user] [clé] is [valeur]",
        value="Enregistre une information pour un utilisateur",
        inline=False
    )
    embed.add_field(
        name="!forget [@user] [clé]",
        value="Oublie une information pour un utilisateur",
        inline=False
    )
    embed.add_field(
        name="!help",
        value="Affiche ce message d'aide",
        inline=False
    )
    embed.add_field(
        name="!lang [language]",
        value="Définit la langue préférée (fr, en, es, ru)",
        inline=False
    )
    embed.add_field(
        name="!history",
        value="Affiche l'historique de conversation",
        inline=False
    )
    embed.add_field(
        name="!about",
        value="Affiche des informations sur le bot",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='lang')
async def set_language(ctx, lang: str):
    user_id = str(ctx.author.id)
    supported_languages = ['fr', 'en', 'es', 'ru']
    if lang in supported_languages:
        memory.add_memory(user_id, 'preferences', 'language', lang)
        await ctx.send(f'Langue définie à {lang}.')
    else:
        await ctx.send(f'Langues prises en charge: {", ".join(supported_languages)}')

@bot.command(name='history')
async def history(ctx):
    user_id = str(ctx.author.id)
    hist = conversation_memory.get_memory(user_id, 'history', [])
    if not hist:
        await ctx.send("❌ Aucun historique de conversation.")
        return
    
    embed = discord.Embed(
        title="📜 Historique de conversation",
        color=discord.Color.blue()
    )
    for i, msg in enumerate(hist, 1):
        embed.add_field(
            name=f"Message {i}",
            value=msg,
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name='about')
async def about(ctx):
    embed = discord.Embed(
        title="🤖 À propos de SHADEBOT",
        description="Bot Discord utilisant Venice.ai pour les interactions intelligentes.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Version",
        value="1.0.0",
        inline=False
    )
    embed.add_field(
        name="Auteur",
        value="GreenLab",
        inline=False
    )
    embed.add_field(
        name="GitHub",
        value="https://github.com/GreenLab-TheSeeds/ShadeBot",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='airdrop')
async def airdrop(ctx, action=None, *args):
    if action is None:
        embed = discord.Embed(
            title="🎁 Cosmos Airdrop Tracker",
            description="Gérez vos airdrops Cosmos",
            color=discord.Color.green()
        )
        embed.add_field(
            name="!airdrop check [address]",
            value="Vérifie les airdrops pour une adresse",
            inline=False
        )
        embed.add_field(
            name="!airdrop list",
            value="Liste vos adresses enregistrées",
            inline=False
        )
        await ctx.send(embed=embed)
        return

    if action == "check":
        if not args:
            await ctx.send("❓ Veuillez spécifier une adresse Cosmos")
            return
        
        address = args[0]
        async with ctx.typing():
            result = await airdrop_tracker.check_eligibility(address, "cosmoshub")
            
            if "error" in result:
                await ctx.send(f"❌ Erreur: {result['error']}")
                return
                
            embed = discord.Embed(
                title=f"🎁 Vérification Airdrop",
                description=f"Adresse: `{address}`",
                color=discord.Color.blue()
            )
            
            for balance in result.get("balances", []):
                embed.add_field(
                    name=f"💰 {balance.get('denom', 'unknown')}",
                    value=f"Montant: {balance.get('amount', '0')}",
                    inline=True
                )
                
            await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))