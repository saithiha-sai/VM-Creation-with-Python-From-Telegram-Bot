# Telegram ESXi VM Creation Bot – README

## Overview

This Python script implements a **Telegram chatbot** that allows users to **create VMware ESXi virtual machines using natural language commands**.

The bot uses **spaCy NLP** to detect VM creation intent, collects VM specifications step-by-step via Telegram chat, and then **connects to an ESXi host over SSH** to create, register, and power on the virtual machine automatically.

This solution is well-suited for **infrastructure automation**, **self-service VM provisioning**, and **core banking / enterprise virtualization environments**.

---

## Key Features

* Natural language VM creation trigger (e.g., *"Create VM"*)
* Step-by-step interactive VM specification via Telegram
* Flexible input handling for CPU, RAM, and HDD
* Automatic VMX and VMDK creation on ESXi
* VM registration and power-on
* SSH-based ESXi control (no vCenter required)
* Markdown-safe Telegram responses

---

## Technologies Used

* **Python**
* **Telegram Bot API (telebot / PyTelegramBotAPI)**
* **spaCy NLP** – command intent detection
* **Paramiko** – SSH connection to ESXi
* **VMware ESXi CLI tools** (`vmkfstools`, `vim-cmd`)

---

## Prerequisites

* Python 3.8+
* VMware ESXi host with SSH enabled
* Telegram bot token
* spaCy English language model

Install dependencies:

```bash
pip install pytelegrambotapi spacy paramiko
python -m spacy download en_core_web_sm
```

---

## Configuration

### 1. Telegram Bot Token

```python
bot = telebot.TeleBot("<YOUR_TELEGRAM_BOT_TOKEN>")
```

---

### 2. ESXi Host Access

```python
ssh.connect(
    "172.24.169.97",
    port=22,
    username="root",
    password="<PASSWORD>"
)
```

> ⚠️ **Security Note:** Use SSH keys or environment variables in production.

---

### 3. ISO Storage Path

```python
iso_path = "/vmfs/volumes/datastore1/iso/<ISO_NAME>.iso"
```

Ensure the ISO file exists on the datastore.

---

## Bot Workflow

### Step 1: Command Detection

The bot uses spaCy NLP to detect VM creation intent:

* Keywords: `create` + `vm`

---

### Step 2: User Interaction Flow

The bot sequentially asks for:

1. VM Name
2. vCPU count
3. RAM size (e.g., `2G`)
4. HDD size (e.g., `20G`)
5. ISO filename

All inputs are validated before proceeding.

---

### Step 3: VM Provisioning on ESXi

Once all inputs are collected:

* Creates VM directory
* Creates VMDK disk using `vmkfstools`
* Generates `.vmx` configuration file
* Registers VM with ESXi
* Powers on the VM

---

## VM Configuration Logic

### CPU & Cores per Socket

```text
≤ 2 vCPU   → 1 core/socket
4 or 8     → vCPU ÷ 2 cores/socket
Others     → 1 core/socket
```

### RAM Conversion

* User input in GB is converted to MB automatically

---

## Example Telegram Interaction

```text
User: Create VM
Bot: What is the VM name?
User: TESTVM01
Bot: How many vCPUs?
User: 4
Bot: Enter RAM (e.g., 2G)
User: 8G
Bot: Enter HDD size (e.g., 20G)
User: 40G
Bot: Enter ISO filename
User: rhel-9.5-x86_64-dvd.iso
```

---

## Success Message

The bot returns a confirmation summary:

* VM Name
* CPU and cores per socket
* RAM
* HDD size
* ISO used

---

## Error Handling

* Input validation for CPU, RAM, HDD, and ISO
* SSH connection and command execution errors
* Safe MarkdownV2 escaping for Telegram

---

## Use Cases

* Self-service VM provisioning
* Lab and testing environments
* Core banking infrastructure automation
* DevOps / SRE workflows
* On-demand VM deployment via chat

---

## Limitations

* Single ESXi host support
* Root SSH access required
* No resource availability checks
* No rollback on partial failure

---

## Future Enhancements

* vCenter API integration (pyVmomi)
* Multiple VM creation support
* ISO selection via buttons
* Snapshot and delete VM commands
* Role-based Telegram access control
* Audit logging and approval workflow

---

## Author

**Sai Thiha**
IT System & Automation Engineer

---

✅ This bot enables fast, secure, and user-friendly VM provisioning directly from Telegram.
