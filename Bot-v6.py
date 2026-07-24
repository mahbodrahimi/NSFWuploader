import telebot
from telebot import types
import json
import os
import time
import threading
from datetime import datetime, timedelta
import requests
import re

# ==================== CONFIGURATION ====================
TOKEN = "8949661112:AAEF7edIbhHkGWi3MgLy0O4DJVIrE8YfiRw"
ADMIN_IDS = [6378393027, 5713289649]
BOT_USERNAME = "Cuteiii_bot"
ADMIN_PASSWORD = "admin"  # قابل تنظیم - پسورد برای حذف آمار و ویدیوها

bot = telebot.TeleBot(TOKEN)

# ==================== حذف webhook قبل از شروع polling ====================
try:
    bot.remove_webhook()
    print("✅ Webhook removed successfully")
except Exception as e:
    print(f"⚠️ Error removing webhook: {e}")

# ==================== FILE PATHS ====================
VIDEOS_FILE = "videos.json"
SPONSORS_FILE = "sponsors.json"
USERS_FILE = "users.json"
STATS_FILE = "stats.json"

# ==================== STATE MANAGEMENT ====================
active_operations = {}
cancelled_operations = set()
input_messages = {}  # Track input messages for editing

# ==================== GLASS BUTTON STYLE ====================
def create_glass_button(text, callback_data):
    return types.InlineKeyboardButton(f"✨ {text} ✨", callback_data=callback_data)

def create_glass_button_url(text, url):
    return types.InlineKeyboardButton(f"🔗 {text}", url=url)

# ==================== DATA MANAGEMENT ====================
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        if filename == USERS_FILE:
            return {"users": [], "total_views": 0}
        elif filename == STATS_FILE:
            return {}
        return {} if filename == USERS_FILE else []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==================== USER TRACKING ====================
def track_user(user_id):
    users_data = load_json(USERS_FILE)
    if user_id not in users_data.get("users", []):
        if "users" not in users_data:
            users_data["users"] = []
        users_data["users"].append(user_id)
        save_json(USERS_FILE, users_data)

def increment_view_count(video_id):
    users_data = load_json(USERS_FILE)
    users_data["total_views"] = users_data.get("total_views", 0) + 1
    save_json(USERS_FILE, users_data)
    
    stats = load_json(STATS_FILE)
    if video_id not in stats:
        stats[video_id] = {"downloads": 0, "added_date": datetime.now().isoformat()}
    stats[video_id]["downloads"] = stats[video_id].get("downloads", 0) + 1
    save_json(STATS_FILE, stats)

# ==================== VIDEO MANAGEMENT ====================
def add_video(name, file_ids, sponsors, delete_time, has_spoiler=False):
    """Add a video/photo with multiple file_ids (multiple media for one share link)"""
    videos = load_json(VIDEOS_FILE)
    video_id = str(int(time.time()))
    video_data = {
        "id": video_id,
        "name": name,
        "file_ids": file_ids if isinstance(file_ids, list) else [file_ids],
        "sponsors": sponsors,
        "delete_time": delete_time,
        "has_spoiler": has_spoiler,
        "added_date": datetime.now().isoformat(),
        "current_index": 0
    }
    videos.append(video_data)
    save_json(VIDEOS_FILE, videos)
    
    # Initialize stats for this video
    stats = load_json(STATS_FILE)
    if video_id not in stats:
        stats[video_id] = {"downloads": 0, "added_date": video_data["added_date"]}
        save_json(STATS_FILE, stats)
    
    return video_id

def get_video(video_id):
    videos = load_json(VIDEOS_FILE)
    for video in videos:
        if video["id"] == video_id:
            if "file_id" in video and "file_ids" not in video:
                video["file_ids"] = [video["file_id"]]
                del video["file_id"]
            if "current_index" not in video:
                video["current_index"] = 0
            if "has_spoiler" not in video:
                video["has_spoiler"] = False
            return video
    return None

def update_video(video_id, updates):
    videos = load_json(VIDEOS_FILE)
    for i, video in enumerate(videos):
        if video["id"] == video_id:
            videos[i].update(updates)
            save_json(VIDEOS_FILE, videos)
            return True
    return False

def delete_video(video_id):
    videos = load_json(VIDEOS_FILE)
    videos = [v for v in videos if v["id"] != video_id]
    save_json(VIDEOS_FILE, videos)

def delete_all_videos():
    """Delete all videos and clear stats"""
    save_json(VIDEOS_FILE, [])
    save_json(STATS_FILE, {})

def clear_all_stats():
    """Clear all statistics"""
    save_json(USERS_FILE, {"users": [], "total_views": 0})
    save_json(STATS_FILE, {})

# ==================== SPONSOR MANAGEMENT ====================
def add_sponsor(video_id, channel_id, channel_name):
    video = get_video(video_id)
    if video:
        video["sponsors"].append({
            "channel_id": channel_id,
            "channel_name": channel_name
        })
        update_video(video_id, {"sponsors": video["sponsors"]})

# ==================== MEMBERSHIP CHECK ====================
def check_membership(user_id, channel_id):
    try:
        if channel_id.startswith('@'):
            channel_id = channel_id[1:]
        
        if channel_id.lstrip('-').isdigit():
            chat_id = int(channel_id)
        else:
            chat_id = f"@{channel_id}"
            
        member = bot.get_chat_member(chat_id, user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def get_missing_sponsors(user_id, video_id):
    video = get_video(video_id)
    if not video:
        return []
    
    missing = []
    for sponsor in video["sponsors"]:
        if not check_membership(user_id, sponsor["channel_id"]):
            missing.append(sponsor)
    
    return missing

# ==================== KEYBOARD GENERATORS ====================
def generate_main_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        create_glass_button("➕ افزودن ویدیو جدید", "admin_add_video"),
        create_glass_button("📋 لیست ویدیوها", "admin_list_videos"),
        create_glass_button("📊 آمار", "admin_stats")
    )
    return keyboard

def generate_video_list_keyboard(page=0, per_page=5):
    videos = load_json(VIDEOS_FILE)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    start = page * per_page
    end = start + per_page
    page_videos = videos[start:end]
    total_pages = (len(videos) + per_page - 1) // per_page
    
    for video in page_videos:
        display_text = f"🎬 {video['name']}"
        keyboard.add(
            create_glass_button(display_text, f"video_detail_{video['id']}")
        )
    
    nav_buttons = []
    if total_pages > 1:
        if page > 0:
            nav_buttons.append(create_glass_button("◀️ صفحه قبل", f"video_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(create_glass_button("صفحه بعد ▶️", f"video_page_{page+1}"))
    
    if nav_buttons:
        if len(nav_buttons) == 2:
            keyboard.row(nav_buttons[0], nav_buttons[1])
        else:
            keyboard.add(nav_buttons[0])
    
    if total_pages > 1:
        keyboard.add(create_glass_button(f"📄 صفحه {page + 1} از {total_pages}", "no_action"))
    
    keyboard.add(create_glass_button("🗑️ حذف همه ویدیوها", "confirm_delete_all_videos"))
    keyboard.add(create_glass_button("🔙 بازگشت", "admin_back"))
    return keyboard

def generate_video_detail_keyboard(video_id):
    video = get_video(video_id)
    spoiler_status = "✅" if video and video.get("has_spoiler", False) else "❌"
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        create_glass_button("👥 مدیریت اسپانسرها", f"manage_sponsors_{video_id}"),
        create_glass_button("⏱️ تنظیم زمان حذف", f"set_delete_time_{video_id}"),
        create_glass_button(f"🔰 اسپویلر: {spoiler_status}", f"toggle_spoiler_{video_id}"),
        create_glass_button("📊 اطلاعات ویدیو", f"video_info_{video_id}"),
        create_glass_button("🔗 دریافت لینک اشتراک", f"get_share_link_{video_id}"),
        create_glass_button("🗑️ حذف ویدیو", f"confirm_delete_{video_id}"),
        create_glass_button("🔙 بازگشت به لیست", "admin_list_videos")
    )
    return keyboard

def generate_spoiler_question_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✅ بله", callback_data="spoiler_yes"),
        types.InlineKeyboardButton("❌ خیر", callback_data="spoiler_no")
    )
    return keyboard

def generate_video_info_keyboard(video_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        create_glass_button("🔙 بازگشت به جزئیات", f"video_detail_{video_id}")
    )
    return keyboard

def generate_stats_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        create_glass_button("🗑️ پاک کردن آمار", "confirm_clear_stats"),
        create_glass_button("🔙 بازگشت", "admin_back")
    )
    return keyboard

def generate_sponsor_check_keyboard(video_id, user_id):
    missing_sponsors = get_missing_sponsors(user_id, video_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    if not missing_sponsors:
        keyboard.add(create_glass_button("✅ تایید عضویت", f"verify_membership_{video_id}"))
    else:
        for sponsor in missing_sponsors:
            if sponsor["channel_id"].startswith('@'):
                url = f"https://t.me/{sponsor['channel_id'][1:]}"
            elif sponsor["channel_id"].lstrip('-').isdigit():
                url = f"https://t.me/c/{sponsor['channel_id'].lstrip('-')}"
            else:
                url = f"https://t.me/{sponsor['channel_id']}"
            
            keyboard.add(
                create_glass_button_url(f"📢 {sponsor['channel_name']}", url)
            )
        
        keyboard.add(create_glass_button("🔄 بررسی عضویت", f"check_sponsors_{video_id}"))
    
    return keyboard

def generate_back_keyboard(callback_data):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(create_glass_button("🔙 بازگشت", callback_data))
    return keyboard

def generate_cancel_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(create_glass_button("❌ کنسل", "cancel_password"))
    return keyboard

# ==================== PASSWORD HANDLING ====================
password_states = {}

def request_password(chat_id, action_type):
    """Request password from admin"""
    password_states[chat_id] = {
        "action": action_type,
        "timestamp": time.time()
    }
    msg = bot.send_message(
        chat_id,
        "🔐 **لطفاً پسورد ادمین را وارد کنید:**",
        reply_markup=generate_cancel_keyboard(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, verify_password)

def verify_password(message):
    """Verify the entered password"""
    chat_id = message.chat.id
    
    if chat_id not in password_states:
        return
    
    if time.time() - password_states[chat_id]["timestamp"] > 300:
        del password_states[chat_id]
        bot.send_message(chat_id, "❌ زمان درخواست منقضی شده است. لطفاً دوباره تلاش کنید.")
        return
    
    if message.text and message.text.strip() == ADMIN_PASSWORD:
        action = password_states[chat_id]["action"]
        del password_states[chat_id]
        
        if action == "clear_stats":
            execute_clear_stats(chat_id)
        elif action == "delete_all_videos":
            execute_delete_all_videos(chat_id)
    else:
        bot.send_message(
            chat_id,
            "❌ **پسورد اشتباه است!**\n\n"
            "لطفاً دوباره تلاش کنید یا دکمه کنسل را بزنید.",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(message, verify_password)

def execute_clear_stats(chat_id):
    clear_all_stats()
    bot.send_message(
        chat_id,
        "✅ **تمام آمار با موفقیت پاک شد!**",
        reply_markup=generate_main_admin_keyboard(),
        parse_mode='Markdown'
    )

def execute_delete_all_videos(chat_id):
    delete_all_videos()
    bot.send_message(
        chat_id,
        "✅ **تمام ویدیوها با موفقیت حذف شدند!**",
        reply_markup=generate_main_admin_keyboard(),
        parse_mode='Markdown'
    )

# ==================== WELCOME MESSAGE ====================
WELCOME_TEXT = """
🌟 **پنل مدیریت بات**

به پنل مدیریت خوش آمدید!
از دکمه‌های زیر برای مدیریت ویدیوها و اسپانسرها استفاده کنید.

🔹 **افزودن ویدیو جدید:** اضافه کردن ویدیو با لینک دانلود
🔹 **لیست ویدیوها:** مشاهده و مدیریت ویدیوهای موجود
🔹 **آمار:** مشاهده آمار بات و ویدیوها
"""

# ==================== MESSAGE HANDLERS ====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    track_user(user_id)
    
    if len(args) > 1 and args[1].startswith('video_'):
        video_id = args[1].replace('video_', '')
        video = get_video(video_id)
        
        if not video:
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "❌ این ویدیو وجود ندارد!")
                return
            else:
                bot.reply_to(message, "❌ ویدیوی مورد نظر وجود ندارد")
                return
        
        if user_id not in ADMIN_IDS:
            missing_sponsors = get_missing_sponsors(user_id, video_id)
            
            if missing_sponsors:
                sponsor_text = "🔐 **برای دریافت ویدیو باید در کانال/گروه‌های زیر عضو باشید:**\n\n"
                for i, sponsor in enumerate(missing_sponsors, 1):
                    sponsor_text += f"**اسپانسر {i}:** {sponsor['channel_name']}\n"
                
                bot.reply_to(
                    message,
                    sponsor_text,
                    reply_markup=generate_sponsor_check_keyboard(video_id, user_id),
                    parse_mode='Markdown'
                )
            else:
                send_video_to_user(message.chat.id, video, user_id)
        else:
            send_video_to_user(message.chat.id, video, user_id)
        return
    
    if user_id in ADMIN_IDS and len(args) == 1:
        bot.send_message(
            message.chat.id,
            WELCOME_TEXT,
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
        return
    elif user_id not in ADMIN_IDS and len(args) == 1:
        return

@bot.message_handler(
    func=lambda message: message.chat.type == 'private' and message.from_user.id in ADMIN_IDS,
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note']
)
def handle_admin_messages(message):
    chat_id = message.chat.id
    
    # اگر ربات منتظر پسورد است، دست به این پیام نزن
    if chat_id in password_states:
        return
    
    # اگر یک عملیات فعال (مثل افزودن ویدیو/اسپانسر/زمان حذف) در حال انجام است
    # منتظر ورودی مربوط به همان عملیات بمان و پنل را باز نکن
    if chat_id in active_operations:
        return
    
    # دستور /start توسط هندلر مخصوص خودش پردازش می‌شود
    if message.text and message.text.strip() == '/start':
        return
    
    # در غیر این صورت ربات منتظر هیچ ورودی خاصی نیست، پس هر پیامی که بیاید پنل را باز کن
    bot.send_message(
        chat_id,
        WELCOME_TEXT,
        reply_markup=generate_main_admin_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "no_action":
        bot.answer_callback_query(call.id)
        return
    
    if data == "cancel_password":
        if chat_id in password_states:
            del password_states[chat_id]
        
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except:
            pass
        
        cancelled_operations.add(chat_id)
        if chat_id in active_operations:
            del active_operations[chat_id]
        if chat_id in input_messages:
            del input_messages[chat_id]
        
        try:
            bot.edit_message_text(
                WELCOME_TEXT,
                chat_id,
                call.message.message_id,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        except:
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(
                chat_id,
                WELCOME_TEXT,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        return
    
    if data == "cancel_operation" or data == "admin_back":
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except:
            pass
        
        if chat_id in password_states:
            del password_states[chat_id]
        
        cancelled_operations.add(chat_id)
        if chat_id in active_operations:
            del active_operations[chat_id]
        if chat_id in input_messages:
            del input_messages[chat_id]
        
        try:
            bot.edit_message_text(
                WELCOME_TEXT,
                chat_id,
                call.message.message_id,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        except:
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(
                chat_id,
                WELCOME_TEXT,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        return
    
    if data == "spoiler_yes":
        if chat_id in active_operations and isinstance(active_operations[chat_id], dict) and "spoiler_pending" in active_operations[chat_id]:
            pending_data = active_operations[chat_id]["spoiler_pending"]
            active_operations[chat_id]["has_spoiler"] = True
            
            # Edit the same message instead of sending new one
            bot.edit_message_text(
                f"✅ **اسپویلر فعال شد**\n\n"
                f"👥 **مرحله 4/5: حالا اسپانسرها را وارد کنید:**\n\n"
                "فرمت: `channel_id1/channel_name1, channel_id2/channel_name2`\n"
                "مثال: `@testchannel/کانال تست, -1001234567890/گروه تست`\n\n"
                "اگر اسپانسر نمی‌خواهید، کلمه `no` را بفرستید.",
                chat_id,
                call.message.message_id,
                reply_markup=generate_back_keyboard("admin_back"),
                parse_mode='Markdown'
            )
            input_messages[chat_id] = call.message.message_id
            bot.register_next_step_handler(call.message, process_sponsors, pending_data["video_name"], pending_data["file_ids"], True)
        else:
            bot.answer_callback_query(call.id, "❌ این عملیات دیگر معتبر نیست، لطفاً دوباره شروع کنید.", show_alert=True)
        return
    
    elif data == "spoiler_no":
        if chat_id in active_operations and isinstance(active_operations[chat_id], dict) and "spoiler_pending" in active_operations[chat_id]:
            pending_data = active_operations[chat_id]["spoiler_pending"]
            active_operations[chat_id]["has_spoiler"] = False
            
            bot.edit_message_text(
                f"✅ **بدون اسپویلر**\n\n"
                f"👥 **مرحله 4/5: حالا اسپانسرها را وارد کنید:**\n\n"
                "فرمت: `channel_id1/channel_name1, channel_id2/channel_name2`\n"
                "مثال: `@testchannel/کانال تست, -1001234567890/گروه تست`\n\n"
                "اگر اسپانسر نمی‌خواهید، کلمه `no` را بفرستید.",
                chat_id,
                call.message.message_id,
                reply_markup=generate_back_keyboard("admin_back"),
                parse_mode='Markdown'
            )
            input_messages[chat_id] = call.message.message_id
            bot.register_next_step_handler(call.message, process_sponsors, pending_data["video_name"], pending_data["file_ids"], False)
        else:
            bot.answer_callback_query(call.id, "❌ این عملیات دیگر معتبر نیست، لطفاً دوباره شروع کنید.", show_alert=True)
        return
    
    elif data.startswith("toggle_spoiler_"):
        video_id = data.replace("toggle_spoiler_", "")
        video = get_video(video_id)
        if video:
            new_spoiler = not video.get("has_spoiler", False)
            update_video(video_id, {"has_spoiler": new_spoiler})
            status = "✅ فعال" if new_spoiler else "❌ غیرفعال"
            bot.answer_callback_query(call.id, f"اسپویلر {status} شد!")
            show_video_detail(chat_id, call.message.message_id, video_id)
        return
    
    if data.startswith('admin_') or data.startswith('video_') or data.startswith('manage_') or data.startswith('set_delete_') or data.startswith('confirm_delete_') or data.startswith('get_share_') or data.startswith('video_info_') or data.startswith('confirm_clear_stats') or data.startswith('confirm_delete_all'):
        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!")
            return
    
    if data == "admin_add_video":
        active_operations[chat_id] = "adding_video"
        cancelled_operations.discard(chat_id)
        
        msg = bot.send_message(
            chat_id,
            "📝 **مرحله 1/5: لطفاً نام ویدیو را وارد کنید:**\n(این نام در لیست ویدیوها نمایش داده می‌شود)",
            reply_markup=generate_back_keyboard("admin_back"),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_video_name)
    
    elif data == "admin_list_videos":
        videos = load_json(VIDEOS_FILE)
        if not videos:
            bot.edit_message_text(
                "📋 **هیچ ویدیویی ثبت نشده است!**\n\nبرای افزودن ویدیو جدید از دکمه زیر استفاده کنید.",
                chat_id,
                call.message.message_id,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        else:
            total_pages = (len(videos) + 4) // 5
            bot.edit_message_text(
                f"📋 **لیست ویدیوها ({len(videos)} عدد):**\n\nبرای مدیریت هر ویدیو روی آن کلیک کنید.\n📄 صفحه 1 از {total_pages}",
                chat_id,
                call.message.message_id,
                reply_markup=generate_video_list_keyboard(page=0),
                parse_mode='Markdown'
            )
    
    elif data == "admin_stats":
        show_stats(chat_id, call.message.message_id)
    
    elif data == "confirm_clear_stats":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            create_glass_button("✅ بله، پاک کن", "request_clear_stats_password"),
            create_glass_button("❌ خیر", "admin_stats")
        )
        bot.edit_message_text(
            "⚠️ **آیا از پاک کردن تمام آمار اطمینان دارید؟**\n\n"
            "این عمل قابل بازگشت نیست!\n"
            "تمام آمار کاربران و دانلودها پاک خواهد شد.",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data == "request_clear_stats_password":
        bot.delete_message(chat_id, call.message.message_id)
        request_password(chat_id, "clear_stats")
    
    elif data == "confirm_delete_all_videos":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            create_glass_button("✅ بله، حذف کن", "request_delete_all_password"),
            create_glass_button("❌ خیر", "admin_list_videos")
        )
        bot.edit_message_text(
            "⚠️ **آیا از حذف تمام ویدیوها اطمینان دارید؟**\n\n"
            "این عمل قابل بازگشت نیست!\n"
            "تمام ویدیوها و اطلاعات آن‌ها حذف خواهد شد.",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data == "request_delete_all_password":
        bot.delete_message(chat_id, call.message.message_id)
        request_password(chat_id, "delete_all_videos")
    
    elif data.startswith("video_page_"):
        page = int(data.split("_")[2])
        videos = load_json(VIDEOS_FILE)
        total_pages = (len(videos) + 4) // 5
        bot.edit_message_text(
            f"📋 **لیست ویدیوها ({len(videos)} عدد):**\n\nبرای مدیریت هر ویدیو روی آن کلیک کنید.\n📄 صفحه {page + 1} از {total_pages}",
            chat_id,
            call.message.message_id,
            reply_markup=generate_video_list_keyboard(page),
            parse_mode='Markdown'
        )
    
    elif data.startswith("video_detail_"):
        video_id = data.replace("video_detail_", "")
        show_video_detail(chat_id, call.message.message_id, video_id)
    
    elif data.startswith("video_info_"):
        video_id = data.replace("video_info_", "")
        show_video_info(chat_id, call.message.message_id, video_id)
    
    elif data.startswith("manage_sponsors_"):
        video_id = data.replace("manage_sponsors_", "")
        video = get_video(video_id)
        current_sponsors = "\n".join([f"• {s['channel_name']} - `{s['channel_id']}`" for s in video['sponsors']]) if video['sponsors'] else "هیچ اسپانسری ثبت نشده"
        
        active_operations[chat_id] = "managing_sponsors"
        cancelled_operations.discard(chat_id)
        
        # Edit the existing message instead of sending new one
        bot.edit_message_text(
            f"👥 **مدیریت اسپانسرها**\n\n"
            f"**اسپانسرهای فعلی:**\n{current_sponsors}\n\n"
            "برای افزودن اسپانسر(ها)، به این فرمت وارد کنید:\n"
            "`channel_id1/channel_name1, channel_id2/channel_name2`\n\n"
            "مثال: `@testchannel/کانال تست, -1001234567890/گروه تست`\n\n"
            "از / برای جدا کردن آیدی و نام استفاده کنید\n"
            "از , برای جدا کردن اسپانسرهای مختلف استفاده کنید",
            chat_id,
            call.message.message_id,
            reply_markup=generate_back_keyboard(f"video_detail_{video_id}"),
            parse_mode='Markdown'
        )
        input_messages[chat_id] = call.message.message_id
        bot.register_next_step_handler(call.message, process_add_sponsor, video_id)
    
    elif data.startswith("set_delete_time_"):
        video_id = data.replace("set_delete_time_", "")
        active_operations[chat_id] = "setting_delete_time"
        cancelled_operations.discard(chat_id)
        
        # Edit the existing message instead of sending new one
        bot.edit_message_text(
            "⏱️ **لطفاً زمان حذف خودکار را به ثانیه وارد کنید:**\n"
            "مثال: 300 برای 5 دقیقه",
            chat_id,
            call.message.message_id,
            reply_markup=generate_back_keyboard(f"video_detail_{video_id}"),
            parse_mode='Markdown'
        )
        input_messages[chat_id] = call.message.message_id
        bot.register_next_step_handler(call.message, process_delete_time, video_id)
    
    elif data.startswith("confirm_delete_"):
        video_id = data.replace("confirm_delete_", "")
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            create_glass_button("✅ بله", f"delete_video_{video_id}"),
            create_glass_button("❌ خیر", f"video_detail_{video_id}")
        )
        bot.edit_message_text(
            "⚠️ **آیا از حذف این ویدیو اطمینان دارید؟**",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data.startswith("delete_video_"):
        video_id = data.replace("delete_video_", "")
        delete_video(video_id)
        bot.edit_message_text(
            "✅ **ویدیو با موفقیت حذف شد!**",
            chat_id,
            call.message.message_id,
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data.startswith("get_share_link_"):
        video_id = data.replace("get_share_link_", "")
        share_link = f"https://t.me/{BOT_USERNAME}?start=video_{video_id}"
        bot.answer_callback_query(call.id, "✅ لینک کپی شد!")
        bot.send_message(
            chat_id,
            f"🔗 **لینک اشتراک ویدیو:**\n`{share_link}`",
            parse_mode='Markdown'
        )
    
    # User Callbacks
    elif data.startswith("check_sponsors_"):
        video_id = data.replace("check_sponsors_", "")
        
        video = get_video(video_id)
        if not video:
            bot.answer_callback_query(call.id, "❌ این ویدیو وجود ندارد!", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
            return
        
        missing_sponsors = get_missing_sponsors(user_id, video_id)
        
        if not missing_sponsors:
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            send_video_to_user(chat_id, video, user_id)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نیستید!", show_alert=True)
            try:
                sponsor_text = "🔐 **برای دریافت ویدیو باید در کانال/گروه‌های زیر عضو باشید:**\n\n"
                for i, sponsor in enumerate(missing_sponsors, 1):
                    sponsor_text += f"**اسپانسر {i}:** {sponsor['channel_name']}\n"
                
                bot.edit_message_text(
                    sponsor_text,
                    chat_id,
                    call.message.message_id,
                    reply_markup=generate_sponsor_check_keyboard(video_id, user_id),
                    parse_mode='Markdown'
                )
            except:
                pass
    
    elif data.startswith("verify_membership_"):
        video_id = data.replace("verify_membership_", "")
        
        video = get_video(video_id)
        if not video:
            bot.answer_callback_query(call.id, "❌ این ویدیو وجود ندارد!", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
            return
        
        missing_sponsors = get_missing_sponsors(user_id, video_id)
        
        if not missing_sponsors:
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            send_video_to_user(chat_id, video, user_id)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نیستید!", show_alert=True)

# ==================== HELPER FUNCTION FOR VIDEO DETAIL ====================
def show_video_detail(chat_id, message_id, video_id):
    video = get_video(video_id)
    if video:
        sponsors_list = "\n".join([f"• {s['channel_name']} (`{s['channel_id']}`)" for s in video['sponsors']]) if video['sponsors'] else "هیچ اسپانسری ثبت نشده"
        
        file_ids = video.get('file_ids', [])
        video_count = len(file_ids)
        spoiler_status = "✅ فعال" if video.get("has_spoiler", False) else "❌ غیرفعال"
        
        detail_text = f"""
🎬 **جزئیات ویدیو**

📝 **نام:** {video['name']}
🆔 **شناسه:** `{video['id']}`
📹 **تعداد فایل‌ها:** {video_count}
🔰 **اسپویلر:** {spoiler_status}
⏱️ **زمان حذف:** {video['delete_time']} ثانیه

👥 **اسپانسرها:**
{sponsors_list}
        """
        if message_id:
            bot.edit_message_text(
                detail_text,
                chat_id,
                message_id,
                reply_markup=generate_video_detail_keyboard(video_id),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                detail_text,
                reply_markup=generate_video_detail_keyboard(video_id),
                parse_mode='Markdown'
            )

# ==================== VIDEO ADDING PROCESS ====================
def process_video_name(message):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    if message.text and message.text.strip():
        name = message.text.strip()
        msg = bot.send_message(
            chat_id,
            f"✅ **نام ویدیو ثبت شد:** `{name}`\n\n"
            f"📹 **مرحله 2/5: حالا لینک‌های دانلود مستقیم را ارسال کنید:**\n\n"
            "می‌توانید لینک ویدیو و عکس را با کاما جدا کنید:\n"
            "مثال: `http://link1.mp4, http://link2.jpg, http://link3.mp4`\n\n"
            "همه فایل‌ها تحت یک نام و یک لینک اشتراک قرار می‌گیرند.",
            reply_markup=generate_back_keyboard("admin_back"),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_video_downloads, name)
    else:
        bot.send_message(chat_id, "❌ نام نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_back_keyboard("admin_back"))
        bot.register_next_step_handler(message, process_video_name)

def process_video_downloads(message, video_name):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    try:
        if message.text and message.text.strip():
            urls = [url.strip() for url in message.text.strip().split(',') if url.strip()]
            
            if not urls:
                bot.send_message(chat_id, "❌ لینک نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_back_keyboard("admin_back"))
                bot.register_next_step_handler(message, process_video_downloads, video_name)
                return
            
            bot.send_message(
                chat_id,
                f"⏳ **در حال دانلود {len(urls)} فایل... لطفاً صبر کنید**",
                parse_mode='Markdown'
            )
            
            file_ids = []
            for i, url in enumerate(urls):
                if chat_id in cancelled_operations:
                    cancelled_operations.discard(chat_id)
                    return
                
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    if response.status_code == 200:
                        # Determine file extension
                        content_type = response.headers.get('content-type', '')
                        if 'video' in content_type or url.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            ext = '.mp4'
                        else:
                            ext = '.jpg' if 'image' in content_type or url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else '.jpg'
                        
                        temp_file = f"temp_{int(time.time())}_{i}{ext}"
                        with open(temp_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        with open(temp_file, 'rb') as media_file:
                            if ext == '.mp4':
                                msg = bot.send_video(chat_id, media_file)
                                file_id = msg.video.file_id
                            else:
                                msg = bot.send_photo(chat_id, media_file)
                                file_id = msg.photo[-1].file_id
                        
                        os.remove(temp_file)
                        bot.delete_message(chat_id, msg.message_id)
                        file_ids.append({"file_id": file_id, "type": "video" if ext == '.mp4' else "photo"})
                    else:
                        bot.send_message(chat_id, f"❌ خطا در دانلود فایل {i+1}! لینک نامعتبر است.")
                        return
                except Exception as e:
                    bot.send_message(chat_id, f"❌ خطا در پردازش فایل {i+1}: {str(e)}")
                    return
            
            if chat_id in cancelled_operations:
                cancelled_operations.discard(chat_id)
                return
            
            # Ask spoiler question
            active_operations[chat_id] = {
                "status": "adding_video",
                "spoiler_pending": {
                    "video_name": video_name,
                    "file_ids": file_ids
                }
            }
            
            bot.send_message(
                chat_id,
                "🔰 **مرحله 3/5: آیا میخواهید به این محتوی اسپویلر اضافه کنید؟**\n\n"
                "بله / خیر",
                reply_markup=generate_spoiler_question_keyboard(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(chat_id, "❌ لینک نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_back_keyboard("admin_back"))
            bot.register_next_step_handler(message, process_video_downloads, video_name)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا: {str(e)}")

def process_sponsors(message, video_name, file_ids, has_spoiler):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    try:
        sponsors = []
        
        if message.text and message.text.strip().lower() != 'no':
            sponsor_pairs = message.text.strip().split(',')
            
            for pair in sponsor_pairs:
                if '/' in pair:
                    parts = pair.strip().split('/')
                    if len(parts) == 2:
                        channel_id = parts[0].strip()
                        channel_name = parts[1].strip()
                        sponsors.append({
                            "channel_id": channel_id,
                            "channel_name": channel_name
                        })
        
        sponsors_text = "\n".join([f"• {s['channel_name']} ({s['channel_id']})" for s in sponsors]) if sponsors else "بدون اسپانسر"
        
        # Edit the input message
        if chat_id in input_messages:
            try:
                bot.edit_message_text(
                    f"✅ **اسپانسرها ثبت شدند:**\n{sponsors_text}\n\n"
                    f"⏱️ **مرحله 5/5: زمان حذف خودکار را به ثانیه وارد کنید:**\n"
                    "مثال: 300 برای 5 دقیقه",
                    chat_id,
                    input_messages[chat_id],
                    reply_markup=generate_back_keyboard("admin_back"),
                    parse_mode='Markdown'
                )
                bot.register_next_step_handler(message, process_final_delete_time, video_name, file_ids, sponsors, has_spoiler)
                return
            except:
                pass
        
        msg = bot.send_message(
            chat_id,
            f"✅ **اسپانسرها ثبت شدند:**\n{sponsors_text}\n\n"
            f"⏱️ **مرحله 5/5: زمان حذف خودکار را به ثانیه وارد کنید:**\n"
            "مثال: 300 برای 5 دقیقه",
            reply_markup=generate_back_keyboard("admin_back"),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_final_delete_time, video_name, file_ids, sponsors, has_spoiler)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در پردازش اسپانسرها: {str(e)}")

def process_final_delete_time(message, video_name, file_ids, sponsors, has_spoiler):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    try:
        delete_time = int(message.text.strip())
        if delete_time <= 0:
            bot.send_message(chat_id, "❌ زمان باید بیشتر از 0 باشد!")
            return
        
        # Convert file_ids list to proper format for storage
        stored_file_ids = [f["file_id"] if isinstance(f, dict) else f for f in file_ids]
        file_types = [f.get("type", "video") if isinstance(f, dict) else "video" for f in file_ids]
        
        video_id = add_video(video_name, stored_file_ids, sponsors.copy(), delete_time, has_spoiler)
        
        # Also store file types
        update_video(video_id, {"file_types": file_types})
        
        share_link = f"https://t.me/{BOT_USERNAME}?start=video_{video_id}"
        
        sponsors_list = "\n".join([f"• {s['channel_name']} (`{s['channel_id']}`)" for s in sponsors]) if sponsors else "بدون اسپانسر"
        
        if chat_id in active_operations:
            del active_operations[chat_id]
        if chat_id in input_messages:
            del input_messages[chat_id]
        
        bot.send_message(
            chat_id,
            f"✅ **ویدیو با موفقیت اضافه شد!**\n\n"
            f"📝 **نام:** `{video_name}`\n"
            f"🆔 **شناسه:** `{video_id}`\n"
            f"📹 **تعداد فایل‌ها:** {len(stored_file_ids)}\n"
            f"🔰 **اسپویلر:** {'✅ فعال' if has_spoiler else '❌ غیرفعال'}\n"
            f"⏱️ **زمان حذف:** {delete_time} ثانیه\n"
            f"👥 **اسپانسرها:**\n{sponsors_list}\n\n"
            f"🔗 **لینک اشتراک:**\n`{share_link}`",
            parse_mode='Markdown'
        )
        
        bot.send_message(
            chat_id,
            WELCOME_TEXT,
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        bot.register_next_step_handler(message, process_final_delete_time, video_name, file_ids, sponsors, has_spoiler)

def process_add_sponsor(message, video_id):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    try:
        if message.text and message.text.strip():
            sponsor_pairs = message.text.strip().split(',')
            
            for pair in sponsor_pairs:
                if '/' in pair:
                    parts = pair.strip().split('/')
                    if len(parts) == 2:
                        channel_id = parts[0].strip()
                        channel_name = parts[1].strip()
                        add_sponsor(video_id, channel_id, channel_name)
            
            video = get_video(video_id)
            sponsors_list = "\n".join([f"• {s['channel_name']} (`{s['channel_id']}`)" for s in video['sponsors']]) if video['sponsors'] else "هیچ اسپانسری ثبت نشده"
            
            if chat_id in active_operations:
                del active_operations[chat_id]
            if chat_id in input_messages:
                del input_messages[chat_id]
            
            # Show success and go back to video detail
            bot.send_message(
                chat_id,
                f"✅ **اسپانسرها بروزرسانی شدند!**\n\n👥 **لیست فعلی:**\n{sponsors_list}",
                parse_mode='Markdown'
            )
            
            show_video_detail(chat_id, None, video_id)
        else:
            bot.send_message(chat_id, "❌ فرمت نادرست! لطفاً دوباره تلاش کنید.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا: {str(e)}")

def process_delete_time(message, video_id):
    chat_id = message.chat.id
    
    if chat_id in cancelled_operations:
        cancelled_operations.discard(chat_id)
        return
    
    try:
        delete_time = int(message.text.strip())
        if delete_time > 0:
            update_video(video_id, {"delete_time": delete_time})
            
            if chat_id in active_operations:
                del active_operations[chat_id]
            if chat_id in input_messages:
                del input_messages[chat_id]
            
            bot.send_message(
                chat_id,
                f"✅ **زمان حذف خودکار تنظیم شد:** {delete_time} ثانیه",
                parse_mode='Markdown'
            )
            
            show_video_detail(chat_id, None, video_id)
        else:
            bot.send_message(chat_id, "❌ زمان باید بیشتر از 0 باشد!")
    except ValueError:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")

# ==================== STATS & INFO FUNCTIONS ====================
def show_stats(chat_id, message_id=None):
    users_data = load_json(USERS_FILE)
    stats = load_json(STATS_FILE)
    videos = load_json(VIDEOS_FILE)
    
    total_users = len(users_data.get("users", []))
    total_views = users_data.get("total_views", 0)
    
    video_stats = []
    for video_id, stat_data in stats.items():
        if video_id != "total_views":
            video = get_video(video_id)
            if video:
                video_stats.append({
                    "name": video["name"],
                    "downloads": stat_data.get("downloads", 0),
                    "video_id": video_id
                })
    
    video_stats.sort(key=lambda x: x["downloads"], reverse=True)
    top_10 = video_stats[:10]
    
    stats_text = f"""
📊 **آمار بات**

👥 **تعداد کاربران:** {total_users}
👁️ **تعداد کل ویوها:** {total_views}
📹 **تعداد کل ویدیوها:** {len(videos)}

🏆 **10 ویدیو برتر:**
"""
    
    if top_10:
        for i, v_stat in enumerate(top_10, 1):
            stats_text += f"{i}. {v_stat['name']}: {v_stat['downloads']} دانلود\n"
    else:
        stats_text += "هنوز ویدیویی ثبت نشده است\n"
    
    if message_id:
        bot.edit_message_text(
            stats_text,
            chat_id,
            message_id,
            reply_markup=generate_stats_keyboard(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            stats_text,
            reply_markup=generate_stats_keyboard(),
            parse_mode='Markdown'
        )

def show_video_info(chat_id, message_id, video_id):
    video = get_video(video_id)
    stats = load_json(STATS_FILE)
    
    if not video:
        return
    
    video_stats = stats.get(video_id, {})
    downloads = video_stats.get("downloads", 0)
    added_date = video.get("added_date", "نامشخص")
    
    if added_date != "نامشخص":
        try:
            date_obj = datetime.fromisoformat(added_date)
            added_date = date_obj.strftime("%Y/%m/%d - %H:%M:%S")
        except:
            pass
    
    file_ids = video.get('file_ids', [])
    file_count = len(file_ids)
    spoiler_status = "✅ فعال" if video.get("has_spoiler", False) else "❌ غیرفعال"
    
    info_text = f"""
📊 **اطلاعات ویدیو**

📝 **نام:** {video['name']}
🆔 **شناسه:** `{video['id']}`
📹 **تعداد فایل‌ها:** {file_count}
🔰 **اسپویلر:** {spoiler_status}
📥 **تعداد دانلود:** {downloads}
📅 **تاریخ اضافه شدن:** {added_date}
⏱️ **زمان حذف:** {video['delete_time']} ثانیه
    """
    
    bot.edit_message_text(
        info_text,
        chat_id,
        message_id,
        reply_markup=generate_video_info_keyboard(video_id),
        parse_mode='Markdown'
    )

# ==================== VIDEO SENDING ====================
def send_video_to_user(chat_id, video, user_id):
    try:
        video_check = get_video(video["id"])
        if not video_check:
            bot.send_message(chat_id, "❌ ویدیوی مورد نظر وجود ندارد")
            return
        
        # Track view
        increment_view_count(video["id"])
        
        # Get all file_ids
        file_ids = video.get("file_ids", [])
        if not file_ids and "file_id" in video:
            file_ids = [video["file_id"]]
        
        has_spoiler = video.get("has_spoiler", False)
        
        # Send all files as a group
        media_group = []
        for i, file_id in enumerate(file_ids):
            # Determine if it's video or photo
            if str(file_id).startswith("BAAC") or str(file_id).startswith("AgAC"):  # Document/Photo IDs
                media_group.append(
                    types.InputMediaPhoto(file_id, has_spoiler=has_spoiler)
                )
            else:  # Video IDs
                media_group.append(
                    types.InputMediaVideo(file_id, has_spoiler=has_spoiler)
                )
        
        # Send as media group
        if len(media_group) > 1:
            try:
                messages = bot.send_media_group(chat_id, media_group)
                video_messages = [msg.message_id for msg in messages]
            except Exception as e:
                # If media group fails, send individually
                video_messages = []
                for media in media_group:
                    if isinstance(media, types.InputMediaVideo):
                        msg = bot.send_video(chat_id, media.media, has_spoiler=has_spoiler)
                    else:
                        msg = bot.send_photo(chat_id, media.media, has_spoiler=has_spoiler)
                    video_messages.append(msg.message_id)
        else:
            if isinstance(media_group[0], types.InputMediaVideo):
                msg = bot.send_video(chat_id, media_group[0].media, has_spoiler=has_spoiler)
            else:
                msg = bot.send_photo(chat_id, media_group[0].media, has_spoiler=has_spoiler)
            video_messages = [msg.message_id]
        
        # Send warning message
        bot.send_message(
            chat_id,
            "⏰ **این فایل‌ها به زودی حذف خواهند شد. لطفاً ذخیره کنید.**",
            parse_mode='Markdown'
        )
        
        # Schedule deletion
        delete_after = video["delete_time"]
        threading.Thread(target=schedule_delete_multiple, args=(chat_id, video_messages, video, delete_after)).start()
        
    except Exception as e:
        bot.send_message(chat_id, "❌ خطا در ارسال فایل! لطفاً دوباره تلاش کنید.")
        print(f"Error sending video: {e}")

def schedule_delete_multiple(chat_id, message_ids, video, delay):
    """حذف چند فایل بعد از زمان مشخص شده"""
    time.sleep(delay)
    try:
        video_check = get_video(video["id"])
        if not video_check:
            return
        
        for msg_id in message_ids:
            try:
                bot.delete_message(chat_id, msg_id)
                time.sleep(0.3)
            except Exception as e:
                print(f"Error deleting message {msg_id}: {e}")
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(create_glass_button("🔄 دانلود مجدد", f"check_sponsors_{video['id']}"))
        
        bot.send_message(
            chat_id,
            f"⏰ **فایل‌ها حذف شدند.**\nبرای دانلود مجدد، روی دکمه زیر کلیک کنید.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error in schedule delete: {e}")

# ==================== BOT START ====================
print("🤖 Bot is running...")
bot.infinity_polling()
