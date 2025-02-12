# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import Intents, Embed
import os
from dotenv import load_dotenv
import aiohttp
import json
import logging
import datetime
import random
from collections import defaultdict
from langdetect import detect, lang_detect_exception
from trackers.cosmos_tracker import CosmosAirdropTracker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\logs\\bot_{datetime.datetime.now().strftime("%Y%m%d")}.log')
    ]
)

# Charger les variables d'environnement
load_dotenv('C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\config\\.env')

# Configuration du bot
intents = Intents.default()
intents.message_content = True
intents.members = True

# Configuration Venice API
VENICE_API_KEY = os.getenv('VENICE_API_KEY')
VENICE_HEADERS = {
    "Authorization": f"Bearer {VENICE_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/json"
}

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

# Style terminal retro
TERMINAL_STYLE = {
    "color": 0x2C2C2C,
    "footer_icon": "https://i.imgur.com/3QZ7Jnk.png",
    "thumbnail": "https://i.imgur.com/5b4WwLp.gif"
}

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
airdrop_tracker = CosmosAirdropTracker()

class PersistentMemory:
    def __init__(self):
        self.file_path = 'C:\\BIG GREEN 2025 V01\\t7steam-core\\t7steam-c1-shadebot\\memory.json'
        self.data = self._load_memory()

    def _load_memory(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {'users': {}, 'preferences': {}, 'alerts': {}, 'monitoring': {}}
        except Exception as e:
            logging.error(f"Erreur de chargement mémoire : {str(e)}")
            return {'users': {}, 'preferences': {}, 'alerts': {}, 'monitoring': {}}

    def _save_memory(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Erreur de sauvegarde mémoire : {str(e)}")

    def remember(self, user_id: str, key: str, value: str):
        if user_id not in self.data['users']:
            self.data['users'][user_id] = {}
        self.data['users'][user_id][key] = value
        self._save_memory()

    def forget(self, user_id: str, key: str = None):
        if key:
            if user_id in self.data['users'] and key in self.data['users'][user_id]:
                del self.data['users'][user_id][key]
                self._save_memory()
                return True
        return False

    def get_memory(self, user_id: str, key: str = None):
        if user_id in self.data['users']:
            if key:
                return self.data['users'][user_id].get(key)
            return self.data['users'][user_id]
        return None

async def ask_venice(question, context=None, task_type="CHAT"):
    try:
        messages = []
        
        # Ajout du contexte système selon le type de tâche
        system_prompts = {
            "CHAT": "Tu es un assistant crypto amical et fun. Utilise des emojis et sois décontracté. Réponds en français.",
            "ANALYSIS": "Tu es un analyste crypto expert. Fournis des analyses détaillées et techniques en français.",
            "TECH": "Tu es un expert technique en blockchain. Aide avec le code et les concepts techniques en français.",
            "MONITOR": "Tu es un système de surveillance. Configure et gère les alertes de prix et événements en français.",
            "TRANSLATE": "Tu es un traducteur spécialisé en crypto. Traduis en gardant les termes techniques appropriés.",
            "SUMMARY": "Tu es un expert en résumé. Synthétise l'information de manière concise et pertinente en français."
        }
        
        messages.append({"role": "system", "content": system_prompts.get(task_type, system_prompts["CHAT"])})
        
        if context:
            messages.append({"role": "system", "content": context})
        
        messages.append({"role": "user", "content": question})
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "dolphin-2.9.2-qwen2-72b",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with session.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers=VENICE_HEADERS,
                json=payload
            ) as response:
                if response.status == 200:
                    # Récupère le texte de la réponse
                    response_text = await response.text()
                    # Parse le JSON manuellement
                    try:
                        data = json.loads(response_text)
                        return data['choices'][0]['message']['content']
                    except json.JSONDecodeError as e:
                        logging.error(f"Erreur de décodage JSON : {str(e)}")
                        return "🤔 Erreur de format des données reçues."
                else:
                    return f"🤔 Erreur {response.status}: {await response.text()}"
    except Exception as e:
        logging.error(f"Erreur Venice: {str(e)}")
        return "🤔 Une erreur s'est produite lors de la communication avec Venice."

# Initialisation de la mémoire
memory = PersistentMemory()
@bot.event
async def on_ready():
    print("\033[1;32mGREENY ONLINE VERT NEON\033[0m")
    logging.info(f"\n{'-'*40}")
    logging.info(f"       T7STEAM - The Shader AI Bot")
    logging.info(f"        Version 7.3 | Greeny CORE")
    logging.info(f"{'-'*40}")
    logging.info(f"Connecté en tant que {bot.user.name}")
    logging.info(f"ID: {bot.user.id}")
    logging.info(f"Serveurs: {len(bot.guilds)}")
    logging.info(f"{'-'*40}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content_lower = message.content.lower()
    
    # Réactions aux mots-clés crypto
    for keyword, emojis in CRYPTO_KEYWORDS.items():
        if keyword in content_lower:
            for emoji in emojis:
                await message.add_reaction(emoji)

    # Traitement des commandes naturelles
    if content_lower.startswith('greeny'):
        async with message.channel.typing():
            query = content_lower[6:].strip()
            
            # Commandes remember/forget
            if 'remember' in query and message.author.guild_permissions.administrator:
                parts = query.split('remember', 1)[1].strip()
                if message.mentions:
                    target = message.mentions[0]
                    content = parts.split(' ', 1)[1] if len(parts.split(' ', 1)) > 1 else ''
                    memory.remember(str(target.id), 'info', content)
                    await message.channel.send(f"🤔 Je me souviendrai que {target.mention}: {content}")
                return

            if 'forget' in query and message.author.guild_permissions.administrator:
                if message.mentions:
                    target = message.mentions[0]
                    memory.forget(str(target.id), 'info')
                    await message.channel.send(f"🤔 J'ai oublié les informations sur {target.mention}")
                return

            # Analyse de wallet
            if 'analyze' in query or 'analyse' in query:
                response = await ask_venice(query, task_type="ANALYSIS")
                await message.channel.send(response)
                return

            # Monitoring
            if 'monitor' in query or 'surveille' in query:
                response = await ask_venice(query, task_type="MONITOR")
                await message.channel.send(response)
                return

            # Traduction
            if 'translate' in query or 'traduis' in query:
                response = await ask_venice(query, task_type="TRANSLATE")
                await message.channel.send(response)
                return

            # Résumé
            if 'summary' in query or 'résume' in query:
                response = await ask_venice(query, task_type="SUMMARY")
                await message.channel.send(response)
                return

            # Support technique
            if any(word in query for word in ['code', 'solidity', 'smart contract', 'help']):
                response = await ask_venice(query, task_type="TECH")
                await message.channel.send(response)
                return

            # Conversation normale
            user_context = memory.get_memory(str(message.author.id))
            context = f"Information sur l'utilisateur: {user_context}" if user_context else None
            response = await ask_venice(query, context=context)
            await message.channel.send(response)

    await bot.process_commands(message)

@bot.command(name='ask')
async def ask(ctx, *, question):
    """Pose une question à  l'IA"""
    async with ctx.typing():
        user_context = memory.get_memory(str(ctx.author.id))
        context = f"Information sur l'utilisateur: {user_context}" if user_context else None
        response = await ask_venice(question, context=context)
        await ctx.send(response)

@bot.command(name='analyze')
async def analyze(ctx, *, target):
    """Analyse un wallet ou un projet"""
    async with ctx.typing():
        response = await ask_venice(f"Analyse détaillée de : {target}", task_type="ANALYSIS")
        await ctx.send(response)

@bot.command(name='monitor')
async def monitor(ctx, *, params):
    """Configure une surveillance de prix ou d'événements"""
    async with ctx.typing():
        response = await ask_venice(f"Configure la surveillance : {params}", task_type="MONITOR")
        await ctx.send(response)

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="🤔 Aide SHADEBOT FULL OPTION",
        description="Je suis votre assistant crypto intelligent !",
        color=TERMINAL_STYLE["color"]
    )
    
    # Commandes de base
    embed.add_field(
        name="🤔 Conversation",
        value="🔹 `greeny` + votre message\n🔹 `!ask` + votre question",
        inline=False
    )
    
    # Commandes d'analyse
    embed.add_field(
        name="🤔 Analyse",
        value="🔹 `greeny analyze` + wallet/projet\n🔹 `!analyze` + wallet/projet",
        inline=False
    )
    
    # Commandes de monitoring
    embed.add_field(
        name="🤔 Monitoring",
        value="🔹 `greeny monitor ETH > 2000`\n🔹 `!monitor BTC 24h`",
        inline=False
    )
    
    # Commandes de traduction
    embed.add_field(
        name="🤔 Traduction",
        value="🔹 `greeny translate` + texte\n🔹 `!translate` + texte",
        inline=False
    )
    
    # Commandes admin
    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="🤔 Admin",
            value="🔹 `greeny remember @user info`\n🔹 `greeny forget @user`",
            inline=False
        )
    
    embed.set_thumbnail(url=TERMINAL_STYLE["thumbnail"])
    embed.set_footer(text="Version 7.3 FULL OPTION", icon_url=TERMINAL_STYLE["footer_icon"])
    
    await ctx.send(embed=embed)

@bot.command(name='airdrop')
async def airdrop(ctx, action=None, *args):
    if action is None:
        embed = discord.Embed(
            title="🤔 Cosmos Airdrop Tracker",
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
            await ctx.send("🤔 Veuillez spécifier une adresse Cosmos")
            return
        
        address = args[0]
        async with ctx.typing():
            result = await airdrop_tracker.check_eligibility(address, "cosmos")
            
            if "error" in result:
                await ctx.send(f"🤔 Erreur: {result['error']}")
                return
                
            embed = discord.Embed(
                title=f"🤔 Vérification Airdrop",
                description=f"Adresse: `{address}`",
                color=discord.Color.blue()
            )
            
            for balance in result.get("balances", []):
                embed.add_field(
                    name=f"🤔 {balance.get('denom', 'unknown')}",
                    value=f"Montant: {balance.get('amount', '0')}",
                    inline=True
                )
                
            await ctx.send(embed=embed)

# Lancer le bot
if __name__ == "__main__":
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logging.error(f"Erreur au démarrage du bot: {str(e)}")