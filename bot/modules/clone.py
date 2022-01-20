import random
import string

from telegram.ext import CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, deleteMessage, delete_all_messages, update_all_messages, sendStatusMessage, sendLog, sendPrivate
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.clone_status import CloneStatus
from bot import dispatcher, LOGGER, CLONE_LIMIT, STOP_DUPLICATE, download_dict, download_dict_lock, Interval
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_gdrive_link, is_gdtot_link, new_thread
from bot.helper.mirror_utils.download_utils.direct_link_generator import gdtot
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException

@new_thread
def cloneNode(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    if len(args) > 1:
        link = args[1]
        if update.message.from_user.username:
            tag = f"@{update.message.from_user.username}"
        else:
            tag = update.message.from_user.mention_html(update.message.from_user.first_name)
    elif reply_to is not None:
        link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    else:
        link = ''
    gdtot_link = is_gdtot_link(link)
    if gdtot_link:
        try:
            msg = sendMessage(f"💤𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗶𝗻𝗴 𝘁𝗼 𝗚𝗗𝗧𝗼𝗧: <code>{link}</code>", context.bot, update)
            link = gdtot(link)
            deleteMessage(context.bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(context.bot, msg)
            return sendMessage(str(e), context.bot, update)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if res != "":
            return sendMessage(res, context.bot, update)
        if STOP_DUPLICATE:
            LOGGER.info('Checking File/Folder if already in Drive...')
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                sendMarkup(msg3, context.bot, update, button)
                if gdtot_link:
                    gd.deletefile(link)
                return
        if CLONE_LIMIT is not None:
            LOGGER.info('Checking File/Folder Size...')
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f'Failed, Clone limit is {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}.'
                return sendMessage(msg2, context.bot, update)
        if files <= 10:
            msg = sendMessage(f"♻️𝗖𝗹𝗼𝗻𝗶𝗻𝗴: <code>{link}</code>", context.bot, update)
            result, button = gd.clone(link)
            deleteMessage(context.bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=12))
            clone_status = CloneStatus(drive, size, update, gid)
            with download_dict_lock:
                download_dict[update.message.message_id] = clone_status
            sendStatusMessage(update, context.bot)
            result, button = drive.clone(link)
            with download_dict_lock:
                del download_dict[update.message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝗬: {uname}'
            men = f'{uname}'
            msg_g = f'\n\n - 𝙽𝚎𝚟𝚎𝚛 𝚂𝚑𝚊𝚛𝚎 𝙸𝚗𝚍𝚎𝚡 𝙻𝚒𝚗𝚔'
            fwdpm = f'\n\n<b>ʏᴏᴜ ᴄᴀɴ ꜰɪɴᴅ ᴜᴘʟᴏᴀᴅ ɪɴ ʙᴏᴛ ᴘᴍ ᴏʀ ᴄʟɪᴄᴋ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ꜱᴇᴇ ᴀᴛ ʟᴏɢ ᴄʜᴀɴɴᴇʟ</b>'
        if button == "cancelled" or button == "":
            sendMessage(men + result, context.bot, update)
        else:
            logmsg = sendLog(result + cc + msg_g, context.bot, update, button)
            if logmsg:
                log_m = f"\n\n𝗟𝗶𝗻𝗸 𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗱, 𝗖𝗹𝗶𝗰𝗸 𝗕𝗲𝗹𝗼𝘄 𝗕𝘂𝘁𝘁𝗼𝗻👇"
                sendMarkup(result + cc + fwdpm, context.bot, update, InlineKeyboardMarkup([[InlineKeyboardButton(text="𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘", url=logmsg.link)]]))
                sendPrivate(result + cc + msg_g, context.bot, update, button)
        if gdtot_link:
            gd.deletefile(link)
    else:
        sendMessage('𝗦𝗲𝗻𝗱 𝗚𝗱𝗿𝗶𝘃𝗲 𝗼𝗿 𝗚𝗗𝗧𝗼𝗧 𝗹𝗶𝗻𝗸 𝗮𝗹𝗼𝗻𝗴 𝘄𝗶𝘁𝗵 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗼𝗿 𝗯𝘆 𝗿𝗲𝗽𝗹𝘆𝗶𝗻𝗴 𝘁𝗼 𝘁𝗵𝗲 𝗹𝗶𝗻𝗸 𝗯𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱', context.bot, update)

clone_handler = CommandHandler(BotCommands.CloneCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
gdtot_handler = CommandHandler(BotCommands.GDToTCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(clone_handler)
dispatcher.add_handler(gdtot_handler)
