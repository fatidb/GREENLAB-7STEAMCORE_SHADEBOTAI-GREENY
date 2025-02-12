import os
import json
import logging
import aiohttp
from typing import Dict

class CosmosAirdropTracker:
    def __init__(self):
        self.active_airdrops = {}
        self.user_addresses = {}
        self.networks = self._load_networks()

    def _load_networks(self):
        try:
            with open('config/networks.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erreur chargement networks: {str(e)}")
            return {}

    async def check_eligibility(self, address: str, chain: str = "cosmoshub"):
        try:
            if chain not in self.networks.get("networks", []):
                return {"error": "Chaîne non supportée"}

            endpoint = self.networks["endpoints"][chain]["balances"]
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}{address}") as response:
                    if response.status == 200:
                        return await response.json()
                    return {"error": f"Erreur API: {response.status}"}
        except Exception as e:
            logging.error(f"Erreur vérification airdrop: {str(e)}")
            return {"error": str(e)}