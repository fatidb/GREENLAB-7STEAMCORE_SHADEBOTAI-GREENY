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
    logging.info(f"\n{'-'*40}")
    logging.info(f" T7STEAM - The Shader AI Bot ".center(40, ' '))
    logging.info(f" Version 7.1.1 | Greeny CORE ".center(40, ' '))
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
            embed.set_footer(text="T7STEAM AI CORE v7.1.1", icon_url=TERMINAL_STYLE["footer_icon"])
            await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Gestion des commandes naturelles
    if message.content.lower().startswith('greeny'):
        content = message.content[6:].strip().lower()
        
        if 'check my airdrop' in content:
            address = content.split('check my airdrop')[-1].strip()
            await handle_airdrop_check(message.channel, address)
            return
            
        elif 'commands' in content:
            await message.channel.send(embed=generate_help_embed())
            return

    await bot.process_commands(message)

def generate_help_embed():
    embed = Embed(
        title="🖥 TERMINAL D'AIDE - GREENY v7.1.1",
        color=TERMINAL_STYLE["color"]
    )
    embed.add_field(
        name="```!airdrop check [address]```",
        value="Scan d'éligibilité Cosmos",
        inline=False
    )
    embed.add_field(
        name="```!degen [action]```", 
        value="Mode dégénéré activé",
        inline=False
    )
    embed.set_thumbnail(url=TERMINAL_STYLE["thumbnail"])
    return embed

bot.run(os.getenv('DISCORD_TOKEN'))