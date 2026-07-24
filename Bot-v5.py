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
def add_video(name, file_id, sponsors, delete_time):
    videos = load_json(VIDEOS_FILE)
    video_id = str(int(time.time()))
    video_data = {
        "id": video_id,
        "name": name,
        "file_id": file_id,
        "sponsors": sponsors,
        "delete_time": delete_time,
        "added_date": datetime.now().isoformat()
    }
    videos.append(video_data)
    save_json(VIDEOS_FILE, videos)
    
    # Initialize stats for this video
    stats = load_json(STATS_FILE)
    if video_id not in stats:
        stats[video_id] = {"downloads": 0, "added_date": video_data["added_date"]}
        save_json(STATS_FILE, stats)
    
    return video_id

def add_multiple_videos(video_data_list):
    """Add multiple videos at once"""
    video_ids = []
    for video_data in video_data_list:
        video_id = add_video(
            video_data["name"],
            video_data["file_id"],
            video_data["sponsors"],
            video_data["delete_time"]
        )
        video_ids.append(video_id)
    return video_ids

def get_video(video_id):
    videos = load_json(VIDEOS_FILE)
    for video in videos:
        if video["id"] == video_id:
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

def generate_video_list_keyboard(page=0, per_page=10):
    videos = load_json(VIDEOS_FILE)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    start = page * per_page
    end = start + per_page
    page_videos = videos[start:end]
    
    for video in page_videos:
        keyboard.add(
            create_glass_button(f"🎬 {video['name']}", f"video_detail_{video['id']}")
        )
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(create_glass_button("◀️ قبلی", f"video_page_{page-1}"))
    if end < len(videos):
        nav_buttons.append(create_glass_button("بعدی ▶️", f"video_page_{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.add(create_glass_button("🔙 بازگشت", "admin_back"))
    return keyboard

def generate_video_detail_keyboard(video_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        create_glass_button("👥 مدیریت اسپانسرها", f"manage_sponsors_{video_id}"),
        create_glass_button("⏱️ تنظیم زمان حذف", f"set_delete_time_{video_id}"),
        create_glass_button("📊 اطلاعات ویدیو", f"video_info_{video_id}"),
        create_glass_button("🔗 دریافت لینک اشتراک", f"get_share_link_{video_id}"),
        create_glass_button("🗑️ حذف ویدیو", f"confirm_delete_{video_id}"),
        create_glass_button("🔙 بازگشت به لیست", "admin_list_videos")
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

def generate_cancel_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(create_glass_button("❌ کنسل", "cancel_operation"))
    return keyboard

# ==================== MESSAGE HANDLERS ====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    # Track all users who start the bot
    track_user(user_id)
    
    if user_id not in ADMIN_IDS and len(args) == 1:
        return
    
    if user_id in ADMIN_IDS and len(args) == 1:
        welcome_text = """
🌟 **پنل مدیریت بات**

به پنل مدیریت خوش آمدید!
از دکمه‌های زیر برای مدیریت ویدیوها و اسپانسرها استفاده کنید.
        """
        bot.reply_to(message, welcome_text, reply_markup=generate_main_admin_keyboard(), parse_mode='Markdown')
        return
    
    if len(args) > 1 and args[1].startswith('video_'):
        video_id = args[1].replace('video_', '')
        video = get_video(video_id)
        
        if not video:
            bot.reply_to(message, "❌ ویدیوی مورد نظر وجود ندارد")
            return
        
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

@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.from_user.id in ADMIN_IDS)
def handle_admin_messages(message):
    """هر پیامی در پیوی برای ادمین‌ها پنل رو بفرسته"""
    if not message.text.startswith('/start'):
        bot.send_message(
            message.chat.id,
            "🌟 **پنل مدیریت بات**",
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    
    # Cancel operation
    if data == "cancel_operation":
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        bot.edit_message_text(
            "❌ **عملیات کنسل شد**",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.send_message(
            call.message.chat.id,
            "🌟 **پنل مدیریت بات**",
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    if data.startswith('admin_') or data.startswith('video_') or data.startswith('manage_') or data.startswith('set_delete_') or data.startswith('confirm_delete_') or data.startswith('get_share_') or data.startswith('video_info_'):
        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!")
            return
    
    # Admin Panel Callbacks
    if data == "admin_add_video":
        msg = bot.send_message(
            call.message.chat.id,
            "📝 **مرحله 1/4: لطفاً نام ویدیوها را وارد کنید:**\n(این نام فقط برای مدیریت نمایش داده می‌شود)\n\n"
            "برای چند ویدیو با کاما جدا کنید:\n"
            "مثال: `Video1, Video2, Video3`",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_video_names)
    
    elif data == "admin_list_videos":
        videos = load_json(VIDEOS_FILE)
        if not videos:
            bot.edit_message_text(
                "📋 **هیچ ویدیویی ثبت نشده است!**",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=generate_main_admin_keyboard(),
                parse_mode='Markdown'
            )
        else:
            bot.edit_message_text(
                "📋 **لیست ویدیوها:**",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=generate_video_list_keyboard(),
                parse_mode='Markdown'
            )
    
    elif data == "admin_stats":
        show_stats(call.message.chat.id, call.message.message_id)
    
    elif data.startswith("video_page_"):
        page = int(data.split("_")[2])
        bot.edit_message_text(
            "📋 **لیست ویدیوها:**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=generate_video_list_keyboard(page),
            parse_mode='Markdown'
        )
    
    elif data.startswith("video_detail_"):
        video_id = data.replace("video_detail_", "")
        video = get_video(video_id)
        if video:
            sponsors_list = "\n".join([f"• {s['channel_name']} (`{s['channel_id']}`)" for s in video['sponsors']]) if video['sponsors'] else "هیچ اسپانسری ثبت نشده"
            
            detail_text = f"""
🎬 **جزئیات ویدیو**

📝 **نام:** {video['name']}
🆔 **شناسه:** `{video['id']}`
⏱️ **زمان حذف:** {video['delete_time']} ثانیه

👥 **اسپانسرها:**
{sponsors_list}
            """
            bot.edit_message_text(
                detail_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=generate_video_detail_keyboard(video_id),
                parse_mode='Markdown'
            )
    
    elif data.startswith("video_info_"):
        video_id = data.replace("video_info_", "")
        show_video_info(call.message.chat.id, call.message.message_id, video_id)
    
    elif data.startswith("manage_sponsors_"):
        video_id = data.replace("manage_sponsors_", "")
        video = get_video(video_id)
        current_sponsors = "\n".join([f"• {s['channel_name']} - `{s['channel_id']}`" for s in video['sponsors']]) if video['sponsors'] else "هیچ اسپانسری ثبت نشده"
        
        msg = bot.send_message(
            call.message.chat.id,
            f"👥 **مدیریت اسپانسرها**\n\n"
            f"**اسپانسرهای فعلی:**\n{current_sponsors}\n\n"
            "برای افزودن اسپانسر(ها)، به این فرمت وارد کنید:\n"
            "`channel_id1/channel_name1, channel_id2/channel_name2`\n\n"
            "مثال: `@testchannel/کانال تست, -1001234567890/گروه تست`\n\n"
            "از / برای جدا کردن آیدی و نام استفاده کنید\n"
            "از , برای جدا کردن اسپانسرهای مختلف استفاده کنید",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_add_sponsor, video_id)
    
    elif data.startswith("set_delete_time_"):
        video_id = data.replace("set_delete_time_", "")
        msg = bot.send_message(
            call.message.chat.id,
            "⏱️ **لطفاً زمان حذف خودکار را به ثانیه وارد کنید:**\n"
            "مثال: 300 برای 5 دقیقه",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_delete_time, video_id)
    
    elif data.startswith("confirm_delete_"):
        video_id = data.replace("confirm_delete_", "")
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            create_glass_button("✅ بله", f"delete_video_{video_id}"),
            create_glass_button("❌ خیر", f"video_detail_{video_id}")
        )
        bot.edit_message_text(
            "⚠️ **آیا از حذف این ویدیو اطمینان دارید؟**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data.startswith("delete_video_"):
        video_id = data.replace("delete_video_", "")
        delete_video(video_id)
        bot.edit_message_text(
            "✅ **ویدیو با موفقیت حذف شد!**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data.startswith("get_share_link_"):
        video_id = data.replace("get_share_link_", "")
        share_link = f"https://t.me/{BOT_USERNAME}?start=video_{video_id}"
        bot.answer_callback_query(call.id, "✅ لینک کپی شد!")
        bot.send_message(
            call.message.chat.id,
            f"🔗 **لینک اشتراک ویدیو:**\n`{share_link}`",
            parse_mode='Markdown'
        )
    
    elif data == "admin_back":
        bot.edit_message_text(
            "🌟 **پنل مدیریت بات**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
    
    # User Callbacks
    elif data.startswith("check_sponsors_"):
        video_id = data.replace("check_sponsors_", "")
        
        # بررسی وجود ویدیو
        video = get_video(video_id)
        if not video:
            bot.answer_callback_query(call.id, "❌ ویدیوی مورد نظر وجود ندارد", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        
        missing_sponsors = get_missing_sponsors(user_id, video_id)
        
        if not missing_sponsors:
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            send_video_to_user(call.message.chat.id, video, user_id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نیستید!")
            bot.edit_message_text(
                call.message.text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=generate_sponsor_check_keyboard(video_id, user_id),
                parse_mode='Markdown'
            )
    
    elif data.startswith("verify_membership_"):
        video_id = data.replace("verify_membership_", "")
        
        # بررسی وجود ویدیو
        video = get_video(video_id)
        if not video:
            bot.answer_callback_query(call.id, "❌ ویدیوی مورد نظر وجود ندارد", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        
        missing_sponsors = get_missing_sponsors(user_id, video_id)
        
        if not missing_sponsors:
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            send_video_to_user(call.message.chat.id, video, user_id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نیستید!")

# ==================== VIDEO ADDING PROCESS ====================
def process_video_names(message):
    if message.text and message.text.strip():
        names = [name.strip() for name in message.text.strip().split(',') if name.strip()]
        if not names:
            bot.send_message(message.chat.id, "❌ نام نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_cancel_keyboard())
            bot.register_next_step_handler(message, process_video_names)
            return
        
        msg = bot.send_message(
            message.chat.id,
            f"✅ **تعداد {len(names)} ویدیو ثبت شد**\n\n"
            f"📹 **مرحله 2/4: حالا لینک‌های دانلود مستقیم ویدیوها را ارسال کنید:**\n\n"
            "با کاما جدا کنید (به ترتیب نام‌ها):\n"
            "مثال: `http://link1.mp4, http://link2.mp4, http://link3.mp4`\n\n"
            f"**نام‌ها:** {', '.join(names)}",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_video_downloads, names)
    else:
        bot.send_message(message.chat.id, "❌ نام نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_cancel_keyboard())
        bot.register_next_step_handler(message, process_video_names)

def process_video_downloads(message, video_names):
    try:
        if message.text and message.text.strip():
            urls = [url.strip() for url in message.text.strip().split(',') if url.strip()]
            
            if len(urls) != len(video_names):
                bot.send_message(
                    message.chat.id,
                    f"❌ تعداد لینک‌ها ({len(urls)}) با تعداد نام‌ها ({len(video_names)}) مطابقت ندارد!",
                    reply_markup=generate_cancel_keyboard()
                )
                bot.register_next_step_handler(message, process_video_downloads, video_names)
                return
            
            file_ids = []
            for i, url in enumerate(urls):
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    if response.status_code == 200:
                        temp_file = f"temp_{int(time.time())}_{i}.mp4"
                        with open(temp_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        with open(temp_file, 'rb') as video_file:
                            msg = bot.send_video(message.chat.id, video_file, caption=f"📹 ویدیو {i+1}: {video_names[i]}")
                            file_id = msg.video.file_id
                        
                        os.remove(temp_file)
                        bot.delete_message(message.chat.id, msg.message_id)
                        file_ids.append(file_id)
                    else:
                        bot.send_message(message.chat.id, f"❌ خطا در دانلود ویدیو {i+1}! لینک نامعتبر است.")
                        return
                except Exception as e:
                    bot.send_message(message.chat.id, f"❌ خطا در پردازش ویدیو {i+1}: {str(e)}")
                    return
            
            msg = bot.send_message(
                message.chat.id,
                f"✅ **{len(file_ids)} ویدیو دانلود شد!**\n\n"
                f"👥 **مرحله 3/4: حالا اسپانسرها را وارد کنید:**\n\n"
                "فرمت: `channel_id1/channel_name1, channel_id2/channel_name2`\n"
                "مثال: `@testchannel/کانال تست, -1001234567890/گروه تست`\n\n"
                "اگر اسپانسر نمی‌خواهید، کلمه `no` را بفرستید.\n"
                "همه ویدیوها اسپانسرهای یکسانی خواهند داشت.",
                reply_markup=generate_cancel_keyboard(),
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_sponsors_multiple, video_names, file_ids)
        else:
            bot.send_message(message.chat.id, "❌ لینک نامعتبر! لطفاً دوباره تلاش کنید.", reply_markup=generate_cancel_keyboard())
            bot.register_next_step_handler(message, process_video_downloads, video_names)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

def process_sponsors_multiple(message, video_names, file_ids):
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
        
        msg = bot.send_message(
            message.chat.id,
            f"✅ **اسپانسرها ثبت شدند:**\n{sponsors_text}\n\n"
            f"⏱️ **مرحله 4/4: زمان حذف خودکار را به ثانیه وارد کنید:**\n"
            "مثال: 300 برای 5 دقیقه\n"
            "همه ویدیوها زمان حذف یکسانی خواهند داشت.",
            reply_markup=generate_cancel_keyboard(),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_final_delete_time_multiple, video_names, file_ids, sponsors)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در پردازش اسپانسرها: {str(e)}")

def process_final_delete_time_multiple(message, video_names, file_ids, sponsors):
    try:
        delete_time = int(message.text.strip())
        if delete_time <= 0:
            bot.send_message(message.chat.id, "❌ زمان باید بیشتر از 0 باشد!")
            return
        
        video_ids = []
        for i in range(len(video_names)):
            video_id = add_video(video_names[i], file_ids[i], sponsors.copy(), delete_time)
            video_ids.append(video_id)
        
        share_links = []
        for i, video_id in enumerate(video_ids):
            share_link = f"https://t.me/{BOT_USERNAME}?start=video_{video_id}"
            share_links.append(f"**{video_names[i]}:** `{share_link}`")
        
        sponsors_list = "\n".join([f"• {s['channel_name']} (`{s['channel_id']}`)" for s in sponsors]) if sponsors else "بدون اسپانسر"
        
        bot.send_message(
            message.chat.id,
            f"✅ **{len(video_ids)} ویدیو با موفقیت اضافه شدند!**\n\n"
            f"⏱️ **زمان حذف:** {delete_time} ثانیه\n"
            f"👥 **اسپانسرها:**\n{sponsors_list}\n\n"
            f"🔗 **لینک‌های اشتراک:**\n" + "\n".join(share_links),
            parse_mode='Markdown'
        )
        
        bot.send_message(
            message.chat.id,
            "🌟 **پنل مدیریت بات**",
            reply_markup=generate_main_admin_keyboard(),
            parse_mode='Markdown'
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        bot.register_next_step_handler(message, process_final_delete_time_multiple, video_names, file_ids, sponsors)

def process_add_sponsor(message, video_id):
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
            
            bot.send_message(
                message.chat.id,
                f"✅ **اسپانسرها بروزرسانی شدند!**\n\n👥 **لیست فعلی:**\n{sponsors_list}",
                parse_mode='Markdown'
            )
            
            bot.send_message(
                message.chat.id,
                "🔙 بازگشت به جزئیات ویدیو:",
                reply_markup=generate_video_detail_keyboard(video_id),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ فرمت نادرست! لطفاً دوباره تلاش کنید.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

def process_delete_time(message, video_id):
    try:
        delete_time = int(message.text.strip())
        if delete_time > 0:
            update_video(video_id, {"delete_time": delete_time})
            bot.send_message(
                message.chat.id,
                f"✅ **زمان حذف خودکار تنظیم شد:** {delete_time} ثانیه",
                parse_mode='Markdown'
            )
            bot.send_message(
                message.chat.id,
                "🔙 بازگشت به جزئیات ویدیو:",
                reply_markup=generate_video_detail_keyboard(video_id),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ زمان باید بیشتر از 0 باشد!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید!")

# ==================== STATS & INFO FUNCTIONS ====================
def show_stats(chat_id, message_id=None):
    users_data = load_json(USERS_FILE)
    stats = load_json(STATS_FILE)
    videos = load_json(VIDEOS_FILE)
    
    total_users = len(users_data.get("users", []))
    total_views = users_data.get("total_views", 0)
    
    # Get top 10 videos by downloads
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
    
    # Sort by downloads
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
        bot.answer_callback_query(call.id, "❌ ویدیو یافت نشد", show_alert=True)
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
    
    info_text = f"""
📊 **اطلاعات ویدیو**

📝 **نام:** {video['name']}
🆔 **شناسه:** `{video['id']}`
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
        # بررسی وجود ویدیو در لیست
        video_check = get_video(video["id"])
        if not video_check:
            bot.send_message(chat_id, "❌ ویدیوی مورد نظر وجود ندارد")
            return
        
        # Track view
        increment_view_count(video["id"])
        
        # ارسال ویدیو
        video_msg = bot.send_video(
            chat_id,
            video["file_id"]
        )
        
        # ارسال پیام جداگانه برای هشدار
        bot.send_message(
            chat_id,
            "⏰ **این ویدیو به زودی حذف خواهد شد. لطفاً ذخیره کنید.**",
            parse_mode='Markdown'
        )
        
        delete_after = video["delete_time"]
        threading.Thread(target=schedule_delete, args=(chat_id, video_msg.message_id, video, delete_after)).start()
        
    except Exception as e:
        bot.send_message(chat_id, "❌ خطا در ارسال ویدیو! لطفاً دوباره تلاش کنید.")
        print(f"Error sending video: {e}")

def schedule_delete(chat_id, message_id, video, delay):
    """حذف ویدیو بعد از زمان مشخص شده"""
    time.sleep(delay)
    try:
        # بررسی وجود ویدیو قبل از حذف
        video_check = get_video(video["id"])
        if not video_check:
            # اگر ویدیو وجود نداشت، پیام خطا ارسال کن
            bot.send_message(
                chat_id,
                "❌ ویدیوی مورد نظر وجود ندارد"
            )
            return
            
        bot.delete_message(chat_id, message_id)
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(create_glass_button("🔄 دانلود مجدد", f"check_sponsors_{video['id']}"))
        
        bot.send_message(
            chat_id,
            f"⏰ **ویدیو حذف شد.**\nبرای دانلود مجدد، روی دکمه زیر کلیک کنید.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error in schedule delete: {e}")

# ==================== BOT START ====================
print("🤖 Bot is running...")
bot.infinity_polling()
