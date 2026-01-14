# Инструкция по развертыванию бота на сервере

## Автоматическое развертывание

### Вариант 1: С использованием sshpass (автоматический ввод пароля)

1. Установите sshpass:
   ```bash
   brew install hudochenkov/sshpass/sshpass  # macOS
   # или
   sudo apt-get install sshpass  # Linux
   ```

2. Запустите скрипт развертывания:
   ```bash
   ./deploy.sh
   ```

### Вариант 2: Ручной ввод пароля

Запустите скрипт, который будет запрашивать пароль:
```bash
./deploy_manual.sh
```

## Ручное развертывание

Если автоматические скрипты не работают, выполните следующие шаги вручную:

### 1. Подключитесь к серверу

```bash
ssh root@185.28.85.26
```

### 2. Установите зависимости системы

```bash
apt-get update
apt-get install -y python3-pip python3-venv git
```

### 3. Клонируйте репозиторий

```bash
mkdir -p /opt/trololobot
cd /opt/trololobot
git clone https://github.com/AlexDevyatov/TrololoBot .
```

### 4. Создайте виртуальное окружение и установите зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Создайте файл creds.txt

```bash
cat > creds.txt << EOF
DEEPSEEK_API_KEY=sk-c9cf0ffdff5c4b52a3e1914efa7a60c4
BOT_TOKEN=8435167940:AAE7oJILEqazeum5e6WJLsqKzO2eihAJ2is
EOF
```

### 6. Создайте systemd service

```bash
cat > /etc/systemd/system/trololobot.service << 'EOF'
[Unit]
Description=Telegram TrololoBot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trololobot
Environment="PATH=/opt/trololobot/venv/bin"
ExecStart=/opt/trololobot/venv/bin/python /opt/trololobot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 7. Запустите сервис

```bash
systemctl daemon-reload
systemctl enable trololobot
systemctl start trololobot
```

### 8. Проверьте статус

```bash
systemctl status trololobot
```

## Просмотр логов

```bash
# Просмотр логов в реальном времени
journalctl -u trololobot -f

# Просмотр последних 100 строк
journalctl -u trololobot -n 100

# Просмотр логов за сегодня
journalctl -u trololobot --since today
```

## Управление сервисом

```bash
# Остановить бота
systemctl stop trololobot

# Запустить бота
systemctl start trololobot

# Перезапустить бота
systemctl restart trololobot

# Проверить статус
systemctl status trololobot
```

## Обновление бота

```bash
cd /opt/trololobot
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart trololobot
```

