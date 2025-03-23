from speedtest import Speedtest, ConfigRetrievalError

from .. import LOGGER
from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    delete_message,
)
from ..helper.ext_utils.bot_utils import new_task, sync_to_async
from ..helper.ext_utils.status_utils import get_readable_file_size


@new_task
async def speedtest(_, message):
    speed = await send_message(message, "<i>Initiating Speedtest...</i>")
    try:
        speed_results = await sync_to_async(Speedtest)
        await sync_to_async(speed_results.get_best_server)
        await sync_to_async(speed_results.download)
        await sync_to_async(speed_results.upload)
    except ConfigRetrievalError:
        await edit_message(
            speed,
            "<b>ERROR:</b> <i>Can't connect to Server at the Moment, Try Again Later !</i>",
        )
        return
    speed_results.results.share()
    result = speed_results.results.dict()
    string_speed = f"""
➲ <pre><b><i>SPEEDTEST INFO</i></b></pre>
┠ <pre><b>Upload:</b></pre> <code>{get_readable_file_size(result['upload'] / 8)}/s</code>
┠ <pre><b>Download:</b></pre>  <code>{get_readable_file_size(result['download'] / 8)}/s</code>
┠ <pre><b>Ping:</b></pre> <code>{result['ping']} ms</code>
┠ <pre><b>Time:</b></pre> <code>{result['timestamp']}</code>
┠ <pre><b>Data Sent:</b></pre> <code>{get_readable_file_size(int(result['bytes_sent']))}</code>
┖ <pre><b>Data Received:</b></pre> <code>{get_readable_file_size(int(result['bytes_received']))}</code>

➲ <pre><b><i>SPEEDTEST SERVER</i></b></pre>
┠ <pre><b>Name:</b></pre> <code>{result['server']['name']}</code>
┠ <pre><b>Country:</b></pre> <code>{result['server']['country']}, {result['server']['cc']}</code>
┠ <pre><b>Sponsor:</b></pre> <code>{result['server']['sponsor']}</code>
┠ <pre><b>Latency:</b></pre> <code>{result['server']['latency']}</code>
┠ <pre><b>Latitude:</b></pre> <code>{result['server']['lat']}</code>
┖ <pre><b>Longitude:</b></pre> <code>{result['server']['lon']}</code>
"""
    try:
        await send_message(message, string_speed, photo=result["share"])
        await delete_message(speed)
    except Exception as e:
        LOGGER.error(str(e))
        await edit_message(speed, string_speed)
