# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import Intents
import os
from dotenv import load_dotenv
import aiohttp
import json
import logging
import datetime
from collections import defaultdict
from langdetect import detect, lang_detect_exception
from trackers.cosmos_tracker import CosmosAirdropTracker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'C:\\BIG GREEN 2025 V01\\shaderbotV001\\logs\\bot_{datetime.datetime.now().strftime("%Y%m%d")}.log')
    ]
)

# Charger les variables d'environnement
load_dotenv('C:\\BIG GREEN 2025 V01\\shaderbotV001\\config\\.env')

# Configuration du bot
intents = Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
# Initialisation des trackers
airdrop_tracker = CosmosAirdropTracker()


# Configuration Venice API
VENICE_API_KEY = os.getenv('VENICE_API_KEY')
VENICE_HEADERS = {
    "Authorization": f"Bearer {VENICE_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
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

# Système de mémoire contextuelle amélioré
class ConversationMemory:
    def __init__(self):
        self.memory = defaultdict(lambda: {
            'context': {},
            'history': [],
            'user_info': {}
        })

    def get_context(self, user_id):
        return self.memory[user_id]['context']

    def update_context(self, user_id, key, value):
        self.memory[user_id]['context'][key] = value

    def get_user_info(self, user_id):
        return self.memory[user_id]['user_info']

    def update_user_info(self, user_id, info):
        self.memory[user_id]['user_info'].update(info)

    def add_history(self, user_id, message):
        if 'history' not in self.memory[user_id]:
            self.memory[user_id]['history'] = []
        self.memory[user_id]['history'].append(message)
        if len(self.memory[user_id]['history']) > 10:
            self.memory[user_id]['history'] = self.memory[user_id]['history'][-10:]

# Initialisation de la mémoire
conversation_memory = ConversationMemory()

# Détecteur de langue
def detect_language(text):
    try:
        return detect(text)
    except lang_detect_exception.LangDetectException:
        return 'en'

# Réponses dans différentes langues
RESPONSES = {
    'greeting': {
        'fr': 'Bonjour! Comment puis-je vous aider?',
        'en': 'Hello! How can I help you?',
        'es': '¡Hola! ¿Cómo puedo ayudarte?',
        'ru': 'Привет! Как я могу вам помочь?'
    },
    'goodbye': {
        'fr': 'Au revoir!',
        'en': 'Goodbye!',
        'es': '¡Adiós!',
        'ru': 'До свидания!'
    }
}

# Préférences linguistiques des utilisateurs
user_languages = {}

@bot.event
async def on_ready():
    logging.info(f'Bot connecté en tant que {bot.user.name}')
    logging.info(f'ID du bot: {bot.user.id}')
    logging.info('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Récupération et stockage automatique des infos Discord
    user_id = str(message.author.id)
    conversation_memory.update_user_info(user_id, {
        'discord_name': message.author.name,
        'display_name': message.author.display_name
    })

    content_lower = message.content.lower()
    
    # Réactions aux mots-clés crypto
    for keyword, emojis in CRYPTO_KEYWORDS.items():
        if keyword in content_lower:
            for emoji in emojis:
                await message.add_reaction(emoji)

    # Détection des triggers simplifiés
    triggers = ['greeny', 'shady']
    
    if not content_lower.startswith('!'):
        for trigger in triggers:
            if trigger in content_lower:
                start_idx = content_lower.find(trigger) + len(trigger)
                question = content_lower[start_idx:].strip()
                
                if question:
                    await ask(message.channel, question=question, user_id=message.author.id)
                else:
                    lang = detect_language(content_lower)
                    greeting = RESPONSES['greeting'][lang] if lang in RESPONSES['greeting'] else RESPONSES['greeting']['en']
                    await message.channel.send(greeting)
                return

    await bot.process_commands(message)
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('pong!')

@bot.command(name='ask')
async def ask(channel, question=None, user_id=None):
    if question is None:
        await channel.send("❌ Merci de poser une question.")
        return

    logging.info(f"Question de {user_id}: {question}")
    
    async with channel.typing():
        try:
            # Récupération du contexte et des infos utilisateur
            user_info = conversation_memory.get_user_info(str(user_id))
            
            messages = []
            if user_info:
                context_msg = f"User information: The user's Discord name is {user_info.get('discord_name')} (display name: {user_info.get('display_name')})"
                messages.append({"role": "system", "content": context_msg})
            
            messages.append({"role": "user", "content": question})
            
            # Détection de la langue
            lang = user_languages.get(str(user_id), detect_language(question))
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "dolphin-2.9.2-qwen2-72b",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                logging.info(f"Envoi requête Venice: {json.dumps(payload)}")
                async with session.post(
                    "https://api.venice.ai/api/v1/chat/completions",
                    headers=VENICE_HEADERS,
                    json=payload
                ) as response:
                    logging.info(f"Status: {response.status}")
                    response_text = await response.text()
                    logging.info(f"Réponse brute: {response_text}")
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            answer = data['choices'][0]['message']['content']
                            
                            # Met à jour le contexte avec la question et la réponse
                            conversation_memory.update_context(str(user_id), 'last_interaction', {
                                'question': question,
                                'answer': answer
                            })
                            conversation_memory.add_history(str(user_id), f"User: {question}\nBot: {answer}")
                            
                            await channel.send(f"🤖 {answer}")
                        except json.JSONDecodeError as e:
                            logging.error(f"Erreur JSON: {e}")
                            await channel.send("❌ Erreur de format dans la réponse.")
                    else:
                        await channel.send(f"❌ Erreur {response.status}: {response_text}")
        except Exception as e:
            logging.error(f"Erreur: {str(e)}", exc_info=True)
            await channel.send("❌ Une erreur s'est produite.")
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
        user_languages[user_id] = lang
        await ctx.send(f'Langue définie à {lang}.')
    else:
        await ctx.send(f'Langues prises en charge: {", ".join(supported_languages)}')

@bot.command(name='history')
async def history(ctx):
    user_id = str(ctx.author.id)
    hist = conversation_memory.memory[user_id].get('history', [])
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

# Lancer le bot

@bot.command(name='airdrop')
async def airdrop(ctx, action=None, *args):
    if action is None:
        embed = discord.Embed(
            title="?? Cosmos Airdrop Tracker",
            description="G�rez vos airdrops Cosmos",
            color=discord.Color.green()
        )
        embed.add_field(
            name="!airdrop check [address]",
            value="V�rifie les airdrops pour une adresse",
            inline=False
        )
        embed.add_field(
            name="!airdrop list",
            value="Liste vos adresses enregistr�es",
            inline=False
        )
        await ctx.send(embed=embed)
        return

    if action == "check":
        if not args:
            await ctx.send("? Veuillez sp�cifier une adresse Cosmos")
            return
        
        address = args[0]
        async with ctx.typing():
            result = await airdrop_tracker.check_eligibility(address, "cosmos")
            
            if "error" in result:
                await ctx.send(f"? Erreur: {result['error']}")
                return
                
            embed = discord.Embed(
                title=f"?? V�rification Airdrop",
                description=f"Adresse: `{address}`",
                color=discord.Color.blue()
            )
            
            for balance in result.get("balances", []):
                embed.add_field(
                    name=f"?? {balance.get('denom', 'unknown')}",
                    value=f"Montant: {balance.get('amount', '0')}",
                    inline=True
                )
                
            await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))

