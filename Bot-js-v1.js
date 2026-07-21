// ==================== Cloudflare Worker - Telegram Bot ====================

const CONFIG = {
  TOKEN: "8949661112:AAEF7edIbhHkGWi3MgLy0O4DJVIrE8YfiRw",
  ADMIN_IDS: [6378393027, 5713289649],
  BOT_USERNAME: "Cuteiii_bot",
  WEBHOOK_PATH: "/webhook"
};

// ==================== HTML PANEL ====================
const PANEL_HTML = `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 پنل مدیریت ربات</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header p { color: #666; font-size: 1.1em; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card .icon { font-size: 2em; margin-bottom: 10px; }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-card .label { color: #666; margin-top: 5px; font-size: 1.1em; }
        .control-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .control-panel h2 { font-size: 1.8em; margin-bottom: 20px; color: #667eea; }
        .bot-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .status-indicator { display: flex; align-items: center; gap: 10px; }
        .status-dot {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.active {
            background: #4CAF50;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        .status-dot.inactive {
            background: #f44336;
            box-shadow: 0 0 10px rgba(244, 67, 54, 0.5);
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: white;
        }
        .btn-success {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
        }
        .btn-danger {
            background: linear-gradient(135deg, #f44336, #da190b);
            box-shadow: 0 5px 15px rgba(244, 67, 54, 0.3);
        }
        .btn-warning {
            background: linear-gradient(135deg, #ff9800, #f57c00);
            box-shadow: 0 5px 15px rgba(255, 152, 0, 0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }
        .btn:active { transform: translateY(0); }
        .info-section {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
            flex-wrap: wrap;
            gap: 10px;
        }
        .info-item:last-child { border-bottom: none; }
        .info-label { font-weight: bold; color: #666; }
        .info-value {
            color: #333;
            font-family: monospace;
            background: #fff;
            padding: 5px 10px;
            border-radius: 5px;
            word-break: break-all;
        }
        .setup-section {
            margin-top: 20px;
            padding: 20px;
            background: #fff3cd;
            border-radius: 15px;
            border: 1px solid #ffc107;
        }
        .setup-section h3 { color: #856404; margin-bottom: 15px; }
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            display: none;
            animation: slideIn 0.3s ease;
            z-index: 1000;
        }
        @keyframes slideIn {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .toast.success { border-right: 4px solid #4CAF50; }
        .toast.error { border-right: 4px solid #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 پنل مدیریت ربات</h1>
            <p>مدیریت و مانیتورینگ ربات تلگرام</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">👥</div>
                <div class="value" id="totalUsers">0</div>
                <div class="label">کاربران کل</div>
            </div>
            <div class="stat-card">
                <div class="icon">🎬</div>
                <div class="value" id="totalVideos">0</div>
                <div class="label">ویدیوها</div>
            </div>
            <div class="stat-card">
                <div class="icon">📢</div>
                <div class="value" id="totalSponsors">0</div>
                <div class="label">اسپانسرها</div>
            </div>
            <div class="stat-card">
                <div class="icon">⚡</div>
                <div class="value" id="webhookStatus">-</div>
                <div class="label">وضعیت Webhook</div>
            </div>
        </div>
        
        <div class="control-panel">
            <h2>🎮 کنترل ربات</h2>
            <div class="bot-status">
                <div class="status-indicator">
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText" style="font-size: 1.2em; font-weight: bold;">در حال بررسی...</span>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-success" onclick="toggleBot('start')" id="startBtn">
                        ▶️ روشن
                    </button>
                    <button class="btn btn-danger" onclick="toggleBot('stop')" id="stopBtn">
                        ⏸️ خاموش
                    </button>
                    <button class="btn btn-warning" onclick="setupWebhook()">
                        🔄 تنظیم Webhook
                    </button>
                </div>
            </div>
            
            <div class="info-section">
                <h3>📊 اطلاعات ربات</h3>
                <div class="info-item">
                    <span class="info-label">نام ربات:</span>
                    <span class="info-value">@${CONFIG.BOT_USERNAME}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Webhook URL:</span>
                    <span class="info-value" id="webhookUrl">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">آخرین بروزرسانی:</span>
                    <span class="info-value" id="lastUpdate">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">نسخه:</span>
                    <span class="info-value">2.0.0</span>
                </div>
            </div>
            
            <div class="setup-section">
                <h3>🚀 راه‌اندازی سریع</h3>
                <p style="margin-bottom: 15px; color: #856404;">
                    برای راه‌اندازی اولیه، روی دکمه زیر کلیک کنید. این کار دیتابیس و Webhook رو خودکار تنظیم می‌کنه.
                </p>
                <button class="btn btn-warning" onclick="initialSetup()">
                    ⚡ راه‌اندازی خودکار
                </button>
                <div id="setupResult" style="margin-top: 15px;"></div>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        let botStatus = false;
        const BOT_USERNAME = '${CONFIG.BOT_USERNAME}';
        
        async function loadStats() {
            try {
                const response = await fetch('/panel/api/stats');
                const data = await response.json();
                
                document.getElementById('totalUsers').textContent = data.users || 0;
                document.getElementById('totalVideos').textContent = data.videos || 0;
                document.getElementById('totalSponsors').textContent = data.sponsors || 0;
                document.getElementById('webhookStatus').textContent = data.webhookSet ? '✅ فعال' : '❌ غیرفعال';
                document.getElementById('webhookUrl').textContent = data.webhookUrl || '-';
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString('fa-IR');
                
                botStatus = data.botStatus || false;
                updateStatusUI();
            } catch (error) {
                console.error('Error loading stats:', error);
                showToast('❌ خطا در بارگذاری اطلاعات', 'error');
            }
        }
        
        function updateStatusUI() {
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');
            const stopBtn = document.getElementById('stopBtn');
            const startBtn = document.getElementById('startBtn');
            
            if (botStatus) {
                dot.className = 'status-dot active';
                text.textContent = '🟢 ربات فعال است';
                stopBtn.style.opacity = '1';
                startBtn.style.opacity = '0.5';
            } else {
                dot.className = 'status-dot inactive';
                text.textContent = '🔴 ربات غیرفعال است';
                stopBtn.style.opacity = '0.5';
                startBtn.style.opacity = '1';
            }
        }
        
        async function toggleBot(action) {
            try {
                const response = await fetch('/panel/api/toggle-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    botStatus = action === 'start';
                    updateStatusUI();
                    showToast(action === 'start' ? '✅ ربات با موفقیت روشن شد' : '⏸️ ربات با موفقیت خاموش شد', 'success');
                    
                    if (action === 'start') {
                        await setupWebhook();
                    }
                } else {
                    showToast('❌ خطا در تغییر وضعیت ربات', 'error');
                }
            } catch (error) {
                showToast('❌ خطا در ارتباط با سرور', 'error');
            }
        }
        
        async function setupWebhook() {
            try {
                showToast('🔄 در حال تنظیم Webhook...', 'success');
                const response = await fetch('/panel/api/setup-webhook', { method: 'POST' });
                const data = await response.json();
                
                if (data.ok) {
                    showToast('✅ Webhook با موفقیت تنظیم شد', 'success');
                    loadStats();
                } else {
                    showToast('❌ خطا در تنظیم Webhook: ' + (data.description || ''), 'error');
                }
            } catch (error) {
                showToast('❌ خطا در ارتباط با سرور', 'error');
            }
        }
        
        async function initialSetup() {
            const resultDiv = document.getElementById('setupResult');
            resultDiv.innerHTML = '<div style="color: #856404;">🔄 در حال راه‌اندازی... لطفاً صبر کنید</div>';
            
            try {
                // Setup database
                const dbResponse = await fetch('/panel/api/setup-database', { method: 'POST' });
                const dbData = await dbResponse.json();
                
                if (dbData.success) {
                    resultDiv.innerHTML += '<div style="color: green;">✅ دیتابیس با موفقیت ساخته شد</div>';
                } else {
                    resultDiv.innerHTML += '<div style="color: red;">❌ خطا در ساخت دیتابیس: ' + dbData.error + '</div>';
                    return;
                }
                
                // Setup webhook
                const webhookResponse = await fetch('/panel/api/setup-webhook', { method: 'POST' });
                const webhookData = await webhookResponse.json();
                
                if (webhookData.ok) {
                    resultDiv.innerHTML += '<div style="color: green;">✅ Webhook با موفقیت تنظیم شد</div>';
                } else {
                    resultDiv.innerHTML += '<div style="color: red;">❌ خطا در تنظیم Webhook: ' + (webhookData.description || '') + '</div>';
                }
                
                // Enable bot
                await fetch('/panel/api/toggle-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'start' })
                });
                
                resultDiv.innerHTML += '<div style="color: green; margin-top: 10px; font-weight: bold;">🎉 راه‌اندازی کامل شد! ربات آماده استفاده است.</div>';
                
                loadStats();
            } catch (error) {
                resultDiv.innerHTML += '<div style="color: red;">❌ خطا: ' + error.message + '</div>';
            }
        }
        
        function showToast(message, type) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast ' + type;
            toast.style.display = 'block';
            
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }
        
        // Initial load
        loadStats();
        
        // Refresh every 30 seconds
        setInterval(loadStats, 30000);
    </script>
</body>
</html>`;

// ==================== DATABASE SETUP ====================
async function setupDatabase(db) {
  const queries = [
    `CREATE TABLE IF NOT EXISTS videos (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      file_id TEXT NOT NULL,
      delete_time INTEGER NOT NULL DEFAULT 300,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )`,
    `CREATE TABLE IF NOT EXISTS sponsors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      video_id TEXT NOT NULL,
      channel_id TEXT NOT NULL,
      channel_name TEXT NOT NULL,
      FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
    )`,
    `CREATE TABLE IF NOT EXISTS users (
      user_id INTEGER PRIMARY KEY,
      username TEXT,
      first_name TEXT,
      last_name TEXT,
      joined_at TEXT NOT NULL DEFAULT (datetime('now')),
      last_activity TEXT NOT NULL DEFAULT (datetime('now'))
    )`,
    `CREATE TABLE IF NOT EXISTS bot_settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    )`,
    `INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_status', 'active')`,
    `INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('webhook_url', '')`
  ];

  for (const query of queries) {
    try {
      await db.prepare(query).run();
    } catch (error) {
      console.error('Database setup error:', error);
      return false;
    }
  }
  
  return true;
}

// ==================== TELEGRAM API HELPER ====================
class TelegramAPI {
  constructor(token) {
    this.token = token;
    this.baseUrl = `https://api.telegram.org/bot${token}`;
  }

  async sendRequest(method, body) {
    const response = await fetch(`${this.baseUrl}/${method}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    return await response.json();
  }

  async sendMessage(chatId, text, options = {}) {
    return await this.sendRequest('sendMessage', {
      chat_id: chatId,
      text: text,
      parse_mode: options.parse_mode || 'Markdown',
      reply_markup: options.reply_markup,
      ...options
    });
  }

  async sendVideo(chatId, video, options = {}) {
    return await this.sendRequest('sendVideo', {
      chat_id: chatId,
      video: video,
      ...options
    });
  }

  async deleteMessage(chatId, messageId) {
    return await this.sendRequest('deleteMessage', {
      chat_id: chatId,
      message_id: messageId
    });
  }

  async getChatMember(chatId, userId) {
    return await this.sendRequest('getChatMember', {
      chat_id: chatId,
      user_id: userId
    });
  }

  async setWebhook(url) {
    return await this.sendRequest('setWebhook', { url });
  }

  async getWebhookInfo() {
    const response = await fetch(`${this.baseUrl}/getWebhookInfo`);
    return await response.json();
  }
}

// ==================== DATABASE HELPER ====================
class Database {
  constructor(db) {
    this.db = db;
  }

  async getVideos() {
    const { results } = await this.db.prepare('SELECT * FROM videos').all();
    return results;
  }

  async getVideo(id) {
    const video = await this.db.prepare('SELECT * FROM videos WHERE id = ?').bind(id).first();
    if (video) {
      const { results: sponsors } = await this.db.prepare('SELECT * FROM sponsors WHERE video_id = ?').bind(id).all();
      video.sponsors = sponsors;
    }
    return video;
  }

  async addVideo(id, name, fileId, deleteTime) {
    await this.db.prepare('INSERT INTO videos (id, name, file_id, delete_time) VALUES (?, ?, ?, ?)')
      .bind(id, name, fileId, deleteTime).run();
  }

  async updateVideo(id, updates) {
    const sets = [];
    const values = [];
    for (const [key, value] of Object.entries(updates)) {
      sets.push(`${key} = ?`);
      values.push(value);
    }
    values.push(id);
    await this.db.prepare(`UPDATE videos SET ${sets.join(', ')} WHERE id = ?`).bind(...values).run();
  }

  async deleteVideo(id) {
    await this.db.prepare('DELETE FROM sponsors WHERE video_id = ?').bind(id).run();
    await this.db.prepare('DELETE FROM videos WHERE id = ?').bind(id).run();
  }

  async addSponsor(videoId, channelId, channelName) {
    await this.db.prepare('INSERT INTO sponsors (video_id, channel_id, channel_name) VALUES (?, ?, ?)')
      .bind(videoId, channelId, channelName).run();
  }

  async addUser(userId, username, firstName, lastName) {
    await this.db.prepare(`
      INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_activity) 
      VALUES (?, ?, ?, ?, datetime('now'))
    `).bind(userId, username, firstName, lastName).run();
  }

  async getTotalUsers() {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM users').first();
    return result.count;
  }

  async getTotalVideos() {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM videos').first();
    return result.count;
  }

  async getTotalSponsors() {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM sponsors').first();
    return result.count;
  }

  async getSetting(key) {
    const result = await this.db.prepare('SELECT value FROM bot_settings WHERE key = ?').bind(key).first();
    return result ? result.value : null;
  }

  async setSetting(key, value) {
    await this.db.prepare('INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)').bind(key, value).run();
  }
}

// ==================== KEYBOARD GENERATORS ====================
function createInlineKeyboard(buttons) {
  return { inline_keyboard: [buttons] };
}

function createGlassButton(text, callbackData) {
  return { text: `✨ ${text} ✨`, callback_data: callbackData };
}

function createGlassButtonUrl(text, url) {
  return { text: `🔗 ${text}`, url: url };
}

function mainAdminKeyboard() {
  return createInlineKeyboard([
    createGlassButton('➕ افزودن ویدیو جدید', 'admin_add_video'),
    createGlassButton('📋 لیست ویدیوها', 'admin_list_videos'),
    createGlassButton('⚙️ تنظیمات', 'admin_settings')
  ]);
}

function videoListKeyboard(videos, page = 0, perPage = 10) {
  const start = page * perPage;
  const end = start + perPage;
  const pageVideos = videos.slice(start, end);
  
  const buttons = pageVideos.map(v => 
    createGlassButton(`🎬 ${v.name}`, `video_detail_${v.id}`)
  );
  
  const navButtons = [];
  if (page > 0) {
    navButtons.push(createGlassButton('◀️ قبلی', `video_page_${page - 1}`));
  }
  if (end < videos.length) {
    navButtons.push(createGlassButton('بعدی ▶️', `video_page_${page + 1}`));
  }
  
  const allButtons = [...buttons];
  if (navButtons.length > 0) {
    allButtons.push(...navButtons);
  }
  allButtons.push(createGlassButton('🔙 بازگشت', 'admin_back'));
  
  return createInlineKeyboard(allButtons);
}

function videoDetailKeyboard(videoId) {
  return createInlineKeyboard([
    createGlassButton('👥 مدیریت اسپانسرها', `manage_sponsors_${videoId}`),
    createGlassButton('⏱️ تنظیم زمان حذف', `set_delete_time_${videoId}`),
    createGlassButton('🔗 دریافت لینک اشتراک', `get_share_link_${videoId}`),
    createGlassButton('🗑️ حذف ویدیو', `confirm_delete_${videoId}`),
    createGlassButton('🔙 بازگشت به لیست', 'admin_list_videos')
  ]);
}

function sponsorCheckKeyboard(videoId, missingSponsors) {
  const buttons = [];
  
  if (missingSponsors.length === 0) {
    buttons.push(createGlassButton('✅ تایید عضویت', `verify_membership_${videoId}`));
  } else {
    for (const sponsor of missingSponsors) {
      let url;
      if (sponsor.channel_id.startsWith('@')) {
        url = `https://t.me/${sponsor.channel_id.substring(1)}`;
      } else if (sponsor.channel_id.replace('-', '').match(/^\d+$/)) {
        url = `https://t.me/c/${sponsor.channel_id.replace('-', '')}`;
      } else {
        url = `https://t.me/${sponsor.channel_id}`;
      }
      buttons.push(createGlassButtonUrl(`📢 ${sponsor.channel_name}`, url));
    }
    buttons.push(createGlassButton('🔄 بررسی عضویت', `check_sponsors_${videoId}`));
  }
  
  return createInlineKeyboard(buttons);
}

// ==================== MEMBERSHIP CHECK ====================
async function checkMembership(telegram, userId, channelId) {
  try {
    let chatId = channelId;
    if (chatId.startsWith('@')) {
      chatId = chatId.substring(1);
    }
    
    if (chatId.replace('-', '').match(/^\d+$/)) {
      chatId = parseInt(chatId);
    } else {
      chatId = `@${chatId}`;
    }
    
    const member = await telegram.getChatMember(chatId, userId);
    return member.result && !['left', 'kicked', 'banned'].includes(member.result.status);
  } catch (error) {
    console.error('Error checking membership:', error);
    return false;
  }
}

async function getMissingSponsors(telegram, db, userId, videoId) {
  const video = await db.getVideo(videoId);
  if (!video) return [];
  
  const missing = [];
  for (const sponsor of video.sponsors) {
    if (!(await checkMembership(telegram, userId, sponsor.channel_id))) {
      missing.push(sponsor);
    }
  }
  
  return missing;
}

// ==================== MESSAGE HANDLERS ====================
async function handleStart(message, telegram, db) {
  const userId = message.from.id;
  const args = message.text.split(' ');
  
  // Save user
  await db.addUser(
    userId,
    message.from.username,
    message.from.first_name,
    message.from.last_name
  );
  
  if (!CONFIG.ADMIN_IDS.includes(userId) && args.length === 1) {
    return;
  }
  
  if (CONFIG.ADMIN_IDS.includes(userId) && args.length === 1) {
    const welcomeText = `🌟 **پنل مدیریت بات**\n\nبه پنل مدیریت خوش آمدید!\nاز دکمه‌های زیر برای مدیریت ویدیوها و اسپانسرها استفاده کنید.`;
    await telegram.sendMessage(message.chat.id, welcomeText, {
      reply_markup: mainAdminKeyboard()
    });
    return;
  }
  
  if (args.length > 1 && args[1].startsWith('video_')) {
    const videoId = args[1].replace('video_', '');
    const video = await db.getVideo(videoId);
    
    if (!video) {
      await telegram.sendMessage(message.chat.id, '❌ ویدیو مورد نظر یافت نشد!');
      return;
    }
    
    const missingSponsors = await getMissingSponsors(telegram, db, userId, videoId);
    
    if (missingSponsors.length > 0) {
      let sponsorText = '🔐 **برای دریافت ویدیو باید در کانال/گروه‌های زیر عضو باشید:**\n\n';
      missingSponsors.forEach((s, i) => {
        sponsorText += `**اسپانسر ${i + 1}:** ${s.channel_name}\n`;
      });
      
      await telegram.sendMessage(message.chat.id, sponsorText, {
        reply_markup: sponsorCheckKeyboard(videoId, missingSponsors)
      });
    } else {
      await sendVideoToUser(telegram, db, message.chat.id, video, userId);
    }
  }
}

async function sendVideoToUser(telegram, db, chatId, video, userId) {
  try {
    const videoMsg = await telegram.sendVideo(chatId, video.file_id);
    
    await telegram.sendMessage(chatId, '⏰ **این ویدیو به زودی حذف خواهد شد. لطفاً ذخیره کنید.**');
    
    // Schedule deletion
    setTimeout(async () => {
      try {
        await telegram.deleteMessage(chatId, videoMsg.result.message_id);
        
        const keyboard = createInlineKeyboard([
          createGlassButton('🔄 دانلود مجدد', `check_sponsors_${video.id}`)
        ]);
        
        await telegram.sendMessage(chatId, 
          `⏰ **ویدیو حذف شد.**\nبرای دانلود مجدد، روی دکمه زیر کلیک کنید.`,
          { reply_markup: keyboard }
        );
      } catch (error) {
        console.error('Error in schedule delete:', error);
      }
    }, video.delete_time * 1000);
    
  } catch (error) {
    console.error('Error sending video:', error);
    await telegram.sendMessage(chatId, '❌ خطا در ارسال ویدیو! لطفاً دوباره تلاش کنید.');
  }
}

async function handleCallback(call, telegram, db) {
  const userId = call.from.id;
  const data = call.data;
  
  // Check admin access
  if (data.startsWith('admin_') || data.startsWith('video_') || 
      data.startsWith('manage_') || data.startsWith('set_delete_') || 
      data.startsWith('confirm_delete_') || data.startsWith('get_share_')) {
    if (!CONFIG.ADMIN_IDS.includes(userId)) {
      await telegram.sendRequest('answerCallbackQuery', {
        callback_query_id: call.id,
        text: '⛔ شما دسترسی ادمین ندارید!',
        show_alert: true
      });
      return;
    }
  }
  
  if (data === 'admin_list_videos') {
    const videos = await db.getVideos();
    if (videos.length === 0) {
      await telegram.sendRequest('editMessageText', {
        chat_id: call.message.chat.id,
        message_id: call.message.message_id,
        text: '📋 **هیچ ویدیویی ثبت نشده است!**',
        parse_mode: 'Markdown',
        reply_markup: mainAdminKeyboard()
      });
    } else {
      await telegram.sendRequest('editMessageText', {
        chat_id: call.message.chat.id,
        message_id: call.message.message_id,
        text: '📋 **لیست ویدیوها:**',
        parse_mode: 'Markdown',
        reply_markup: videoListKeyboard(videos)
      });
    }
  }
  
  else if (data.startsWith('video_page_')) {
    const page = parseInt(data.split('_')[2]);
    const videos = await db.getVideos();
    await telegram.sendRequest('editMessageText', {
      chat_id: call.message.chat.id,
      message_id: call.message.message_id,
      text: '📋 **لیست ویدیوها:**',
      parse_mode: 'Markdown',
      reply_markup: videoListKeyboard(videos, page)
    });
  }
  
  else if (data.startsWith('video_detail_')) {
    const videoId = data.replace('video_detail_', '');
    const video = await db.getVideo(videoId);
    
    if (video) {
      const sponsorsList = video.sponsors.length > 0 
        ? video.sponsors.map(s => `• ${s.channel_name} (\`${s.channel_id}\`)`).join('\n')
        : 'هیچ اسپانسری ثبت نشده';
      
      const detailText = `🎬 **جزئیات ویدیو**\n\n📝 **نام:** ${video.name}\n🆔 **شناسه:** \`${video.id}\`\n⏱️ **زمان حذف:** ${video.delete_time} ثانیه\n\n👥 **اسپانسرها:**\n${sponsorsList}`;
      
      await telegram.sendRequest('editMessageText', {
        chat_id: call.message.chat.id,
        message_id: call.message.message_id,
        text: detailText,
        parse_mode: 'Markdown',
        reply_markup: videoDetailKeyboard(videoId)
      });
    }
  }
  
  else if (data.startsWith('get_share_link_')) {
    const videoId = data.replace('get_share_link_', '');
    const shareLink = `https://t.me/${CONFIG.BOT_USERNAME}?start=video_${videoId}`;
    
    await telegram.sendRequest('answerCallbackQuery', {
      callback_query_id: call.id,
      text: '✅ لینک کپی شد!',
      show_alert: true
    });
    
    await telegram.sendMessage(call.message.chat.id, 
      `🔗 **لینک اشتراک ویدیو:**\n\`${shareLink}\``
    );
  }
  
  else if (data === 'admin_back') {
    await telegram.sendRequest('editMessageText', {
      chat_id: call.message.chat.id,
      message_id: call.message.message_id,
      text: '🌟 **پنل مدیریت بات**',
      parse_mode: 'Markdown',
      reply_markup: mainAdminKeyboard()
    });
  }
  
  else if (data.startsWith('check_sponsors_')) {
    const videoId = data.replace('check_sponsors_', '');
    const missingSponsors = await getMissingSponsors(telegram, db, userId, videoId);
    
    if (missingSponsors.length === 0) {
      await telegram.sendRequest('answerCallbackQuery', {
        callback_query_id: call.id,
        text: '✅ عضویت شما تایید شد!',
        show_alert: true
      });
      
      const video = await db.getVideo(videoId);
      if (video) {
        await sendVideoToUser(telegram, db, call.message.chat.id, video, userId);
        await telegram.deleteMessage(call.message.chat.id, call.message.message_id);
      }
    } else {
      await telegram.sendRequest('answerCallbackQuery', {
        callback_query_id: call.id,
        text: '❌ هنوز در همه کانال‌ها عضو نیستید!',
        show_alert: true
      });
      
      await telegram.sendRequest('editMessageReplyMarkup', {
        chat_id: call.message.chat.id,
        message_id: call.message.message_id,
        reply_markup: sponsorCheckKeyboard(videoId, missingSponsors)
      });
    }
  }
  
  else if (data.startsWith('verify_membership_')) {
    const videoId = data.replace('verify_membership_', '');
    const missingSponsors = await getMissingSponsors(telegram, db, userId, videoId);
    
    if (missingSponsors.length === 0) {
      const video = await db.getVideo(videoId);
      if (video) {
        await sendVideoToUser(telegram, db, call.message.chat.id, video, userId);
        await telegram.deleteMessage(call.message.chat.id, call.message.message_id);
      }
    } else {
      await telegram.sendRequest('answerCallbackQuery', {
        callback_query_id: call.id,
        text: '❌ هنوز در همه کانال‌ها عضو نیستید!',
        show_alert: true
      });
    }
  }
  
  // Acknowledge callback
  await telegram.sendRequest('answerCallbackQuery', {
    callback_query_id: call.id
  });
}

// ==================== MAIN WORKER ====================
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const telegram = new TelegramAPI(CONFIG.TOKEN);
    const db = new Database(env.DB);
    
    // Auto-setup database on first request
    const dbSetup = await db.getSetting('db_initialized');
    if (!dbSetup) {
      await setupDatabase(env.DB);
      await db.setSetting('db_initialized', 'true');
    }
    
    // Panel routes
    if (url.pathname === '/panel' || url.pathname === '/panel/') {
      return new Response(PANEL_HTML.replace(/\$\{CONFIG\.BOT_USERNAME\}/g, CONFIG.BOT_USERNAME), {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      });
    }
    
    // Panel API routes
    if (url.pathname === '/panel/api/stats') {
      const users = await db.getTotalUsers();
      const videos = await db.getTotalVideos();
      const sponsors = await db.getTotalSponsors();
      const botStatus = await db.getSetting('bot_status');
      const webhookUrl = await db.getSetting('webhook_url');
      const webhookInfo = await telegram.getWebhookInfo();
      
      return new Response(JSON.stringify({
        users,
        videos,
        sponsors,
        botStatus: botStatus === 'active',
        webhookUrl: webhookUrl || `${url.origin}${CONFIG.WEBHOOK_PATH}`,
        webhookSet: webhookInfo.result && webhookInfo.result.url ? true : false
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (url.pathname === '/panel/api/toggle-bot') {
      const body = await request.json();
      const action = body.action;
      
      await db.setSetting('bot_status', action === 'start' ? 'active' : 'inactive');
      
      return new Response(JSON.stringify({ success: true }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (url.pathname === '/panel/api/setup-webhook') {
      const webhookUrl = `${url.origin}${CONFIG.WEBHOOK_PATH}`;
      const result = await telegram.setWebhook(webhookUrl);
      await db.setSetting('webhook_url', webhookUrl);
      
      return new Response(JSON.stringify(result), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (url.pathname === '/panel/api/setup-database') {
      try {
        const success = await setupDatabase(env.DB);
        if (success) {
          return new Response(JSON.stringify({ success: true }), {
            headers: { 'Content-Type': 'application/json' }
          });
        } else {
          return new Response(JSON.stringify({ success: false, error: 'Database setup failed' }), {
            headers: { 'Content-Type': 'application/json' }
          });
        }
      } catch (error) {
        return new Response(JSON.stringify({ success: false, error: error.message }), {
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // Webhook route
    if (url.pathname === CONFIG.WEBHOOK_PATH) {
      const botStatus = await db.getSetting('bot_status');
      
      if (botStatus !== 'active') {
        return new Response('Bot is inactive', { status: 503 });
      }
      
      try {
        const update = await request.json();
        
        if (update.message) {
          const message = update.message;
          
          if (message.text && message.text.startsWith('/start')) {
            await handleStart(message, telegram, db);
          } else if (message.chat.type === 'private' && CONFIG.ADMIN_IDS.includes(message.from.id)) {
            await telegram.sendMessage(message.chat.id, '🌟 **پنل مدیریت بات**', {
              reply_markup: mainAdminKeyboard()
            });
          }
        }
        
        if (update.callback_query) {
          await handleCallback(update.callback_query, telegram, db);
        }
        
        return new Response('OK', { status: 200 });
      } catch (error) {
        console.error('Error processing update:', error);
        return new Response('Error', { status: 500 });
      }
    }
    
    // Auto-setup webhook on root request
    if (url.pathname === '/') {
      const webhookUrl = `${url.origin}${CONFIG.WEBHOOK_PATH}`;
      await telegram.setWebhook(webhookUrl);
      await db.setSetting('webhook_url', webhookUrl);
      
      return new Response(JSON.stringify({
        message: 'Bot is running!',
        panel: `${url.origin}/panel`,
        webhook: webhookUrl
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  }
};
