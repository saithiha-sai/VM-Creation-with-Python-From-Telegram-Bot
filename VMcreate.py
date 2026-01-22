import telebot
import spacy
import paramiko
import re
import time

# Load NLP
nlp = spacy.load("en_core_web_sm")

# Telegram Bot Token
bot = telebot.TeleBot("8070703754:AAFtWrztBwTy-A7zp7RC_OPOGPQAK_OI__A")

# Temporary user data store
user_data = {}

def detect_create_vm(text):
    doc = nlp(text.lower())
    return "create" in [token.lemma_ for token in doc] and "vm" in [token.text for token in doc]

def escape_markdown_v2(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if detect_create_vm(text):
        user_data[chat_id] = {}
        bot.send_message(chat_id, "🖥️ What is the VM name?")
        bot.register_next_step_handler(message, ask_cpu)
    else:
        bot.send_message(chat_id, "❓ Please type something like 'Create VM' to begin.")

def ask_cpu(message):
    chat_id = message.chat.id
    user_data[chat_id]['vm_name'] = message.text.strip()
    bot.send_message(chat_id, "💽 How many vCPUs?")
    bot.register_next_step_handler(message, ask_ram)

def ask_ram(message):
    chat_id = message.chat.id
    try:
        cpu_count = int(message.text.strip())
    except ValueError:
        bot.send_message(chat_id, "⚠️ Please enter a valid number for vCPUs.")
        bot.register_next_step_handler(message, ask_ram)
        return

    user_data[chat_id]['cpu'] = cpu_count
    bot.send_message(chat_id, "🧠 Enter RAM (e.g., 2G):")
    bot.register_next_step_handler(message, ask_hdd)

def ask_hdd(message):
    chat_id = message.chat.id
    ram_input = message.text.strip().lower()
    ram_gb_match = re.findall(r'\d+', ram_input)
    if not ram_gb_match:
        bot.send_message(chat_id, "⚠️ Please enter RAM like '2G'. Try again:")
        bot.register_next_step_handler(message, ask_hdd)
        return

    ram_gb = int(ram_gb_match[0])
    user_data[chat_id]['ram'] = ram_gb * 1024
    bot.send_message(chat_id, "📦 Enter HDD size (e.g., 20G):")
    bot.register_next_step_handler(message, ask_iso)

def ask_iso(message):
    chat_id = message.chat.id
    hdd_input = message.text.strip().lower()
    hdd_gb_match = re.findall(r'\d+', hdd_input)
    if not hdd_gb_match:
        bot.send_message(chat_id, "⚠️ Please enter HDD size like '20G'. Try again:")
        bot.register_next_step_handler(message, ask_iso)
        return

    hdd_gb = int(hdd_gb_match[0])
    user_data[chat_id]['hdd'] = f"{hdd_gb}G"
    bot.send_message(chat_id, "📁 Enter ISO filename (e.g., rhel-9.5-x86_64-dvd.iso):")
    bot.register_next_step_handler(message, finalize_creation)

def finalize_creation(message):
    chat_id = message.chat.id
    iso_filename = message.text.strip()
    if not iso_filename.lower().endswith('.iso'):
        bot.send_message(chat_id, "⚠️ Please enter a valid ISO filename ending with '.iso'. Try again:")
        bot.register_next_step_handler(message, finalize_creation)
        return

    user_data[chat_id]['iso'] = iso_filename
    data = user_data[chat_id]
    iso_path = f"/vmfs/volumes/datastore1/iso/{data['iso']}"  # FULL PATH ISO

    cpu = data['cpu']
    if cpu <= 2:
        cores_per_socket = 1
    elif cpu in [4, 8]:
        cores_per_socket = cpu // 2
    else:
        cores_per_socket = 1

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("172.24.169.97", port=22, username="root", password="asd123!@#")

        vm_path = f"/vmfs/volumes/datastore1/{data['vm_name']}"
        vmx_path = f"{vm_path}/{data['vm_name']}.vmx"
        vmdk_path = f"{vm_path}/{data['vm_name']}.vmdk"

        ssh.exec_command(f"mkdir -p {vm_path}")
        time.sleep(1)

        ssh.exec_command(f"vmkfstools -c {data['hdd']} -a lsilogic {vmdk_path}")
        time.sleep(1)

        vmx_content = f""".encoding = "UTF-8"
config.version = "8"
virtualHW.version = "13"
displayName = "{data['vm_name']}"
memsize = "{data['ram']}"
numvcpus = "{cpu}"
cpuid.coresPerSocket = "{cores_per_socket}"
guestOS = "rhel7_64Guest"

sata0.present = "TRUE"
sata0:0.present = "TRUE"
sata0:0.fileName = "{iso_path}"
sata0:0.deviceType = "cdrom-image"
sata0:0.clientDevice = "FALSE"
sata0:0.startConnected = "TRUE"

scsi0.present = "TRUE"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "{data['vm_name']}.vmdk"
scsi0:0.deviceType = "scsi-hardDisk"

ethernet0.present = "TRUE"
ethernet0.connectionType = "network"
ethernet0.networkName = "LAN"
ethernet0.virtualDev = "e1000"
ethernet0.startConnected = "FALSE"

bios.bootOrder = "sata0"

mem.hotadd = "TRUE"
vcpu.hotadd = "TRUE"
svga.present = "TRUE"
tools.syncTime = "TRUE"
"""

        escaped_vmx = vmx_content.replace('"', '\\"').replace('$', '\\$').replace('\n', '\\n')
        cmd_write_vmx = f'echo -e "{vmx_content}" > {vmx_path}'
        ssh.exec_command(cmd_write_vmx)
        time.sleep(1)

        stdin, stdout, stderr = ssh.exec_command(f"vim-cmd solo/registervm {vmx_path}")
        vm_id = stdout.read().decode().strip()
        time.sleep(1)

        ssh.exec_command(f"vim-cmd vmsvc/power.on {vm_id}")
        ssh.close()

        try:
            bot.send_message(chat_id,
                f"✅ VM *{escape_markdown_v2(data['vm_name'])}* created successfully!\n"
                f"CPU: {cpu} (Cores/Socket: {cores_per_socket})\n"
                f"RAM: {data['ram']} MB\n"
                f"HDD: {data['hdd']}\n"
                f"ISO: {escape_markdown_v2(data['iso'])}",
                parse_mode="MarkdownV2")
        except Exception:
            bot.send_message(chat_id,
                f"✅ VM {data['vm_name']} created successfully!\n"
                f"CPU: {cpu} (Cores/Socket: {cores_per_socket})\n"
                f"RAM: {data['ram']} MB\n"
                f"HDD: {data['hdd']}\n"
                f"ISO: {data['iso']}")

    except Exception as e:
        bot.send_message(chat_id, f"❌ VM creation failed:\n{str(e)}")

    if chat_id in user_data:
        del user_data[chat_id]

bot.infinity_polling()
