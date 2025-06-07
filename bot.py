import os
import uuid
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import FSInputFile
from aiogram.enums import ContentType
from aiogram.filters import VIDEO

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()


def split_video_ffmpeg(input_path, output_folder, ig_handle="@your_ig", clip_duration=60):
    os.makedirs(output_folder, exist_ok=True)
    output_pattern = os.path.join(output_folder, "part_%03d.mp4")
    
    command = [
        "ffmpeg",
        "-i", input_path,
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(clip_duration),
        "-f", "segment",
        "-reset_timestamps", "1",
        output_pattern
    ]
    subprocess.run(command, check=True)
    
    return sorted([
        os.path.join(output_folder, f)
        for f in os.listdir(output_folder)
        if f.endswith(".mp4")
    ])


@router.message(VIDEO)
async def handle_video(message: types.Message):
    await message.answer("📥 Downloading your video...")

    file_id = str(uuid.uuid4())
    file = await bot.get_file(message.video.file_id)
    input_path = f"temp/{file_id}.mp4"
    os.makedirs("temp", exist_ok=True)
    await bot.download_file(file.file_path, input_path)

    await message.answer("✂️ Splitting your video into parts...")

    output_folder = f"temp/output_{file_id}"
    output_files = split_video_ffmpeg(input_path, output_folder, ig_handle="@piyush_bhawsar")

    for path in output_files:
        await message.answer_video(FSInputFile(path))

    await message.answer("✅ Done! All parts sent.")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
