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
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/bot_{datetime.datetime.now().strftime("%Y%m%d")}.log')
    ]
)

# Load environment variables
load_dotenv('config/.env')

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
VENICE_API_KEY = os.getenv('VENICE_API_KEY')

# Bot Intents
intents = Intents.default()
intents.message_content = True
intents.members = True

# API Headers
VENICE_HEADERS = {
    "Authorization": f"Bearer {VENICE_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/json"
}

# Bot Styling
BOT_STYLE = {
    "color": 0x2ecc71,
    "footer_icon": "https://i.imgur.com/3QZ7Jnk.png",
    "thumbnail": "https://i.imgur.com/5b4WwLp.gif"
}

# API Endpoints
API_ENDPOINTS = {
    "JOKES": "https://v2.jokeapi.dev/joke/Any",
    "MEMES": "https://meme-api.com/gimme",
    "FACTS": "https://uselessfacts.jsph.pl/random.json",
    "COINGECKO": "https://api.coingecko.com/api/v3",
    "BINANCE": "https://api.binance.com/api/v3",
    "DOGS": "https://dog.ceo/api/breeds/image/random"
}

class GreenyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            activity=discord.Game(name="!help | GREENY v7.4")
        )
        # Mémoire contextuelle de v7.0
        self.memory = ConversationMemory()
        
        # Crypto keywords de v7.0
        self.crypto_keywords = CRYPTO_KEYWORDS
        
        # APIs et rate limits de v7.4
        self.api_endpoints = API_ENDPOINTS
        self.rate_limits = defaultdict(lambda: defaultdict(float))

    async def setup_hook(self):
        try:
            await self.tree.sync()
            logging.info("Command tree synced")
        except Exception as e:
            logging.error(f"Error syncing command tree: {str(e)}")

    def load_memory(self):
        try:
            with open('data/memory.json', 'r') as f:
                self.memory = json.load(f)
        except FileNotFoundError:
            self.memory = {}
            self.save_memory()

    def save_memory(self):
        with open('data/memory.json', 'w') as f:
            json.dump(self.memory, f, indent=4)

    async def ask_venice(self, question: str, context: Optional[str] = None) -> str:
        try:
            messages = [
                {"role": "system", "content": "You are GREENY, a friendly and knowledgeable crypto AI assistant. Always respond in English."},
                {"role": "user", "content": question}
            ]
            
            if context:
                messages.insert(1, {"role": "system", "content": context})

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.venice.ai/api/v1/chat/completions",
                    headers=VENICE_HEADERS,
                    json={
                        "model": "dolphin-2.9.2-qwen2-72b",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                ) as response:
                    try:
                        data = await response.json(content_type=None)
                        if 'choices' in data and len(data['choices']) > 0:
                            return data['choices'][0]['message']['content']
                        logging.error(f"Unexpected response format: {data}")
                    except Exception as e:
                        logging.error(f"JSON parsing error: {str(e)}")
                    
                    return "I'm having trouble processing your request. Try: 'joke', 'meme', 'dog', or 'price btc'"
        except Exception as e:
            logging.error(f"Venice API Error: {str(e)}")
            return "Try these commands: 'joke', 'meme', 'dog', or 'price btc'"

    # Nouvelle fonction pour CoinGecko
    async def get_crypto_price(self, crypto_id: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_ENDPOINTS['COINGECKO']}/simple/price?ids={crypto_id}&vs_currencies=usd") as response:
                    if response.status == 200:
                        data = await response.json()
                        if crypto_id in data:
                            price = data[crypto_id]['usd']
                            return f"💰 {crypto_id.upper()} Price: ${price:,.2f} USD"
                    return "Could not fetch price data."
        except Exception as e:
            logging.error(f"CoinGecko API Error: {str(e)}")
            return "Error fetching price data."

    # Nouvelle fonction pour Binance
    async def get_binance_price(self, symbol: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_ENDPOINTS['BINANCE']}/ticker/price?symbol={symbol.upper()}") as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['price'])
                        return f"📊 {symbol.upper()} Price: ${price:,.2f} USD"
                    return "Could not fetch Binance price."
        except Exception as e:
            logging.error(f"Binance API Error: {str(e)}")
            return "Error fetching Binance data."

    # Fun commands
    async def get_random_joke(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_ENDPOINTS["JOKES"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["type"] == "single":
                            return f"😄 {data['joke']}"
                        else:
                            return f"😄 {data['setup']}\n\n🎯 {data['delivery']}"
                    return "Couldn't fetch a joke right now!"
        except Exception as e:
            return "Error fetching joke!"

    async def get_random_meme(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_ENDPOINTS["MEMES"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["url"]
                    return "Couldn't fetch a meme right now!"
        except Exception as e:
            return "Error fetching meme!"

    async def get_random_fact(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_ENDPOINTS["FACTS"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"🤓 {data['text']}"
                    return "Couldn't fetch a fact right now!"
        except Exception as e:
            return "Error fetching fact!"

    async def get_random_dog(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_ENDPOINTS["DOGS"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["message"]
                    return "Couldn't fetch a dog picture right now!"
        except Exception as e:
            return "Error fetching dog picture!"

    def add_commands(self):
        @self.command(name='joke')
        async def joke(ctx):
            """Get a random joke"""
            async with ctx.typing():
                response = await self.get_random_joke()
                await ctx.send(response)

        @self.command(name='meme')
        async def meme(ctx):
            """Get a random meme"""
            async with ctx.typing():
                meme_url = await self.get_random_meme()
                embed = Embed(color=BOT_STYLE["color"])
                embed.set_image(url=meme_url)
                await ctx.send(embed=embed)

        @self.command(name='fact')
        async def fact(ctx):
            """Get a random fact"""
            async with ctx.typing():
                response = await self.get_random_fact()
                await ctx.send(response)

        @self.command(name='dog')
        async def dog(ctx):
            """Get a random dog picture"""
            async with ctx.typing():
                dog_url = await self.get_random_dog()
                embed = Embed(color=BOT_STYLE["color"])
                embed.set_image(url=dog_url)
                await ctx.send(embed=embed)

bot = GreenyBot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    logging.info(f"\n{'-'*40}")
    logging.info(f"       GREENY - Advanced Crypto AI Bot")
    logging.info(f"        Version 7.4 | Enhanced Core")
    logging.info(f"{'-'*40}")
    logging.info(f"Connected as {bot.user.name}")
    logging.info(f"Bot ID: {bot.user.id}")
    logging.info(f"Serving {len(bot.guilds)} servers")
    logging.info(f"{'-'*40}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    
    # Réactions crypto (de v7.0)
    for keyword, emojis in self.crypto_keywords.items():
        if keyword in content:
            for emoji in emojis:
                await message.add_reaction(emoji)

    # Commandes naturelles
    if content == "joke":
        await self.get_joke(message)
    elif content == "dog":
        await self.get_dog(message)
    elif content == "meme":
        await self.get_meme(message)
    elif content.startswith("price "):
        crypto = content[6:].strip()
        await self.get_crypto_price(crypto)
    elif "greeny" in content:
        # Utiliser Venice avec contexte (de v7.0)
        question = content.replace("greeny", "").strip()
        if question:
            await self.ask_venice(question)

    await self.process_commands(message)

@bot.command(name='help')
async def help_command(ctx):
    embed = Embed(
        title="🤖 GREENY Bot Commands",
        description="Your advanced crypto AI assistant!",
        color=BOT_STYLE["color"]
    )
    
    embed.add_field(
        name="🎯 Fun Commands",
        value="• `joke` - Get a random joke\n• `meme` - Get a random meme\n• `dog` - Get a cute dog picture",
        inline=False
    )
    
    embed.add_field(
        name="💰 Crypto",
        value="• `price <crypto>` - Get crypto price\n• `greeny` + your question",
        inline=False
    )
    
    embed.set_thumbnail(url=BOT_STYLE["thumbnail"])
    embed.set_footer(text="GREENY v7.4", icon_url=BOT_STYLE["footer_icon"])
    
    await ctx.send(embed=embed)

@bot.command(name='ask')
async def ask(ctx, *, question):
    """Ask GREENY anything"""
    async with ctx.typing():
        response = await bot.ask_venice(question)
        await ctx.send(response)

@bot.command(name='analyze')
async def analyze(ctx, *, target):
    """Analyze a wallet or project"""
    async with ctx.typing():
        response = await bot.ask_venice(
            f"Provide a detailed analysis of: {target}",
            context="You are a crypto analysis expert. Provide detailed insights."
        )
        await ctx.send(response)

@bot.command(name='price')
async def price(ctx, crypto: str):
    """Get crypto price from multiple sources"""
    async with ctx.typing():
        # Try CoinGecko first
        coingecko_response = await bot.get_crypto_price(crypto.lower())
        binance_response = await bot.get_binance_price(f"{crypto}USDT")
        
        embed = Embed(
            title=f"🔍 Price Check: {crypto.upper()}",
            color=BOT_STYLE["color"]
        )
        embed.add_field(name="CoinGecko", value=coingecko_response, inline=False)
        embed.add_field(name="Binance", value=binance_response, inline=False)
        embed.set_footer(text="Data from multiple sources", icon_url=BOT_STYLE["footer_icon"])
        
        await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)