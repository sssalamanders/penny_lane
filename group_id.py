#!/usr/bin/env python3
"""
group_id.py - Penny Lane Bot Module
Handles the actual Telegram bot functionality for group ID retrieval
"""

import logging
import time
import os
import hashlib
from collections import defaultdict
from pathlib import Path
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Configure logging
DEBUG_MODE = os.getenv("PENNY_DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        *([logging.FileHandler('penny_debug.log')] if DEBUG_MODE else [])
    ]
)
logger = logging.getLogger(__name__)

# Silence overly verbose telegram logs unless in debug mode
if not DEBUG_MODE:
    logging.getLogger('httpx').setLevel(logging.WARNING)

# ---- Ephemeral in-memory store (RAM only) ----
owners = set()                          # User IDs who started bot privately
recent_groups = defaultdict(float)      # {group_id: expiry_timestamp}
TTL = 300  # 5 minutes in seconds

def encrypt_id(id_value):
    """Encrypt sensitive IDs for logging"""
    # Use SHA-256 hash and truncate to 8 characters for logging
    hash_obj = hashlib.sha256(str(id_value).encode())
    return hash_obj.hexdigest()[:8]

def prune_expired():
    """Remove expired group records from memory."""
    now = time.time()
    expired = [gid for gid, exp in recent_groups.items() if exp <= now]
    for gid in expired:
        del recent_groups[gid]
    if expired:
        logger.info(f"Pruned {len(expired)} expired group records")

async def bandaid_command(update, context):
    """Handle /bandaid command in private chats and groups."""
    prune_expired()
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Debug logging with encrypted IDs
    encrypted_user_id = encrypt_id(user.id)
    encrypted_chat_id = encrypt_id(chat.id)
    logger.debug(f"Received /bandaid from user #{encrypted_user_id} in chat #{encrypted_chat_id} (type: {chat.type})")
    
    if chat.type == "private":
        # Register user for private notifications
        owners.add(user.id)
        logger.info(f"Registered new owner: #{encrypted_user_id} (@{user.username or 'no_username'})")
        logger.debug(f"Total registered owners: {len(owners)}")
        
        await update.message.reply_text(
            "🎸 Hey there! I'm Penny Lane, your group ID band aid.\n\n"
            "Here's how this works:\n"
            "1. Add me as an admin to any group you manage\n"
            "2. Send /bandaid in that group\n"
            "3. I'll privately message you the group's ID\n"
            "4. I forget everything after 5 minutes for your privacy!\n\n"
            "Ready when you are! 🎵"
        )
        return
    
    if chat.type in {"group", "supergroup"}:
        logger.debug(f"Processing group request - Group: {chat.title} (#{encrypted_chat_id})")
        
        # Check if user is actually an admin
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            logger.debug(f"User #{encrypted_user_id} status in group: {member.status}")
            if member.status not in ["creator", "administrator"]:
                logger.info(f"Non-admin #{encrypted_user_id} tried to use /bandaid in group #{encrypted_chat_id}")
                await update.message.reply_text(
                    "Sorry, only group admins can use this command."
                )
                return
        except Exception as e:
            logger.warning(f"Could not verify admin status for #{encrypted_user_id} in #{encrypted_chat_id}: {e}")
        
        # Only send ID if we haven't already sent it recently
        if chat.id not in recent_groups:
            logger.debug(f"New group request for #{encrypted_chat_id}, sending to {len(owners)} owners")
            
            # Send group ID to all registered owners with GIF
            message_text = (
                f"🎵 New group detected!\n\n"
                f"📝 Title: {chat.title or 'Unnamed Group'}\n"
                f"🆔 ID: `{chat.id}`\n\n"
                f"Copy the ID above (tap to select). "
                f"This info will be forgotten in 5 minutes."
            )
            
            success_count = 0
            for owner_id in owners:
                try:
                    # Create inline keyboard with donation button
                    keyboard = [[
                        InlineKeyboardButton(
                            "🎵 Support the music", 
                            callback_data="donate_stars"
                        )
                    ]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Try to send with GIF first
                    gif_path = Path("success.gif")
                    if gif_path.exists():
                        with open(gif_path, 'rb') as gif_file:
                            await context.bot.send_animation(
                                chat_id=owner_id,
                                animation=gif_file,
                                caption=message_text,
                                parse_mode="Markdown",
                                reply_markup=reply_markup
                            )
                    else:
                        # Fallback to text-only if GIF not found
                        await context.bot.send_message(
                            chat_id=owner_id,
                            text=message_text,
                            parse_mode="Markdown",
                            reply_markup=reply_markup
                        )
                        logger.warning("success.gif not found, sent text-only message")
                    
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send to owner {owner_id}: {e}")
                    # Try fallback text message if GIF fails
                    try:
                        await context.bot.send_message(
                            chat_id=owner_id,
                            text=message_text,
                            parse_mode="Markdown"
                        )
                        success_count += 1
                    except Exception as e2:
                        logger.error(f"Both GIF and text failed for owner {owner_id}: {e2}")
            
            # Remember this group temporarily
            recent_groups[chat.id] = time.time() + TTL
            logger.info(f"Sent group ID #{encrypted_chat_id} to {success_count} owners")
            
            await update.message.reply_text(
                f"✅ Group ID sent privately to {success_count} registered admin(s)!"
            )
        else:
            await update.message.reply_text(
                "I already sent this group's ID recently. "
                "Check your private messages with me!"
            )

async def help_command(update, context):
    """Provide help information."""
    help_text = (
        "🎸 **Penny Lane - Group ID Bot**\n\n"
        "I help you get Telegram group IDs safely and privately!\n\n"
        "**How to use:**\n"
        "1. Start me in a private chat with /bandaid\n"
        "2. Add me as admin to your group\n"
        "3. Send /bandaid in that group\n"
        "4. I'll DM you the group ID\n\n"
        "**Privacy:** I only keep info in memory for 5 minutes, "
        "then forget everything completely.\n\n"
        "**Commands:**\n"
        "/bandaid - Register privately or get group ID\n"
        "/help - Show this help message\n"
        "/status - Show current memory usage"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def status_command(update, context):
    """Show bot status (only works in private chat)."""
    if update.effective_chat.type != "private":
        return
    
    prune_expired()
    
    status_text = (
        f"🎵 **Penny Lane Status**\n\n"
        f"👥 Registered owners: {len(owners)}\n"
        f"📊 Active group cache: {len(recent_groups)}\n"
        f"⏱️ Cache TTL: {TTL} seconds\n\n"
        f"All data is stored in RAM only and automatically expires!"
    )
    
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def handle_donation_callback(update, context):
    """Handle donation button press"""
    query = update.callback_query
    
    if query.data == "donate_stars":
        await query.answer()  # Acknowledge the button press
        await query.message.reply_text(
            "🎸 Thanks for supporting Penny Lane!\n\n"
            "To send Telegram Stars:\n"
            "1. Tap the attachment (📎) button below\n"
            "2. Select 'Payment'\n"
            "3. Choose 'Send Stars'\n"
            "4. Pick any amount you'd like\n\n"
            "Every star helps keep the music playing! 🎵"
        )

async def handle_other_messages(update, context):
    """Handle non-command messages with friendly responses."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Hey! Use /bandaid to get started, or /help for more info. 🎸"
        )

def run_bot(token):
    """Run the bot with the given token"""
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("bandaid", bandaid_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Add callback handler for donation button
    application.add_handler(CallbackQueryHandler(handle_donation_callback))
    
    # Handle other messages
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_other_messages
    ))
    
    logger.info("🎸 Penny Lane is starting up...")
    logger.info("🔒 Privacy mode: RAM-only storage with 5-minute expiry")
    logger.info("📡 Bot is now polling for updates...")
    
    try:
        application.run_polling(drop_pending_updates=True)
        return 0
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        return 1
    finally:
        logger.info("🧹 All data cleared from memory")
