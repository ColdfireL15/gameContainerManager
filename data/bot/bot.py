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
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:5000')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
logs_url = "http://192.168.1.11:5000/"

def load_data():
    try:
        response = requests.get(f"{BACKEND_URL}/api/containers")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des données: {str(e)}")
        return []

def pad_right(text, length):
            return f"{text:<{length}}"

class ContainerActions(View):
    def __init__(self, container_name, container_status):
        super().__init__(timeout=300)
        self.container_name = container_name
        self.container_status = container_status

        if container_status == 'running':
            self.restart_button = Button(label="Redémarrer", style=discord.ButtonStyle.green)
            self.restart_button.callback = self.restart_button_callback
            self.add_item(self.restart_button)
            
            self.stop_button = Button(label="Arrêter", style=discord.ButtonStyle.red)
            self.stop_button.callback = self.stop_button_callback
            self.add_item(self.stop_button)
        else:
            self.restart_button = Button(label="Lancer", style=discord.ButtonStyle.green)
            self.restart_button.callback = self.restart_button_callback
            self.add_item(self.restart_button)

        self.logs_button = Button(label="", style=discord.ButtonStyle.blurple, emoji="📜")
        self.logs_button.callback = self.logs_button_callback
        self.add_item(self.logs_button)

    async def restart_button_callback(self, interaction: discord.Interaction):
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/restart")
                    response.raise_for_status()
                    
                    embed = discord.Embed(
                        title=f"{self.container_name}",
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

    async def stop_button_callback(self, interaction: discord.Interaction):
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/stop")
                    response.raise_for_status()
                    
                    embed = discord.Embed(
                        title=f"{self.container_name}",
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

    async def logs_button_callback(self, interaction: discord.Interaction):
        try:
            data = load_data()
            container_id = None
            for container in data:
                if container['name'] == self.container_name:
                    container_id = container['id']
                    break
            
            if not container_id:
                await interaction.response.send_message(
                    f"Conteneur {self.container_name} non trouvé.", 
                    ephemeral=True
                )
                return

            response = requests.get(f"{BACKEND_URL}/api/container/{container_id}/logs")
            response.raise_for_status()
            logs_data = response.json()

            if logs_data['status'] == 'success':
                logs = logs_data['logs'].strip()
                logs = logs[-1900:]
                
                await interaction.response.send_message(
                    f"Logs : {self.container_name}\n```\n{logs}```\n[Voir plus de logs →]({logs_url})",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Erreur: {logs_data.get('message', 'Erreur inconnue')}",
                    ephemeral=True
                )

        except requests.RequestException as e:
            await interaction.response.send_message(
                f"❌ Erreur lors de la récupération des logs: {str(e)}",
                ephemeral=True
            )

class ContainerSelect(discord.ui.Select):
    def __init__(self, containers):
        options = []
        for container in containers:
            status_emoji = "🟩" if container['status'] == 'running' else "🟥"
            options.append(discord.SelectOption(
                label=container['name'],
                value=container['name'],
                emoji=status_emoji,
                description=f"Status: {container['status']}"
            ))
        
        super().__init__(
            placeholder="Sélectionner un conteneur pour plus de détails...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.containers = {c['name']: c for c in containers}

    async def callback(self, interaction: discord.Interaction):
        container = self.containers[self.values[0]]
        if container['status'] == 'running':
            couleur = discord.Color.green()
            status_symbol = "🟩"
        else:
            couleur = discord.Color.red()
            status_symbol = "🟥"

        embed = discord.Embed(
            color=couleur
        )

        width = 41
        label_width = 12
        content_width = width - label_width - 3

        top_line    = "┌" + "─" * (width - 2) + "┐"
        name_line   = f" {status_symbol} {pad_right(container['name'], width - 8)}{status_symbol}"
        middle_line = f"├{'─' * (label_width)}┬{'─' * (content_width)}┤"
        status_line = f"│ {pad_right('Status', label_width - 1)}│ {pad_right(container['status'], content_width - 1)}│"
        bottom_line = f"└{'─' * (label_width)}┴{'─' * (content_width)}┘"
        
        container_info = f"""```
{top_line}
{name_line}
{middle_line}
{status_line}
{bottom_line}```"""
        
        embed.add_field(
            name="\u200b",
            value=container_info,
            inline=False
        )
        
        view = ContainerActions(container['name'], container['status'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ContainerListView(discord.ui.View):
    def __init__(self, containers):
        super().__init__(timeout=300)
        self.add_item(ContainerSelect(containers))

@bot.tree.command(name="status", description="Affiche l'état de tous les conteneurs")
async def status(interaction: discord.Interaction):

    is_mobile = interaction.user.is_on_mobile()
    
    if is_mobile:
        await interaction.response.send_message(
            f"Pour consulter l'état des containers sur mobile veuillez vous rendre au lien suivant : {logs_url}",
            ephemeral=True
        )
        return

    data = load_data()
    embed = discord.Embed(
        title="État des conteneurs",
        color=discord.Color.blurple()
    )
    
    for container in data:

        width = 41
        label_width = 12
        content_width = width - label_width - 3
        
        status_symbol = "🟩" if container['status'] == 'running' else "🟥"


        top_line    = "┌" + "─" * (width - 2) + "┐"
        name_line   = f" {status_symbol} {pad_right(container['name'], width - 8)}{status_symbol}"
        middle_line = f"├{'─' * (label_width)}┬{'─' * (content_width)}┤"
        status_line = f"│ {pad_right('Status', label_width - 1)}│ {pad_right(container['status'], content_width - 1)}│"
        bottom_line = f"└{'─' * (label_width)}┴{'─' * (content_width)}┘"
        
        container_info = f"""```
{top_line}
{name_line}
{middle_line}
{status_line}
{bottom_line}```"""
        
        embed.add_field(
            name="\u200b",
            value=container_info,
            inline=False
        )
    
    if not data:
        embed.description = "Aucun conteneur trouvé"
    
    view = ContainerListView(data)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="aide", description="Affiche l'aide du bot")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        description="Voici les commandes disponibles :",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="/status",
        value="Affiche l'état de tous les conteneurs et permet de les gérer",
        inline=False
    )

    embed.add_field(
        name="/aide",
        value="Affiche ce message d'aide",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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