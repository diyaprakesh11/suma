
import logging

from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, ChatAdminRequired
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton

from bot import TELEGRAM_API, TELEGRAM_HASH, CHANNEL_USERNAME, BOT_TOKEN

msp = Client(
   "ForceSub Bot",
   api_id=TELEGRAM_API,
   api_hash=TELEGRAM_HASH,
   bot_token=BOT_TOKEN,
)

# get mute request
static_data_filter = filters.create(lambda _, __, query: query.data == "onUnmute")

@msp.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
  user_id = cb.from_user.id
  chat_id = cb.message.chat.id
  chat_u = CHANNEL_USERNAME #channel for force sub
  if chat_u:
    channel = chat_u
    chat_member = client.get_chat_member(chat_id, user_id)
    if chat_member.restricted_by:
      if chat_member.restricted_by.id == (client.get_me()).id:
          try:
            client.get_chat_member(channel, user_id)
            client.unban_chat_member(chat_id, user_id)
            if cb.message.reply_to_message.from_user.id == user_id:
              cb.message.delete()
          except UserNotParticipant:
            client.answer_callback_query(cb.id, text=f"❗ Join the {chat_u} and press the 'Unmute Me' button again.", show_alert=True)
      else:
        client.answer_callback_query(cb.id, text="❗ You are muted by admins for other reasons.", show_alert=True)
    else:
      if not client.get_chat_member(chat_id, (client.get_me()).id).status == 'administrator':
        client.send_message(chat_id, f"❗ **{cb.from_user.mention} is trying to Unmute himself but I can't unmute him because I am not an admin in this chat.")
      else:
        client.answer_callback_query(cb.id, text="❗ Warning: Don't click the button if you can speak freely.", show_alert=True)

@msp.on_message(filters.text & ~filters.private & ~filters.edited, group=1)
def _check_member(client, message):
  chat_id = message.chat.id
  chat_u = CHANNEL_USERNAME #channel for force sub
  if chat_u:
    user_id = message.from_user.id
    if not client.get_chat_member(chat_id, user_id).status in ("administrator", "creator"):
      channel = chat_u
      try:
        client.get_chat_member(channel, user_id)
      except UserNotParticipant:
         try:
              chat_u = chat_u.replace('@','')
              tauk = message.from_user.mention
              sent_message = message.reply_text(
                 "{} , you are not subscribed to my channel yet. Please join using below button and press the UnMute Me button to unmute yourself.".format(message.from_user.mention, channel, channel),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                  [[InlineKeyboardButton(f"Join {chat_u} Channel", url=f"https://t.me/{chat_u}")],
                  [InlineKeyboardButton("Unmute Me", callback_data="onUnmute")]]))
              client.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))

         except ChatAdminRequired:
            sent_message.edit("❗ **I am not an admin here.**\n__Make me admin with ban user permission__")

      except ChatAdminRequired:
         client.send_message(chat_id, text=f"❗ **I am not an admin in {chat_u}**\n__Make me admin in the channel__")

msp.run()
