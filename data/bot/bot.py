import os
import json
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
from discord import app_commands
from discord.ui import Button, View
from datetime import datetime
from dateutil import parser
import time


load_dotenv()
TOKEN = os.getenv('DOCKERCONTAINERMANAGER_DISCORD_TOKEN')
DEBUG = os.getenv('DOCKERCONTAINERMANAGER_DEBUG')
BACKEND_URL = os.getenv('DOCKERCONTAINERMANAGER_BACKEND_URL', 'http://backend:5000')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
LOGS_URL = os.getenv('DOCKERCONTAINERMANAGER_FRONT_URL')

global_cooldowns = {}

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

def format_uptime(started_at, status):
    if status != 'running':
        return "Stopped"
    
    if not started_at:
        return "N/A"
        
    try:
        start_time = parser.parse(started_at)
        if not start_time.tzinfo:
            start_time = start_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
            
        current_time = datetime.now().astimezone()
        diff = current_time - start_time
        
        total_seconds = int(diff.total_seconds())
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}j")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)
        
    except Exception as e:
        return "N/A"

class ContainerActions(View):
    def __init__(self, container_name, container_status):
        super().__init__(timeout=300)
        self.container_name = container_name
        self.container_status = container_status
        self.last_command_time = {}

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

    async def check_cooldown(self, interaction: discord.Interaction) -> bool:
        current_time = time.time()
        user_id = interaction.user.id
        
        if user_id in global_cooldowns:
            if current_time - global_cooldowns[user_id] < 10:
                await interaction.response.send_message(
                    "Veuillez attendre 10 secondes avant d'utiliser à nouveau cette commande.",
                    ephemeral=True
                )
                return False
        
        if user_id in self.last_command_time:
            if current_time - self.last_command_time[user_id] < 10:
                await interaction.response.send_message(
                    "Veuillez attendre 10 secondes avant d'utiliser à nouveau cette commande.",
                    ephemeral=True
                )
                return False
        
        self.last_command_time[user_id] = current_time
        global_cooldowns[user_id] = current_time
        return True

    async def restart_button_callback(self, interaction: discord.Interaction):
        if not await self.check_cooldown(interaction):
            return
            
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                embed = discord.Embed(
                    title=f"{self.container_name}",
                    description="✅ Redémarré avec succès",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/restart")
                    response.raise_for_status()
                    
                    public_embed = discord.Embed(
                        title="Action sur un conteneur",
                        description=f"🔄 Le conteneur **{self.container_name}** a été redémarré par {interaction.user.mention}",
                        color=discord.Color.green()
                    )
                    public_embed.set_footer(text="via Discord")
                    await interaction.channel.send(embed=public_embed, delete_after=86400)
                except requests.RequestException as e:
                    pass
                return
                
        await interaction.response.send_message(
            f"Conteneur {self.container_name} non trouvé.", 
            ephemeral=True
        )

    async def stop_button_callback(self, interaction: discord.Interaction):
        if not await self.check_cooldown(interaction):
            return
            
        data = load_data()
        for container in data:
            if container['name'] == self.container_name:
                embed = discord.Embed(
                    title=f"{self.container_name}",
                    description="✅ Arrêté avec succès",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
                try:
                    container_id = container['id']
                    response = requests.post(f"{BACKEND_URL}/api/container/{container_id}/stop")
                    response.raise_for_status()
                    
                    public_embed = discord.Embed(
                        title="Action sur un conteneur",
                        description=f"🟥 Le conteneur **{self.container_name}** a été arrêté par {interaction.user.mention}",
                        color=discord.Color.red()
                    )
                    public_embed.set_footer(text="via Discord")
                    await interaction.channel.send(embed=public_embed, delete_after=86400)
                except requests.RequestException as e:
                    pass
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
                    f"Logs : {self.container_name}\n```\n{logs}```\n[Voir plus de logs →]({LOGS_URL})",
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

        self.disabled = True
        
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
        
        status_symbol = "🟩" if container['status'] == 'running' else "🟥"

        top_line    = "┌" + "─" * (width - 2) + "┐"
        name_line   = f" {status_symbol} {pad_right(container['name'], width - 8)}{status_symbol}"
        middle_line = f"├{'─' * (label_width)}┬{'─' * (content_width)}┤"
        middle_line_in = f"├{'─' * (label_width)}┼{'─' * (content_width)}┤"
        status_line = f"│ {pad_right('Status', label_width - 1)}│ {pad_right(container['status'], content_width - 1)}│"
        uptime_line = f"│ {pad_right('Uptime', label_width - 1)}│ {pad_right(format_uptime(container['started_at'], container['status']), content_width - 1)}│"
        bottom_line = f"└{'─' * (label_width)}┴{'─' * (content_width)}┘"
        
        container_info = f"""```
{top_line}
{name_line}
{middle_line}
{status_line}
{middle_line_in}
{uptime_line}
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
        self.select = ContainerSelect(containers)
        self.add_item(self.select)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

@bot.tree.command(name="status", description="Affiche l'état de tous les conteneurs")
async def status(interaction: discord.Interaction):
    current_time = time.time()
    user_id = interaction.user.id
    
    if user_id in global_cooldowns:
        if current_time - global_cooldowns[user_id] < 10:
            await interaction.response.send_message(
                "Veuillez attendre 10 secondes avant d'utiliser à nouveau cette commande.",
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
        middle_line_in = f"├{'─' * (label_width)}┼{'─' * (content_width)}┤"
        status_line = f"│ {pad_right('Status', label_width - 1)}│ {pad_right(container['status'], content_width - 1)}│"
        uptime_line = f"│ {pad_right('Uptime', label_width - 1)}│ {pad_right(format_uptime(container['started_at'], container['status']), content_width - 1)}│"
        bottom_line = f"└{'─' * (label_width)}┴{'─' * (content_width)}┘"
        
        container_info = f"""```
{top_line}
{name_line}
{middle_line}
{status_line}
{middle_line_in}
{uptime_line}
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

@status.error
async def status_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Veuillez attendre {error.retry_after:.1f} secondes avant d'utiliser à nouveau cette commande.",
            ephemeral=True
        )

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