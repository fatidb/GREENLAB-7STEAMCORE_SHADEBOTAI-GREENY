# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import Intents, Embed
import os
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
