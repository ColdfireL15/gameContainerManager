import os
import json
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
from discord import app_commands
from discord.ui import Button, View

load_dotenv()
TOKEN = os.getenv('DOCKERCONTAINERMANAGER_DISCORD_TOKEN')
DEBUG = os.getenv('DOCKERCONTAINERMANAGER_DEBUG')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:5001')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

def load_data():
    try:
        response = requests.get(f"{BACKEND_URL}/api/containers")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des données: {str(e)}")
        return []

# Fonction d'autocomplétion pour les noms de conteneurs
async def container_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    data = load_data()
    containers = [container['name'] for container in data]
    return [
        app_commands.Choice(name=container, value=container)
        for container in containers if current.lower() in container.lower()
    ]

class ContainerActions(View):
    def __init__(self, container_name):
        super().__init__(timeout=300)
        self.container_name = container_name

    @discord.ui.button(label="Redémarrer", style=discord.ButtonStyle.green, emoji="⚡")
    async def restart_button(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/restart")
                    response.raise_for_status()
                    
                    embed = discord.Embed(
                        title=f"Conteneur {self.container_name}",
                        description="✅ Redémarré avec succès",
                        color=discord.Color.green()
                    )
                    await interaction.response.edit_message(embed=embed, view=None)
                except requests.RequestException as e:
                    error_embed = discord.Embed(
                        title="Erreur",
                        description=f"❌ Erreur lors du redémarrage du conteneur: {str(e)}",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
        
        await interaction.response.send_message(
            f"Conteneur {self.container_name} non trouvé.", 
            ephemeral=True
        )

    @discord.ui.button(label="Arrêter", style=discord.ButtonStyle.red, emoji="🛑")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/stop")
                    response.raise_for_status()
                    
                    embed = discord.Embed(
                        title=f"Conteneur {self.container_name}",
                        description="✅ Arrêté avec succès",
                        color=discord.Color.red()
                    )
                    await interaction.response.edit_message(embed=embed, view=None)
                except requests.RequestException as e:
                    error_embed = discord.Embed(
                        title="Erreur",
                        description=f"❌ Erreur lors de l'arrêt du conteneur: {str(e)}",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
                
        await interaction.response.send_message(
            f"Conteneur {self.container_name} non trouvé.", 
            ephemeral=True
        )

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.blurple, emoji="📜")
    async def logs_button(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                embed = discord.Embed(
                    title=f"Logs du conteneur {self.container_name}",
                    description=f"```{container['logs']}```",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        await interaction.response.send_message(f"Conteneur {self.container_name} non trouvé.", ephemeral=True)

@bot.tree.command(name="status", description="Affiche l'état de tous les conteneurs")
async def status(interaction: discord.Interaction):
    data = load_data()
    embed = discord.Embed(
        title="État des conteneurs",
        color=discord.Color.blue()
    )
    
    for container in data:
        status_emoji = "🟢" if container['status'] == 'running' else "🔴"
        embed.add_field(
            name=f"{status_emoji} {container['name']}",
            value=f"Status: {container['status']}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="container", description="Gérer un conteneur spécifique")
@app_commands.describe(container_name="Nom du conteneur à gérer")
@app_commands.autocomplete(container_name=container_autocomplete)
async def container_slash(interaction: discord.Interaction, container_name: str):
    data = load_data()
    container_found = False
    
    for container in data:
        if container['name'] == container_name:
            container_found = True
            status_emoji = "🟢" if container['status'] == 'running' else "🔴"
            embed = discord.Embed(
                title=f"Gestion du conteneur {container_name}",
                description=f"Status: {status_emoji} {container['status']}",
                color=discord.Color.blue()
            )
            
            view = ContainerActions(container_name)
            await interaction.response.send_message(embed=embed, view=view)
            break
    
    if not container_found:
        embed = discord.Embed(
            title="Erreur",
            description=f"Conteneur {container_name} non trouvé",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="aide", description="Affiche l'aide du bot")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Aide du Bot Docker Manager",
        description="Voici les commandes disponibles :",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="/status",
        value="Affiche l'état de tous les conteneurs",
        inline=False
    )
    embed.add_field(
        name="/container <nom>",
        value="Affiche les options de gestion pour un conteneur spécifique",
        inline=False
    )
    embed.add_field(
        name="/aide",
        value="Affiche ce message d'aide",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} est en ligne !')
    print(f'ID du bot: {bot.user.id}')
    print(f'Serveurs connectés: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'- {guild.name} (id: {guild.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Commandes synchronisées: {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation: {str(e)}")

try:
    print("Tentative de démarrage du bot...")
    bot.run(TOKEN)
except Exception as e:
    print(f"Erreur lors du démarrage du bot: {str(e)}")

bot.run(TOKEN) 