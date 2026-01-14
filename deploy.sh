#!/bin/bash

# Скрипт развертывания Telegram бота на сервере

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Читаем данные из creds.txt
if [ ! -f "creds.txt" ]; then
    echo -e "${RED}Ошибка: файл creds.txt не найден${NC}"
    exit 1
fi

# Читаем значения из creds.txt безопасно
SERVER_IP=$(grep "^SERVER_IP=" creds.txt | cut -d'=' -f2)
SERVER_LOGIN=$(grep "^SERVER_LOGIN=" creds.txt | cut -d'=' -f2)
SERVER_PASSWORD=$(grep "^SERVER_PASSWORD=" creds.txt | cut -d'=' -f2)
GIT_REPO=$(grep "^GIT_REPO=" creds.txt | cut -d'=' -f2)

# Значения по умолчанию
SERVER_IP=${SERVER_IP:-"185.28.85.26"}
SERVER_LOGIN=${SERVER_LOGIN:-"root"}
SERVER_PASSWORD=${SERVER_PASSWORD:-""}
GIT_REPO=${GIT_REPO:-"https://github.com/AlexDevyatov/TrololoBot"}
PROJECT_DIR="/opt/trololobot"
SERVICE_NAME="trololobot"

echo -e "${GREEN}Начинаем развертывание бота на сервере...${NC}"

# Функция для выполнения команд на сервере
execute_remote() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        "${SERVER_LOGIN}@${SERVER_IP}" "$1"
}

# Функция для копирования файлов на сервер
copy_to_remote() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        "$1" "${SERVER_LOGIN}@${SERVER_IP}:$2"
}

# Проверяем наличие sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}Установка sshpass...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass || echo -e "${RED}Не удалось установить sshpass. Установите вручную: brew install hudochenkov/sshpass/sshpass${NC}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
fi

echo -e "${GREEN}Подключение к серверу...${NC}"

# Проверяем подключение
if ! execute_remote "echo 'Connection test successful'"; then
    echo -e "${RED}Ошибка: не удалось подключиться к серверу${NC}"
    exit 1
fi

echo -e "${GREEN}Проверка окружения на сервере...${NC}"

# Проверяем Python
execute_remote "python3 --version || (echo 'Python3 не установлен' && exit 1)"

# Устанавливаем зависимости системы
echo -e "${GREEN}Установка системных зависимостей...${NC}"
execute_remote "apt-get update && apt-get install -y python3-pip python3-venv git"

# Создаем директорию проекта
echo -e "${GREEN}Создание директории проекта...${NC}"
execute_remote "mkdir -p $PROJECT_DIR"

# Клонируем или обновляем репозиторий
echo -e "${GREEN}Клонирование/обновление репозитория...${NC}"
execute_remote "
if [ -d \"$PROJECT_DIR/.git\" ]; then
    cd $PROJECT_DIR && git pull
else
    git clone $GIT_REPO $PROJECT_DIR
fi
"

# Создаем виртуальное окружение
echo -e "${GREEN}Настройка виртуального окружения...${NC}"
execute_remote "
cd $PROJECT_DIR
if [ ! -d \"venv\" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
"

# Создаем creds.txt на сервере
echo -e "${GREEN}Создание файла конфигурации на сервере...${NC}"
copy_to_remote "creds.txt" "$PROJECT_DIR/creds.txt"

# Создаем systemd service
echo -e "${GREEN}Создание systemd service...${NC}"
execute_remote "cat > /etc/systemd/system/${SERVICE_NAME}.service << 'EOF'
[Unit]
Description=Telegram TrololoBot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin\"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
"

# Перезагружаем systemd
echo -e "${GREEN}Перезагрузка systemd...${NC}"
execute_remote "systemctl daemon-reload"

# Останавливаем старый сервис, если он запущен
echo -e "${GREEN}Остановка старого сервиса...${NC}"
execute_remote "systemctl stop ${SERVICE_NAME} || true"

# Запускаем сервис
echo -e "${GREEN}Запуск сервиса...${NC}"
execute_remote "systemctl enable ${SERVICE_NAME}"
execute_remote "systemctl start ${SERVICE_NAME}"

# Проверяем статус
echo -e "${GREEN}Проверка статуса сервиса...${NC}"
sleep 3
execute_remote "systemctl status ${SERVICE_NAME} --no-pager -l"

echo -e "${GREEN}Развертывание завершено!${NC}"
echo -e "${YELLOW}Для просмотра логов используйте:${NC}"
echo -e "ssh ${SERVER_LOGIN}@${SERVER_IP} 'journalctl -u ${SERVICE_NAME} -f'"

