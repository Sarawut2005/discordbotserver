import os
from keep_alive import keep_Alive
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio

from google.oauth2 import service_account
from googleapiclient.discovery import build


# --- ตั้งค่าตัวแปร ---
ALLOWED_CHANNEL_ID = 1394713573065752848  # ใส่ ID ช่องที่อนุญาตให้ใช้คำสั่ง
FOLDER_ID = "1wJ6d1_TES5PDWnZ3y-c6j2nLNehAVjeM"  # ใส่ ID โฟลเดอร์ Google Drive ที่เก็บไฟล์
SERVICE_ACCOUNT_FILE = 'sincere-lexicon-466015-b5-61b989c8596b.json'  # ไฟล์ Service Account JSON ของ Google

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Google Drive API Setup ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

async def get_file_link(filename):
    """ค้นหาไฟล์ใน Google Drive โฟลเดอร์ที่กำหนด และคืนลิงก์แชร์"""
    query = f"name = '{filename}' and '{FOLDER_ID}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        return None
    file_id = files[0]['id']
    link = f"https://drive.google.com/file/d/{file_id}/view"
    return link

# --- Bot Events ---

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    keep_alive.start()

@tasks.loop(minutes=10)
async def keep_alive():
    print("Bot is still alive...")

# --- Slash Command ---

@bot.tree.command(name="ส่งไฟล์", description="ส่งหมายศาลจาก Google Drive ทาง DM")
@app_commands.describe(member="ผู้รับ", filename="ชื่อไฟล์ PDF ใน Google Drive (ต้องระบุ .pdf)")
async def ส่งไฟล์(interaction: discord.Interaction, member: discord.Member, filename: str):
    # เช็คช่องที่อนุญาตใช้คำสั่ง
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในช่องที่กำหนดเท่านั้น", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    link = await get_file_link(filename)
    if not link:
        await interaction.followup.send(f"❌ ไม่พบไฟล์ `{filename}` ใน Google Drive", ephemeral=True)
        return

    try:
        await member.send(f"📜 คุณได้รับหมายศาลจากศาลยุติธรรม\n🔗 ลิงก์ไฟล์: {link}")
        await interaction.followup.send(f"✅ ส่งลิงก์ไฟล์ `{filename}` ให้ {member.mention} เรียบร้อยแล้ว", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(f"❌ ไม่สามารถส่ง DM ให้ {member.mention} ได้ (อาจปิด DM)", ephemeral=True)

# --- Sync Slash Commands on startup ---

@bot.event
async def on_connect():
    try:
        await bot.tree.sync()
        print("Synced slash commands globally")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

keep_Alive()

token = os.environ['TOKEN']
bot.run(token)