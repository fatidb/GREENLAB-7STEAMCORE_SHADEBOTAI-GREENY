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

# Configuration simplifiée du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'C:\\BIG GREEN 2025 V01\\shaderbotV001\\logs\\bot_{datetime.datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)

# Style terminal retro
TERMINAL_STYLE = {
    "color": 0x2C2C2C,  # Noir profond
    "footer_icon": "https://i.imgur.com/3QZ7Jnk.png",
    "thumbnail": "https://i.imgur.com/5b4WwLp.gif"
}

# Chargement des variables d'environnement
load_dotenv('C:\\BIG GREEN 2025 V01\\shaderbotV001\\config\\.env')

# Fichier de mémoire persistante
MEMORY_FILE = 'memory.json'

# Charger la mémoire existante
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Sauvegarder la mémoire
def save_memory(memory):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=4)

# Initialiser la mémoire
memory = load_memory()

class EnhancedCosmosTracker(CosmosAirdropTracker):
    async def check_eligibility(self, address, network):
        try:
            # Ajout d'un timeout et de réessais
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(f"https://api-cosmoshub-ia.cosmosia.notional.ventures/cosmos/bank/v1beta1/balances/{address}") as response:
                    if response.status == 200:
                        return await response.json()
                    return {"error": f"HTTP Error {response.status}"}
        except Exception as e:
            return {"error": f"Erreur réseau: {str(e)}"}

# Configuration du bot
intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    help_command=None,
    activity=discord.Game(name="T7STEAM AI CORE | !help")
)

airdrop_tracker = EnhancedCosmosTracker()

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

@bot.command(name='airdrop')
async def airdrop(ctx, action=None, *args):
    """Gestion améliorée des airdrops avec style rétro"""
    if not action:
        embed = Embed(
            title="🛰 COSMOS AIRDROP TERMINAL",
            description="```diff\n+ ACTIVEZ VOS RÉCOMPENSES COSMOS\n```",
            color=TERMINAL_STYLE["color"]
        )
        embed.add_field(
            name="🔍 `check [address]`",
            value="```Vérification des éligibilités```",
            inline=False
        )
        embed.add_field(
            name="📋 `list`", 
            value="```Liste des adresses enregistrées```",
            inline=False
        )
        embed.set_thumbnail(url=TERMINAL_STYLE["thumbnail"])
        await ctx.send(embed=embed)
        return

    if action == "check":
        if not args:
            return await ctx.send("```diff\n- ERREUR: Spécifiez une adresse Cosmos valide\n```")
        
        address = args[0]
        async with ctx.typing():
            result = await airdrop_tracker.check_eligibility(address, "cosmos")
            
            if "error" in result:
                embed = Embed(
                    title="🚨 ERREUR SYSTÈME",
                    description=f"```fix\n{result['error']}\n```",
                    color=0xff0000
                )
                return await ctx.send(embed=embed)
                
            embed = Embed(
                title=f"📡 DONNÉES AIRDROP - {address[:12]}...",
                color=TERMINAL_STYLE["color"]
            )
            for balance in result.get("balances", []):
                emoji = "🟢" if float(balance.get('amount', 0)) > 0 else "🔴"
                embed.add_field(
                    name=f"{emoji} {balance.get('denom', 'unknown').upper()}",
                    value=f"```yaml\n{balance.get('amount', '0')}```",
                    inline=True
                )
            embed.set_footer(text="T7STEAM AI CORE v7.3", icon_url=TERMINAL_STYLE["footer_icon"])
            await ctx.send(embed=embed)

@bot.command(name='greeny_help')
async def greeny_help(ctx):
    await ctx.send(embed=generate_help_embed())

@bot.command(name='scrt7')
async def scrt7(ctx, action, member: discord.Member, *, info=None):
    """Commandes secrètes pour gérer la mémoire du bot"""
    user_id = str(member.id)
    
    if action == "remember":
        if not info:
            await ctx.send("```diff\n- ERREUR: Spécifiez ce que je dois me rappeler\n```")
            return
        memory[user_id] = info
        save_memory(memory)
        await ctx.send(f"```diff\n+ Je me souviendrai que {member.display_name} {info}\n```")
    
    elif action == "forget":
        if user_id in memory:
            del memory[user_id]
            save_memory(memory)
            await ctx.send(f"```diff\n+ J'ai oublié ce que je savais sur {member.display_name}\n```")
        else:
            await ctx.send(f"```diff\n- Je n'ai rien à oublier pour {member.display_name}\n```")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Vérification des permissions d'administrateur
    def is_admin(user):
        return any(role.permissions.administrator for role in user.roles)

    # Gestion des commandes naturelles
    if message.content.lower().startswith('greeny'):
        content = message.content[6:].strip().lower()
        
        if 'check my airdrop' in content:
            address = content.split('check my airdrop')[-1].strip()
            await handle_airdrop_check(message.channel, address)
            return
            
        elif 'commands' in content or 'help me' in content:
            await message.channel.send(embed=generate_help_embed())
            return

        elif 'remember my secret' in content:
            if not is_admin(message.author):
                await message.channel.send("```diff\n- ERREUR: Vous devez être administrateur pour utiliser cette commande.\n```")
                return

            parts = content.split('remember my secret')
            if len(parts) > 1:
                info = parts[1].strip()
                user_id = str(message.author.id)
                memory[user_id] = info
                save_memory(memory)
                await message.channel.send(f"```diff\n+ Je me souviendrai que {message.author.display_name} {info}\n```")
            else:
                await message.channel.send("```diff\n- ERREUR: Spécifiez ce que je dois me rappeler\n```")
            return

        elif 'forget' in content:
            if not is_admin(message.author):
                await message.channel.send("```diff\n- ERREUR: Vous devez être administrateur pour utiliser cette commande.\n```")
                return

            user_id = str(message.author.id)
            if user_id in memory:
                del memory[user_id]
                save_memory(memory)
                await message.channel.send(f"```diff\n+ J'ai oublié ce que je savais sur {message.author.display_name}\n```")
            else:
                await message.channel.send(f"```diff\n- Je n'ai rien à oublier pour {message.author.display_name}\n```")
            return

    await bot.process_commands(message)

def generate_help_embed():
    embed = Embed(
        title="🖥 TERMINAL D'AIDE - GREENY v7.3",
        color=TERMINAL_STYLE["color"]
    )
    embed.add_field(
        name="```!airdrop check [address]```",
        value="Vérifie l'éligibilité pour un airdrop Cosmos",
        inline=False
    )
    embed.add_field(
        name="```!airdrop list```",
        value="Liste les adresses enregistrées",
        inline=False
    )
    embed.add_field(
        name="```!degen [action]```",
        value="Mode dégénéré activé",
        inline=False
    )
    embed.add_field(
        name="```!scrt7 remember @user [info]```",
        value="Se souvenir de quelque chose à propos d'un utilisateur",
        inline=False
    )
    embed.add_field(
        name="```!scrt7 forget @user```",
        value="Oublier ce qui a été mémorisé pour un utilisateur",
        inline=False
    )
    embed.set_thumbnail(url=TERMINAL_STYLE["thumbnail"])
    return embed

bot.run(os.getenv('DISCORD_TOKEN'))