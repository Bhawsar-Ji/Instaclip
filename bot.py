import os
import uuid
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ContentType
from aiogram.types import FSInputFile
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def split_resize_watermark(input_path, output_folder, ig_handle="@your_ig", clip_duration=60):
    os.makedirs(output_folder, exist_ok=True)
    video = VideoFileClip(input_path)
    total_duration = int(video.duration)
    num_parts = (total_duration + clip_duration - 1) // clip_duration
    output_files = []

    for i in range(num_parts):
        start_time = i * clip_duration
        end_time = min(start_time + clip_duration, total_duration)
        subclip = video.subclip(start_time, end_time)
        resized_clip = subclip.resize(height=1920 * 0.8)
        bg_clip = subclip.resize((1080, 1920)).fx(vfx.blur, 25).set_opacity(0.3)
        centered_clip = resized_clip.set_position(("center", "center"))

        part_text = f"Part {i + 1}"
        txt_part = TextClip(part_text, fontsize=70, color='white', font='Arial-Bold')
        txt_part = txt_part.set_duration(subclip.duration).set_position(("center", "top")).margin(top=30)

        txt_watermark = TextClip(ig_handle, fontsize=40, color='white', font='Arial-Bold').set_opacity(0.5)
        txt_watermark = txt_watermark.set_duration(subclip.duration).set_position(("center", "bottom")).margin(bottom=30)

        final = CompositeVideoClip([bg_clip, centered_clip, txt_part, txt_watermark], size=(1080, 1920))
        output_path = os.path.join(output_folder, f"part_{i + 1}.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        output_files.append(output_path)

    return output_files

@dp.message(content_types=ContentType.VIDEO)
async def handle_video(message: types.Message, bot: Bot):
    await message.answer("📥 Downloading your video...")

    file_id = str(uuid.uuid4())
    file = await bot.get_file(message.video.file_id)
    input_path = f"temp/{file_id}.mp4"
    os.makedirs("temp", exist_ok=True)
    await bot.download_file(file.file_path, input_path)

    await message.answer("✂️ Cutting into Reels with watermark...")

    output_folder = f"temp/output_{file_id}"
    output_files = split_resize_watermark(input_path, output_folder, ig_handle="@piyush_bhawsar")

    for path in output_files:
        await message.answer_video(FSInputFile(path))

    await message.answer("✅ Done! All parts sent.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
