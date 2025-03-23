from asyncio import gather
from platform import platform, version
from re import search as research
from time import time

from aiofiles.os import path as aiopath
from psutil import (
    Process,
    boot_time,
    cpu_count,
    cpu_freq,
    cpu_percent,
    disk_io_counters,
    disk_usage,
    getloadavg,
    net_io_counters,
    swap_memory,
    virtual_memory,
)

from .. import bot_cache, bot_start_time
from ..core.config_manager import Config, BinConfig
from ..helper.ext_utils.bot_utils import cmd_exec, compare_versions, new_task
from ..helper.ext_utils.status_utils import (
    get_progress_bar_string,
    get_readable_file_size,
    get_readable_time,
)
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_message,
)
from ..version import get_version

commands = {
    "aria2": ([BinConfig.ARIA2_NAME, "--version"], r"aria2 version ([\d.]+)"),
    "qBittorrent": ([BinConfig.QBIT_NAME, "--version"], r"qBittorrent v([\d.]+)"),
    "SABnzbd+": ([BinConfig.SABNZBD_NAME, "--version"], rf"{BinConfig.SABNZBD_NAME}-([\d.]+)"),
    "python": (["python3", "--version"], r"Python ([\d.]+)"),
    "rclone": ([BinConfig.RCLONE_NAME, "--version"], r"rclone v([\d.]+)"),
    "yt-dlp": (["yt-dlp", "--version"], r"([\d.]+)"),
    "ffmpeg": ([BinConfig.FFMPEG_NAME, "-version"], r"ffmpeg version ([\d.]+(-\w+)?).*"),
    "7z": (["7z", "i"], r"7-Zip ([\d.]+)"),
    "aiohttp": (["uv", "pip", "show", "aiohttp"], r"Version: ([\d.]+)"),
    "pyrofork": (["uv", "pip", "show", "pyrofork"], r"Version: ([\d.]+)"),
    "gapi": (["uv", "pip", "show", "google-api-python-client"], r"Version: ([\d.]+)"),
    "mega": (["pip", "show", "megasdk"], r"Version: ([\d.]+)"),
}


async def get_stats(event, key="home"):
    user_id = event.from_user.id
    btns = ButtonMaker()
    btns.data_button("Back", f"stats {user_id} home")
    if key == "home":
        btns = ButtonMaker()
        btns.data_button("Bot Stats", f"stats {user_id} stbot")
        btns.data_button("OS Stats", f"stats {user_id} stsys")
        btns.data_button("Repo Stats", f"stats {user_id} strepo")
        btns.data_button("Pkgs Stats", f"stats {user_id} stpkgs")
        btns.data_button("Bot Task Limits", f"stats {user_id} tlimits")
        msg = "⌬ <pre><b><i>Max Bot & OS Statistics!</i></b></pre>"
    elif key == "stbot":
        total, used, free, disk = disk_usage("/")
        swap = swap_memory()
        memory = virtual_memory()
        disk_io = disk_io_counters()
        msg = f"""⌬ <pre><b><i>BOT STATISTICS :</i></b></pre>
┖ <pre><b>Bot Uptime :</b></pre> {get_readable_time(time() - bot_start_time)}

┎ <pre><b><i>RAM ( MEMORY ) :</i></b></pre>
┃ {get_progress_bar_string(memory.percent)} {memory.percent}%
┖ <pre><b>U :</b></pre> {get_readable_file_size(memory.used)} | <pre><b>F :</b></pre> {get_readable_file_size(memory.available)} | <pre><b>T :</b></pre> {get_readable_file_size(memory.total)}

┎ <pre><b><i>SWAP MEMORY :</i></b></pre>
┃ {get_progress_bar_string(swap.percent)} {swap.percent}%
┖ <pre><b>U :</b></pre> {get_readable_file_size(swap.used)} | <pre><b>F :</b></pre> {get_readable_file_size(swap.free)} | <pre><b>T :</b></pre> {get_readable_file_size(swap.total)}

┎ <pre><b><i>DISK :</i></b></pre>
┃ {get_progress_bar_string(disk)} {disk}%
┃ <pre><b>Total Disk Read :</b></pre> {f"{get_readable_file_size(disk_io.read_bytes)} ({get_readable_time(disk_io.read_time / 1000)})" if disk_io else "Access Denied"}
┃ <pre><b>Total Disk Write :</b></pre> {f"{get_readable_file_size(disk_io.write_bytes)} ({get_readable_time(disk_io.write_time / 1000)})" if disk_io else "Access Denied"}
┖ <pre><b>U :</b></pre> {get_readable_file_size(used)} | <pre><b>F :</b></pre> {get_readable_file_size(free)} | <pre><b>T :</b></pre> {get_readable_file_size(total)}
"""
    elif key == "stsys":
        cpu_usage = cpu_percent(interval=0.5)
        msg = f"""⌬ <pre><b><i>OS SYSTEM :</i></b></pre>
┟ <pre><b>OS Uptime :</b></pre> {get_readable_time(time() - boot_time())}
┠ <pre><b>OS Version :</b></pre> {version()}
┖ <pre><b>OS Arch :</b></pre> {platform()}

⌬ <pre><b><i>NETWORK STATS :</i></b></pre>
┟ <pre><b>Upload Data:</b></pre> {get_readable_file_size(net_io_counters().bytes_sent)}
┠ <pre><b>Download Data:</b></pre> {get_readable_file_size(net_io_counters().bytes_recv)}
┠ <pre><b>Pkts Sent:</b></pre> {str(net_io_counters().packets_sent)[:-3]}k
┠ <pre><b>Pkts Received:</b></pre> {str(net_io_counters().packets_recv)[:-3]}k
┖ <pre><b>Total I/O Data:</b></pre> {get_readable_file_size(net_io_counters().bytes_recv + net_io_counters().bytes_sent)}

┎ <pre><b>CPU :</b></pre>
┃ {get_progress_bar_string(cpu_usage)} {cpu_usage}%
┠ <pre><b>CPU Frequency :</b></pre> {f"{cpu_freq().current / 1000:.2f} GHz" if cpu_freq() else "Access Denied"}
┠ <pre><b>System Avg Load :</b></pre> {"%, ".join(str(round((x / cpu_count() * 100), 2)) for x in getloadavg())}%, (1m, 5m, 15m)
┠ <pre><b>P-Core(s) :</b></pre> {cpu_count(logical=False)} | <b>V-Core(s) :</b> {cpu_count(logical=True) - cpu_count(logical=False)}
┠ <pre><b>Total Core(s) :</b></pre> {cpu_count(logical=True)}
┖ <pre><b>Usable CPU(s) :</b></pre> {len(Process().cpu_affinity())}
"""
    elif key == "strepo":
        last_commit, changelog = "No Data", "N/A"
        if await aiopath.exists(".git"):
            last_commit = (
                await cmd_exec(
                    "git log -1 --pretty='%cd ( %cr )' --date=format-local:'%d/%m/%Y'",
                    True,
                )
            )[0]
            changelog = (
                await cmd_exec(
                    "git log -1 --pretty=format:'<code>%s</code> <b>By</b> %an'", True
                )
            )[0]
        official_v = (
            await cmd_exec(
                f"curl -o latestversion.py https://raw.githubusercontent.com/SilentDemonSD/WZML-X/{Config.UPSTREAM_BRANCH}/bot/version.py -s && python3 latestversion.py && rm latestversion.py",
                True,
            )
        )[0]
        msg = f"""⌬ <pre><b><i>Repo Statistics :</i></b></pre>
│
┟ <pre><b>Bot Updated :</b></pre> {last_commit}
┠ <pre><b>Current Version :</b></pre> {get_version()}
┠ <pre><b>Latest Version :</b></pre> {official_v}
┖ <pre><b>Last ChangeLog :</b></pre> {changelog}

⌬ <pre><b>REMARKS :</b></pre> <code>{compare_versions(get_version(), official_v)}</code>
    """
    elif key == "stpkgs":
        msg = f"""⌬ <pre><b><i>Packages Statistics :</i></b></pre>
│
┟ <pre><b>python:</b></pre> {bot_cache["eng_versions"]["python"]}
┠ <pre><b>aria2:</b></pre> {bot_cache["eng_versions"]["aria2"]}
┠ <pre><b>qBittorrent:</b></pre> {bot_cache["eng_versions"]["qBittorrent"]}
┠ <pre><b>SABnzbd+:</b></pre> {bot_cache["eng_versions"]["SABnzbd+"]}
┠ <pre><b>rclone:</b></pre> {bot_cache["eng_versions"]["rclone"]}
┠ <pre><b>yt-dlp:</b></pre> {bot_cache["eng_versions"]["yt-dlp"]}
┠ <pre><b>ffmpeg:</b></pre> {bot_cache["eng_versions"]["ffmpeg"]}
┠ <pre><b>7z:</b></pre> {bot_cache["eng_versions"]["7z"]}
┠ <pre><b>Aiohttp:</b></pre> {bot_cache["eng_versions"]["aiohttp"]}
┠ <pre><b>Pyrofork:</b></pre> {bot_cache["eng_versions"]["pyrofork"]}
┠ <pre><b>Google API:</b></pre> {bot_cache["eng_versions"]["gapi"]}
┖ <pre><b>Mega SDK:</b></pre> {bot_cache["eng_versions"]["mega"]}
"""
    elif key == "tlimits":
        msg = f"""⌬ <pre><b><i>Bot Task Limits :</i></b></pre>
│
┟ <pre><b>Direct Limit :</b></pre> {Config.DIRECT_LIMIT or "∞"} GB
┠ <pre><b>Torrent Limit :</b></pre> {Config.TORRENT_LIMIT or "∞"} GB
┠ <pre><b>GDriveDL Limit :</b></pre> {Config.GD_DL_LIMIT or "∞"} GB
┠ <pre><b>RCloneDL Limit :</b></pre> {Config.RC_DL_LIMIT or "∞"} GB
┠ <pre><b>Clone Limit :</b></pre> {Config.CLONE_LIMIT or "∞"} GB
┠ <pre><b>JDown Limit :</b></pre> {Config.JD_LIMIT or "∞"} GB
┠ <pre><b>NZB Limit :</b></pre> {Config.NZB_LIMIT or "∞"} GB
┠ <pre><b>YT-DLP Limit :</b></pre> {Config.YTDLP_LIMIT or "∞"} GB
┠ <pre><b>Playlist Limit :</b></pre> {Config.PLAYLIST_LIMIT or "∞"}
┠ <pre><b>Mega Limit :</b></pre> {Config.MEGA_LIMIT or "∞"} GB
┠ <pre><b>Leech Limit :</b></pre> {Config.LEECH_LIMIT or "∞"} GB
┠ <pre><b>Archive Limit :</b></pre> {Config.ARCHIVE_LIMIT or "∞"} GB
┠ <pre><b>Extract Limit :</b></pre> {Config.EXTRACT_LIMIT or "∞"} GB
┞ <pre><b>Threshold Storage :</b></pre> {Config.STORAGE_LIMIT or "∞"} GB
│
┟ <pre><b>Token Validity :</b></pre> {Config.VERIFY_TIMEOUT or "Disabled"}
┠ <pre><b>User Time Limit :</b></pre> {Config.USER_TIME_INTERVAL or "0"}s / task
┠ <pre><b>User Max Tasks :</b></pre> {Config.USER_MAX_TASKS or "∞"}
┖ <pre><b>Bot Max Tasks :</b></pre> {Config.BOT_MAX_TASKS or "∞"}
    """

    btns.data_button("Close", f"stats {user_id} close", "footer")
    return msg, btns.build_menu(2)


@new_task
async def bot_stats(_, message):
    msg, btns = await get_stats(message)
    await send_message(message, msg, btns)


@new_task
async def stats_pages(_, query):
    data = query.data.split()
    message = query.message
    user_id = query.from_user.id
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2] == "close":
        await query.answer()
        await delete_message(message, message.reply_to_message)
    else:
        await query.answer()
        msg, btns = await get_stats(query, data[2])
        await edit_message(message, msg, btns)


async def get_version_async(command, regex):
    try:
        out, err, code = await cmd_exec(command)
        if code != 0:
            return f"Error: {err}"
        match = research(regex, out)
        return match.group(1) if match else "-"
    except Exception as e:
        return f"Exception: {str(e)}"


@new_task
async def get_packages_version():
    tasks = [get_version_async(command, regex) for command, regex in commands.values()]
    versions = await gather(*tasks)
    bot_cache["eng_versions"] = {}
    for tool, ver in zip(commands.keys(), versions):
        bot_cache["eng_versions"][tool] = ver
    if await aiopath.exists(".git"):
        last_commit = await cmd_exec(
            "git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'", True
        )
        last_commit = last_commit[0]
    else:
        last_commit = "No UPSTREAM_REPO"
    bot_cache["commit"] = last_commit
