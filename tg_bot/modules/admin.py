from telegram import Update, ChatAdministratorRights, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
)
from telegram.helpers import mention_html, escape_markdown

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    bot = context.bot

    user_id = context.args[0] if context.args else None
    if not user_id or not user_id.isdigit():
        await message.reply_text("Please provide a valid user ID.")
        return

    user_id = int(user_id)
    bot_member = await chat.get_member(bot.id)
    user_member = await chat.get_member(user_id)

    if user_member.status in ['administrator', 'creator']:
        await message.reply_text("The user is already an admin.")
        return

    if user_id == bot.id:
        await message.reply_text("I can't promote myself!")
        return

    rights = ChatAdministratorRights(
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
        can_promote_members=bot_member.can_promote_members,
    )

    await bot.promote_chat_member(chat.id, user_id, rights)
    await message.reply_text("Successfully promoted!")

async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    bot = context.bot

    user_id = context.args[0] if context.args else None
    if not user_id or not user_id.isdigit():
        await message.reply_text("Please provide a valid user ID.")
        return

    user_id = int(user_id)
    user_member = await chat.get_member(user_id)

    if user_member.status == 'creator':
        await message.reply_text("Cannot demote the creator of the chat.")
        return

    if user_member.status != 'administrator':
        await message.reply_text("The user is not an admin.")
        return

    rights = ChatAdministratorRights(
        can_change_info=False,
        can_post_messages=False,
        can_edit_messages=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_pin_messages=False,
        can_promote_members=False,
    )

    await bot.promote_chat_member(chat.id, user_id, rights)
    await message.reply_text("Successfully demoted!")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    bot = context.bot

    is_silent = 'notify' not in context.args and 'loud' not in context.args
    if message.reply_to_message:
        try:
            await bot.pin_chat_message(chat.id, message.reply_to_message.message_id, disable_notification=is_silent)
            await message.reply_text("Message pinned successfully.")
        except BadRequest as e:
            await message.reply_text(f"Failed to pin message: {e}")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    try:
        await chat.unpin_message()
        await update.message.reply_text("Message unpinned successfully.")
    except BadRequest as e:
        await update.message.reply_text(f"Failed to unpin message: {e}")

async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admins = await update.effective_chat.get_administrators()
    admin_list = "\n".join(
        [f"- {mention_html(admin.user.id, admin.user.first_name)}" for admin in admins]
    )
    await update.message.reply_text(f"Admins in this chat:\n{admin_list}", parse_mode=ParseMode.HTML)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.username:
        await update.message.reply_text(f"https://t.me/{chat.username}")
    else:
        bot_member = await chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            link = await context.bot.export_chat_invite_link(chat.id)
            await update.message.reply_text(link)
        else:
            await update.message.reply_text("I don't have permission to generate an invite link.")

def main() -> None:
    application = Application.builder().token("YOUR_TOKEN").build()

    application.add_handler(CommandHandler("promote", promote, filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("demote", demote, filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("pin", pin, filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("unpin", unpin, filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("adminlist", adminlist, filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("invitelink", invite, filters.ChatType.GROUPS))

    application.run_polling()
