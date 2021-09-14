import os
import re
import asyncio
import subprocess
from pytgcalls import idle
from pytgcalls import PyTgCalls
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioParameters
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputVideoStream
from pytgcalls.types.input_stream import VideoParameters
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, SESSION_NAME
from youtube_dl import YoutubeDL

app = Client(SESSION_NAME, API_ID, API_HASH)
call_py = PyTgCalls(app)
FFMPEG_PROCESSES = {}
def raw_converter(dl, song, video):
    subprocess.Popen(
        ['ffmpeg', '-i', dl, '-f', 's16le', '-ac', '1', '-ar', '48000', song, '-y', '-f', 'rawvideo', '-r', '20', '-pix_fmt', 'yuv420p', '-vf', 'scale=640:360', video, '-y'],
        stdin=None,
        stdout=None,
        stderr=None,
        cwd=None,
    )
opts = {"format": "best[height=?480]/best", "noplaylist": True}
ydl = YoutubeDL(opts)

@Client.on_message(filters.private & filters.command(["cstream"]))
async def chstream(client, m: Message):
    replied = m.reply_to_message
    if not replied:
        if len(m.command) < 2:
            await m.reply("`Reply to some Video File or YT Link!`")
        else:
            livelink = m.text.split(None, 1)[1]
            process = raw_converter(livelink, f'audio{chat_id}.raw', f'video{chat_id}.raw')
            FFMPEG_PROCESSES[chat_id] = process
            msg = await m.reply("`Starting Video Stream...`")
            await asyncio.sleep(10)
            try:
                audio_file = f'audio{chat_id}.raw'
                video_file = f'video{chat_id}.raw'
                while not os.path.exists(audio_file) or \
                        not os.path.exists(video_file):
                    await asyncio.sleep(2)
                await call_py.join_group_call(
                    chat_id,
                    InputAudioStream(
                        audio_file,
                        AudioParameters(
                            bitrate=48000,
                        ),
                    ),
                    InputVideoStream(
                        video_file,
                        VideoParameters(
                            width=1280,
                            height=720,
                            frame_rate=20,
                        ),
                    ),
                    stream_type=StreamType().local_stream,
                )
                await msg.edit("**Started Channel Stream!**")
                await idle()
            except Exception as e:
                await msg.edit(f"**Error** -- `{e}`")
   
    elif replied.video or replied.document:
        msg = await m.reply("`Downloading...`")
        video = await client.download_media(m.reply_to_message)
        chat_id = CHANNEL
        await msg.edit("`Processing...`")
        os.system(f"ffmpeg -i '{video}' -f s16le -ac 1 -ar 48000 'audio{chat_id}.raw' -y -f rawvideo -r 20 -pix_fmt yuv420p -vf scale=640:360 'video{chat_id}.raw' -y")
        try:
            audio_file = f'audio{chat_id}.raw'
            video_file = f'video{chat_id}.raw'
            while not os.path.exists(audio_file) or \
                    not os.path.exists(video_file):
                await asyncio.sleep(2)
            await call_py.join_group_call(
                chat_id,
                InputAudioStream(
                    audio_file,
                    AudioParameters(
                        bitrate=48000,
                    ),
                ),
                InputVideoStream(
                    video_file,
                    VideoParameters(
                        width=640,
                        height=360,
                        frame_rate=20,
                    ),
                ),
                stream_type=StreamType().local_stream,
            )
            await msg.edit("**Started Channel Stream!**")
        except Exception as e:
            await msg.edit(f"**Error** -- `{e}`")
            await idle()
    else:
        await m.reply("`Reply to some Video!`")

@Client.on_message(filters.private & filters.command(["cstop"]))
async def chstopvideo(client, m: Message):
    try:
        process = FFMPEG_PROCESSES.get(chat_id)
        if process:
            try:
                process.send_signal(SIGINT)
                await asyncio.sleep(3)
            except Exception as e:
                print(e)
        await call_py.leave_group_call(chat_id)
        await m.reply("**⏹️ Stop Channel Stream!**")
    except Exception as e:
        await m.reply(f"**🚫 Error** - `{e}`")