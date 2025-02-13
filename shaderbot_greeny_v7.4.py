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
from langdetect import detect
import time

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
    "color": 0x2ecc71,  # Matrix Green
    "footer_icon": "https://i.imgur.com/3QZ7Jnk.png",  # Matrix icon
    "thumbnail": "https://i.imgur.com/5b4WwLp.gif",  # Matrix rain gif
    "background": 0x000000,  # Pure black
    "font": "Courier New"  # Terminal font
}

# API Endpoints
API_ENDPOINTS = {
    "WIKI": "https://fr.wikipedia.org/w/api.php",
    "NEWS": "https://newsapi.org/v2",
    "COINGECKO": "https://api.coingecko.com/api/v3",
    "DOGS": "https://dog.ceo/api",
    "JOKES": "https://v2.jokeapi.dev",
    "MEALS": "https://www.themealdb.com/api/json/v1/1",
    "BINANCE": "https://api.binance.com/api/v3"
}

class GreenyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            activity=discord.Game(name="!help | GREENY v7.4")
        )
        self.memory = {}
        self.load_memory()
        self.cache = {}
        self.rate_limits = defaultdict(lambda: defaultdict(float))  # Stockage des timestamps
        self.api_limits = {
            "COINGECKO": 1.0,    # 1 requête/seconde
            "BINANCE": 0.5,      # 2 requêtes/seconde
            "VENICE": 2.0,       # 1 requête/2 secondes
            "WIKI": 1.0,         # 1 requête/seconde
            "DEFAULT": 1.0       # Limite par défaut
        }

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

    async def ask_venice(self, question: str, user: discord.Member, context: Optional[str] = None) -> str:
        # Récupérer la mémoire de l'utilisateur
        user_memory = self.memory.get(str(user.id), {})
        is_admin = user.guild_permissions.administrator
        
        messages = [
            {
                "role": "system", 
                "content": """You are GREENY, a Web3 dev from the 90s era. 
                Personality traits:
                - Matrix movie references 🕶️
                - Boomer-style tech jokes
                - Serious about crypto/code
                - Casual about everything else
                - Use 90s/2000s references
                
                Key behaviors:
                - Remember users and their preferences
                - Extra respectful to admins
                - Mix humor with technical accuracy
                - 'Take the red pill' approach to teaching
                """
            },
            {"role": "system", "content": f"User context: {user_memory}"},
            {"role": "system", "content": f"Admin status: {is_admin}"},
            {"role": "user", "content": question}
        ]
        
        # Update user memory
        if '@' in question:
            mentioned = message.mentions[0] if message.mentions else None
            if mentioned:
                self.memory[str(mentioned.id)] = {
                    'last_mention': datetime.now().isoformat(),
                    'context': question
                }
        
        # Add VVV context with style
        if "vvv" in question.lower() or "vcu" in question.lower():
            messages.insert(1, {
                "role": "system", 
                "content": """What if I told you... VVV stats:
                - APR: 97.79% (not a glitch in the Matrix)
                - VCU Rate: 1 VVV = 0.313 VCU/day
                
                Take the red pill for more details..."""
            })

        # Détection et respect de la langue
        try:
            user_lang = detect(question)
            messages[0]["content"] += f" Please respond in {user_lang}."
        except:
            pass

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
        """Get random knowledge from the Matrix"""
        sources = ['WIKI', 'NEWS', 'JOKES', 'MEALS']
        source = random.choice(sources)
        
        if source == 'WIKI':
            data = await self.fetch_data('WIKI', 'random')
        elif source == 'NEWS':
            data = await self.fetch_data('NEWS', 'top-headlines')
        elif source == 'JOKES':
            data = await self.fetch_data('JOKES', 'Any')
        else:
            data = await self.fetch_data('MEALS', 'random.php')
            
        return self.format_matrix_style(data)

    def format_matrix_style(self, data: dict) -> str:
        """Format response in Matrix style"""
        return f"🕶️ [Matrix Data Feed]: {json.dumps(data, indent=2)}"

    def create_matrix_embed(self, title: str, description: str) -> discord.Embed:
        """Create Matrix-styled embed"""
        embed = discord.Embed(
            title=f"🖥️ {title}",
            description=f"```ansi\n\u001b[32m{description}\u001b[0m\n```",
            color=BOT_STYLE["color"]
        )
        embed.set_thumbnail(url=BOT_STYLE["thumbnail"])
        embed.set_footer(
            text="GREENY v7.4 | Matrix Protocol",
            icon_url=BOT_STYLE["footer_icon"]
        )
        return embed

    async def fetch_data(self, api_name: str, endpoint: str, params: dict = None) -> dict:
        """Enhanced Matrix-style data fetching with rate limiting and cache"""
        cache_key = f"{api_name}:{endpoint}:{str(params)}"
        
        # Check rate limits
        if self.is_rate_limited(api_name):
            return {"error": "Too many red pills. Wait for system cooldown..."}
            
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{API_ENDPOINTS[api_name]}/{endpoint}"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Cache the response
                        self.cache[cache_key] = data
                        # Update rate limit
                        self.update_rate_limit(api_name)
                        return data
                    return {
                        "error": f"[ERROR {response.status}] Agent Smith detected...",
                        "matrix_code": "RED_PILL_REJECTED"
                    }
        except Exception as e:
            return {
                "error": "⚠️ MATRIX BREACH DETECTED ⚠️",
                "details": str(e),
                "solution": "Need operator intervention. Take the blue pill and try again."
            }

    @commands.command(name='matrix')
    async def matrix_command(self, ctx, source: str, *args):
        """Access the Matrix mainframe"""
        loading_msg = await ctx.send("```ansi\n\u001b[32mInitializing Matrix connection...\u001b[0m\n```")
        
        try:
            data = await self.fetch_data(source.upper(), *args)
            
            if "error" in data:
                embed = self.create_matrix_embed(
                    "System Failure",
                    f"🚫 {data['error']}\n⚡ Matrix connection unstable"
                )
            else:
                formatted_data = json.dumps(data, indent=2)
                embed = self.create_matrix_embed(
                    "Matrix Data Retrieved",
                    f"📊 Data Stream:\n{formatted_data}"
                )
            
            await loading_msg.delete()
            await ctx.send(embed=embed)
            
        except Exception as e:
            await loading_msg.edit(content="```ansi\n\u001b[31mMATRIX CONNECTION LOST\u001b[0m\n```")

    async def get_crypto_info(self, coin: str) -> str:
        """Get crypto data from multiple sources"""
        try:
            # CoinGecko
            gecko_data = await self.fetch_data("COINGECKO", f"simple/price?ids={coin}&vs_currencies=usd")
            
            # Binance
            binance_data = await self.fetch_data("BINANCE", f"ticker/price?symbol={coin.upper()}USDT")
            
            return f"""
            🕶️ Red pill data for {coin.upper()}:
            CoinGecko: ${gecko_data[coin]['usd']:,.2f}
            Binance: ${float(binance_data['price']):,.2f}
            """
        except:
            return "Looks like Agent Smith is messing with the data..."

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

        @self.command(name='matrix')
        async def matrix_data(ctx, source: str, *args):
            """Access the Matrix data"""
            response = await self.fetch_data(source.upper(), *args)
            await ctx.send(f"```json\n{json.dumps(response, indent=2)}\n```")

    def is_rate_limited(self, api_name: str) -> bool:
        """
        Vérifie si on peut faire une nouvelle requête
        Retourne True si on doit attendre
        """
        now = time.time()
        last_call = self.rate_limits[api_name]
        limit = self.api_limits.get(api_name, self.api_limits["DEFAULT"])
        
        return (now - last_call) < limit  # True = doit attendre

    def update_rate_limit(self, api_name: str):
        """
        Enregistre quand on fait une requête
        """
        self.rate_limits[api_name] = time.time()

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
    
    # Commandes simples
    if content == "joke":
        async with aiohttp.ClientSession() as session:
            async with session.get("https://v2.jokeapi.dev/joke/Any") as response:
                data = await response.json()
                if data["type"] == "single":
                    await message.channel.send(f"😄 {data['joke']}")
                else:
                    await message.channel.send(f"😄 {data['setup']}\n\n🎯 {data['delivery']}")
    
    elif content == "dog":
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                data = await response.json()
                embed = discord.Embed(color=0x2ecc71)
                embed.set_image(url=data["message"])
                await message.channel.send(embed=embed)
    
    elif content == "meme":
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as response:
                data = await response.json()
                embed = discord.Embed(color=0x2ecc71)
                embed.set_image(url=data["url"])
                await message.channel.send(embed=embed)
    
    elif content.startswith("price "):
        crypto = content[6:]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd") as response:
                data = await response.json()
                if crypto in data:
                    price = data[crypto]['usd']
                    await message.channel.send(f"💰 {crypto.upper()} Price: ${price:,.2f} USD")
    
    elif content == "help":
        help_text = """
Available commands:
- `joke` : Get a random joke
- `dog` : See a cute dog
- `meme` : Get a random meme
- `price btc` : Get crypto price
- `help` : Show this help
        """
        await message.channel.send(help_text)

    await bot.process_commands(message)

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
        response = await bot.ask_venice(question, ctx.author)
        await ctx.send(response)

@bot.command(name='analyze')
async def analyze(ctx, *, target):
    """Analyze a wallet or project"""
    async with ctx.typing():
        response = await bot.ask_venice(
            f"Provide a detailed analysis of: {target}",
            ctx.author,
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

@bot.command(name='admin')
@commands.has_permissions(administrator=True)
async def admin_command(ctx, *, command):
    """Matrix-style admin interface"""
    response = f"⚡ Operator, welcome to the mainframe...\n"
    # Admin specific logic here

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)