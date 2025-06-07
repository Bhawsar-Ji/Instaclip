import os
import uuid
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import FSInputFile

# Load bot token from environment variable
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Create temp folders
os.makedirs("temp", exist_ok=True)

def split_and_compress(input_path, output_folder, ig_handle="@your_ig", clip_duration=60):
    os.makedirs(output_folder, exist_ok=True)
    output_template = os.path.join(output_folder, "part_%03d.mp4")

    # Step 1: Split video without re-encoding
    split_command = [
        "ffmpeg",
        "-i", input_path,
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(clip_duration),
        "-f", "segment",
        "-reset_timestamps", "1",
        output_template
    ]
    subprocess.run(split_command, check=True)

    # Step 2: Compress each part
    compressed_files = []
    for file in sorted(os.listdir(output_folder)):
        if not file.endswith(".mp4"):
            continue
        input_part = os.path.join(output_folder, file)
        output_part = os.path.join(output_folder, "compressed_" + file)

        compress_command = [
            "ffmpeg",
            "-i", input_part,
            "-vf", "scale=720:1280",
            "-b:v", "800k",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_part
        ]
        subprocess.run(compress_command, check=True)
        compressed_files.append(output_part)

    return compressed_files

@router.message(lambda message: message.video is not None)
async def handle_video(message: types.Message):
    await message.answer("📥 Downloading your video...")

    file_id = str(uuid.uuid4())
    file = await bot.get_file(message.video.file_id)
    input_path = f"temp/{file_id}.mp4"
    await bot.download_file(file.file_path, input_path)

    await message.answer("✂️ Splitting & compressing video...")

    output_folder = f"temp/output_{file_id}"
    output_files = split_and_compress(input_path, output_folder)

    for idx, path in enumerate(output_files, start=1):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > 50:
            await message.answer(f"⚠️ Skipping Part {idx} — too big ({int(size_mb)}MB)")
            continue
        await message.answer_video(FSInputFile(path), caption=f"Part {idx}")

    await message.answer("✅ All parts sent!")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
            
