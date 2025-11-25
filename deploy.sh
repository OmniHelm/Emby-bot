#!/bin/bash

# EmbyBot 一键部署脚本 (Docker 版)
# 用于交互式配置并部署项目

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# 读取用户输入，支持默认值
read_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_password="${4:-false}"

    if [ -n "$default" ]; then
        prompt="$prompt [默认: $default]"
    fi

    if [ "$is_password" = "true" ]; then
        read -s -p "$prompt: " input
        echo ""
    else
        read -p "$prompt: " input
    fi

    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi

    eval "$var_name='$input'"
}

# 读取是否选项
read_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    local var_name="$3"

    local default_hint="[y/N]"
    if [ "$default" = "y" ]; then
        default_hint="[Y/n]"
    fi

    read -p "$prompt $default_hint: " answer

    if [ -z "$answer" ]; then
        answer="$default"
    fi

    case "$answer" in
        [Yy]* ) eval "$var_name=true";;
        * ) eval "$var_name=false";;
    esac
}

# 读取数组输入
read_array() {
    local prompt="$1"
    local var_name="$2"
    local example="$3"

    echo "$prompt"
    if [ -n "$example" ]; then
        echo "  示例: $example"
    fi
    echo "  输入多个值请用逗号分隔，回车跳过"
    read -p "  > " input

    if [ -z "$input" ]; then
        eval "$var_name='[]'"
    else
        # 将逗号分隔的字符串转换为 JSON 数组
        IFS=',' read -ra items <<< "$input"
        local json_array="["
        local first=true
        for item in "${items[@]}"; do
            item=$(echo "$item" | xargs) # 去除前后空格
            if [ "$first" = true ]; then
                first=false
            else
                json_array+=","
            fi
            # 判断是否为数字
            if [[ "$item" =~ ^-?[0-9]+$ ]]; then
                json_array+="$item"
            else
                json_array+="\"$item\""
            fi
        done
        json_array+="]"
        eval "$var_name='$json_array'"
    fi
}

# 验证必填项
validate_required() {
    local value="$1"
    local field_name="$2"

    if [ -z "$value" ]; then
        print_error "$field_name 不能为空!"
        return 1
    fi
    return 0
}

# 主函数
main() {
    clear
    print_header "EmbyBot 一键部署脚本 (Docker)"

    print_info "此脚本将引导你完成 EmbyBot 的配置和 Docker 部署"
    print_info "按 Ctrl+C 可随时退出"
    echo ""

    # 检查 Docker 是否安装
    if ! command -v docker &> /dev/null; then
        print_error "未检测到 Docker，请先安装 Docker"
        print_info "安装命令: curl -fsSL https://get.docker.com | bash"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "未检测到 Docker Compose"
        print_info "请安装 Docker Compose 或使用 Docker 内置的 compose 插件"
        exit 1
    fi

    # 检查是否已存在配置文件
    if [ -f "config.json" ]; then
        print_warning "检测到已存在 config.json 文件"
        read_yes_no "是否备份现有配置并重新生成？" "n" BACKUP_CONFIG
        if [ "$BACKUP_CONFIG" = true ]; then
            backup_file="config.json.backup.$(date +%Y%m%d_%H%M%S)"
            cp config.json "$backup_file"
            print_success "已备份到: $backup_file"
        else
            print_info "已取消部署"
            exit 0
        fi
    fi

    # ==================== 基础配置 ====================
    print_header "第 1 步: 基础配置"

    while true; do
        read_input "Bot 名称" "EmbyBot" BOT_NAME
        validate_required "$BOT_NAME" "Bot 名称" && break
    done

    while true; do
        read_input "Bot Token (从 @BotFather 获取)" "" BOT_TOKEN
        validate_required "$BOT_TOKEN" "Bot Token" && break
    done

    while true; do
        read_input "Telegram API ID (从 https://my.telegram.org 获取)" "" OWNER_API
        validate_required "$OWNER_API" "Telegram API ID" && break
    done

    while true; do
        read_input "Telegram API Hash" "" OWNER_HASH
        validate_required "$OWNER_HASH" "Telegram API Hash" && break
    done

    while true; do
        read_input "拥有者 Telegram ID (你的数字 ID)" "" OWNER
        validate_required "$OWNER" "拥有者 ID" && break
    done

    # ==================== Emby 服务器配置 ====================
    print_header "第 2 步: Emby 服务器配置"

    while true; do
        read_input "Emby 服务器 URL" "http://localhost:8096" EMBY_URL
        validate_required "$EMBY_URL" "Emby URL" && break
    done

    while true; do
        read_input "Emby API Key (从 Emby 控制台获取)" "" EMBY_API
        validate_required "$EMBY_API" "Emby API Key" && break
    done

    read_input "Emby 访问线路域名 (用于显示给用户)" "emby.example.com" EMBY_LINE
    read_input "白名单用户专用线路 (可选，留空则与普通线路相同)" "" EMBY_WHITELIST_LINE

    # ==================== 数据库配置 ====================
    print_header "第 3 步: 数据库配置"

    print_info "Docker 模式下，建议使用 docker-compose.yml 中的 MySQL 配置"
    read_input "数据库主机" "mysql" DB_HOST
    read_input "数据库端口" "3306" DB_PORT
    read_input "数据库用户名" "susu" DB_USER
    read_input "数据库密码" "1234" DB_PWD true
    read_input "数据库名称" "embybot" DB_NAME
    read_input "MySQL Docker 容器名称" "mysql" DB_DOCKER_NAME

    # ==================== 群组和频道配置 ====================
    print_header "第 4 步: 群组和频道配置"

    read_array "管理群组 ID 列表 (可选)" GROUP_ARRAY "-1001234567890,-1009876543210"
    if [ "$GROUP_ARRAY" = "[]" ]; then
        GROUP_ARRAY="[]"
    fi

    read_input "主群组用户名 (可选，不含 @)" "" MAIN_GROUP
    read_input "公告频道用户名 (可选，不含 @)" "" CHANEL
    read_input "Bot 头像 URL (可选)" "" BOT_PHOTO

    # ==================== 货币和开放功能配置 ====================
    print_header "第 5 步: 功能配置"

    read_input "虚拟货币名称" "花币" MONEY

    print_info "开放功能配置："
    read_yes_no "  启用签到功能？" "y" OPEN_CHECKIN
    read_yes_no "  启用兑换码功能？" "y" OPEN_EXCHANGE
    read_yes_no "  启用白名单申请？" "y" OPEN_WHITELIST
    read_yes_no "  启用邀请功能？" "n" OPEN_INVITE
    read_yes_no "  退群后封禁用户？" "y" OPEN_LEAVE_BAN
    read_yes_no "  显示播放记录统计？" "y" OPEN_UPLAYS

    if [ "$OPEN_EXCHANGE" = true ]; then
        read_input "兑换码花费" "100" EXCHANGE_COST
    else
        EXCHANGE_COST=100
    fi

    if [ "$OPEN_WHITELIST" = true ]; then
        read_input "白名单申请花费" "9999" WHITELIST_COST
    else
        WHITELIST_COST=9999
    fi

    if [ "$OPEN_INVITE" = true ]; then
        read_input "邀请功能花费" "1000" INVITE_COST
    else
        INVITE_COST=1000
    fi

    # ==================== 定时任务配置 ====================
    print_header "第 6 步: 定时任务配置"

    print_info "定时任务开关："
    read_yes_no "  启用日榜生成？" "y" SCHED_DAYRANK
    read_yes_no "  启用周榜生成？" "y" SCHED_WEEKRANK
    read_yes_no "  启用到期检测？" "y" SCHED_CHECK_EX
    read_yes_no "  启用低活跃度检测？" "n" SCHED_LOW_ACTIVITY
    read_yes_no "  启用数据库备份？" "n" SCHED_BACKUP_DB

    if [ "$SCHED_BACKUP_DB" = true ]; then
        read_input "数据库备份目录" "./db_backup" DB_BACKUP_DIR
        read_input "备份保留份数" "7" DB_BACKUP_MAXCOUNT
    else
        DB_BACKUP_DIR="./db_backup"
        DB_BACKUP_MAXCOUNT=7
    fi

    # ==================== API 服务配置 ====================
    print_header "第 7 步: Web API 配置"

    read_yes_no "是否启用 Web API 服务？" "y" API_STATUS
    if [ "$API_STATUS" = true ]; then
        read_input "API 监听地址" "0.0.0.0" API_HOST
        read_input "API 监听端口" "8838" API_PORT
    else
        API_HOST="0.0.0.0"
        API_PORT=8838
    fi

    # ==================== 高级配置 ====================
    print_header "第 8 步: 高级配置 (可选)"

    read_yes_no "是否配置 MoviePilot 集成？" "n" CONFIG_MOVIEPILOT
    if [ "$CONFIG_MOVIEPILOT" = true ]; then
        read_input "MoviePilot 服务地址 (如 http://192.168.1.100:3000)" "" MP_URL
        read_input "MoviePilot 用户名" "" MP_USERNAME
        read_input "MoviePilot 密码" "" MP_PASSWORD true
        read_input "电影请求花费 (虚拟货币)" "1" MP_PRICE
        read_input "求片通知群组 ID (可选，留空则使用第一个授权群组)" "" MP_REQUEST_CHATID
        read_input "下载日志群组 ID (可选)" "" MP_DOWNLOAD_CHATID
        read_input "求片用户默认等级 (a=白名单/b=正常/c=临时)" "b" MP_LV
        MP_STATUS=true
    else
        MP_STATUS=false
        MP_URL=""
        MP_USERNAME=""
        MP_PASSWORD=""
        MP_PRICE=1
        MP_REQUEST_CHATID=""
        MP_DOWNLOAD_CHATID=""
        MP_LV="b"
    fi

    read_yes_no "是否配置代理？" "n" CONFIG_PROXY
    if [ "$CONFIG_PROXY" = true ]; then
        read_input "代理协议 (socks5/http)" "socks5" PROXY_SCHEME
        read_input "代理地址" "127.0.0.1" PROXY_HOSTNAME
        read_input "代理端口" "1080" PROXY_PORT
        read_input "代理用户名 (可选)" "" PROXY_USERNAME
        read_input "代理密码 (可选)" "" PROXY_PASSWORD true
    else
        PROXY_SCHEME=""
        PROXY_HOSTNAME=""
        PROXY_PORT="null"
        PROXY_USERNAME=""
        PROXY_PASSWORD=""
    fi

    read_yes_no "是否启用自动更新？" "y" AUTO_UPDATE

    print_info "高级功能配置："
    read_yes_no "  启用红包功能？" "y" RED_ENVELOPE_STATUS
    if [ "$RED_ENVELOPE_STATUS" = true ]; then
        read_yes_no "  允许专属红包？" "y" RED_ENVELOPE_PRIVATE
    else
        RED_ENVELOPE_PRIVATE=true
    fi

    read_input "活跃度检测天数" "21" ACTIVITY_CHECK_DAYS
    read_input "账号封存天数 (不活跃后)" "5" FREEZE_DAYS
    read_input "/kk 指令赠送资格天数" "30" KK_GIFT_DAYS
    read_yes_no "是否狙杀皮套人？" "y" FUXX_PITAO

    # ==================== 生成配置文件 ====================
    print_header "生成配置文件"

    print_info "正在生成 config.json..."

    # 处理可选的字符串字段
    if [ -z "$MAIN_GROUP" ]; then
        MAIN_GROUP_JSON="null"
    else
        MAIN_GROUP_JSON="\"$MAIN_GROUP\""
    fi

    if [ -z "$CHANEL" ]; then
        CHANEL_JSON="null"
    else
        CHANEL_JSON="\"$CHANEL\""
    fi

    if [ -z "$BOT_PHOTO" ]; then
        BOT_PHOTO_JSON="null"
    else
        BOT_PHOTO_JSON="\"$BOT_PHOTO\""
    fi

    if [ -z "$EMBY_WHITELIST_LINE" ]; then
        EMBY_WHITELIST_LINE_JSON="null"
    else
        EMBY_WHITELIST_LINE_JSON="\"$EMBY_WHITELIST_LINE\""
    fi

    # MoviePilot 配置
    if [ "$MP_STATUS" = true ]; then
        MP_URL_JSON="\"$MP_URL\""
        MP_USERNAME_JSON="\"$MP_USERNAME\""
        MP_PASSWORD_JSON="\"$MP_PASSWORD\""

        # 处理可选的 chatid 字段
        if [ -z "$MP_REQUEST_CHATID" ]; then
            MP_REQUEST_CHATID_JSON="null"
        else
            MP_REQUEST_CHATID_JSON="$MP_REQUEST_CHATID"
        fi

        if [ -z "$MP_DOWNLOAD_CHATID" ]; then
            MP_DOWNLOAD_CHATID_JSON="null"
        else
            MP_DOWNLOAD_CHATID_JSON="$MP_DOWNLOAD_CHATID"
        fi

        MP_LV_JSON="\"$MP_LV\""
    else
        MP_URL_JSON="\"\""
        MP_USERNAME_JSON="\"\""
        MP_PASSWORD_JSON="\"\""
        MP_REQUEST_CHATID_JSON="null"
        MP_DOWNLOAD_CHATID_JSON="null"
        MP_LV_JSON="\"b\""
    fi

    # 代理配置
    if [ -z "$PROXY_SCHEME" ]; then
        PROXY_SCHEME_JSON="\"\""
        PROXY_HOSTNAME_JSON="\"\""
        PROXY_PORT_JSON="null"
        PROXY_USERNAME_JSON="\"\""
        PROXY_PASSWORD_JSON="\"\""
    else
        PROXY_SCHEME_JSON="\"$PROXY_SCHEME\""
        PROXY_HOSTNAME_JSON="\"$PROXY_HOSTNAME\""
        PROXY_PORT_JSON="$PROXY_PORT"
        if [ -z "$PROXY_USERNAME" ]; then
            PROXY_USERNAME_JSON="\"\""
        else
            PROXY_USERNAME_JSON="\"$PROXY_USERNAME\""
        fi
        if [ -z "$PROXY_PASSWORD" ]; then
            PROXY_PASSWORD_JSON="\"\""
        else
            PROXY_PASSWORD_JSON="\"$PROXY_PASSWORD\""
        fi
    fi

    # 生成 JSON 配置
    cat > config.json <<EOF
{
  "bot_name": "$BOT_NAME",
  "bot_token": "$BOT_TOKEN",
  "owner_api": $OWNER_API,
  "owner_hash": "$OWNER_HASH",
  "owner": $OWNER,
  "group": $GROUP_ARRAY,
  "main_group": $MAIN_GROUP_JSON,
  "chanel": $CHANEL_JSON,
  "bot_photo": $BOT_PHOTO_JSON,
  "admins": [],
  "credits_name": "$MONEY",
  "emby_api": "$EMBY_API",
  "emby_url": "$EMBY_URL",
  "emby_line": "$EMBY_LINE",
  "emby_whitelist_line": $EMBY_WHITELIST_LINE_JSON,
  "blocked_clients": [
    ".*curl.*",
    ".*wget.*",
    ".*python.*",
    ".*bot.*",
    ".*spider.*",
    ".*crawler.*",
    ".*scraper.*",
    ".*downloader.*",
    ".*aria2.*",
    ".*youtube-dl.*",
    ".*yt-dlp.*",
    ".*ffmpeg.*",
    ".*vlc.*"
  ],
  "client_filter_terminate_session": true,
  "client_filter_block_user": false,
  "db_host": "$DB_HOST",
  "db_user": "$DB_USER",
  "db_pwd": "$DB_PWD",
  "db_name": "$DB_NAME",
  "db_port": $DB_PORT,
  "emby_block": [
    "nsfw"
  ],
  "extra_emby_libs": [
    "电视"
  ],
  "open": {
    "stat": false,
    "open_us": 30,
    "all_user": 1000,
    "timing": 0,
    "tem": 0,
    "checkin": $OPEN_CHECKIN,
    "exchange": $OPEN_EXCHANGE,
    "whitelist": $OPEN_WHITELIST,
    "invite": $OPEN_INVITE,
    "invite_lv": "b",
    "leave_ban": $OPEN_LEAVE_BAN,
    "uplays": $OPEN_UPLAYS,
    "checkin_reward": [1, 10],
    "exchange_cost": $EXCHANGE_COST,
    "whitelist_cost": $WHITELIST_COST,
    "invite_cost": $INVITE_COST
  },
  "tz_ad": "",
  "tz_api": "",
  "tz_id": [],
  "ranks": {
    "logo": "EmbyBot",
    "backdrop": false
  },
  "schedall": {
    "dayrank": $SCHED_DAYRANK,
    "weekrank": $SCHED_WEEKRANK,
    "dayplayrank": false,
    "weekplayrank": false,
    "check_ex": $SCHED_CHECK_EX,
    "low_activity": $SCHED_LOW_ACTIVITY,
    "backup_db": $SCHED_BACKUP_DB
  },
  "db_is_docker": true,
  "db_docker_name": "$DB_DOCKER_NAME",
  "db_backup_dir": "$DB_BACKUP_DIR",
  "db_backup_maxcount": $DB_BACKUP_MAXCOUNT,
  "kk_gift_days": $KK_GIFT_DAYS,
  "fuxx_pitao": $FUXX_PITAO,
  "activity_check_days": $ACTIVITY_CHECK_DAYS,
  "freeze_days": $FREEZE_DAYS,
  "w_anti_channel_ids": [],
  "proxy": {
    "scheme": $PROXY_SCHEME_JSON,
    "hostname": $PROXY_HOSTNAME_JSON,
    "port": $PROXY_PORT_JSON,
    "username": $PROXY_USERNAME_JSON,
    "password": $PROXY_PASSWORD_JSON
  },
  "moviepilot": {
    "status": $MP_STATUS,
    "url": $MP_URL_JSON,
    "username": $MP_USERNAME_JSON,
    "password": $MP_PASSWORD_JSON,
    "access_token": "",
    "price": $MP_PRICE,
    "download_log_chatid": $MP_DOWNLOAD_CHATID_JSON,
    "movie_request_chatid": $MP_REQUEST_CHATID_JSON,
    "lv": $MP_LV_JSON
  },
  "auto_update": {
    "status": $AUTO_UPDATE,
    "git_repo": "OmniHelm/Emby-bot",
    "commit_sha": null
  },
  "red_envelope": {
    "status": $RED_ENVELOPE_STATUS,
    "allow_private": $RED_ENVELOPE_PRIVATE
  },
  "api": {
    "status": $API_STATUS,
    "http_url": "$API_HOST",
    "http_port": $API_PORT,
    "allow_origins": [
      "*"
    ]
  }
}
EOF

    print_success "配置文件已生成: config.json"

    # ==================== 部署 ====================
    print_header "开始部署"

    # 检查是否使用 docker-compose 或 docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    read_yes_no "是否现在启动 Docker 服务？" "y" START_DOCKER

    if [ "$START_DOCKER" = true ]; then
        print_info "正在启动 Docker 服务..."

        # 创建必要的目录
        mkdir -p log

        # 启动服务
        $COMPOSE_CMD up -d

        print_success "Docker 服务已启动"
    fi

    # ==================== 完成 ====================
    print_header "部署完成"

    print_success "EmbyBot 配置已完成！"
    echo ""
    print_info "重要提示："
    echo "  1. 配置文件位置: ./config.json"
    echo "  2. 日志目录: ./log"
    echo "  3. 管理命令:"
    echo "     - 查看日志: $COMPOSE_CMD logs -f embybot"
    echo "     - 重启服务: $COMPOSE_CMD restart embybot"
    echo "     - 停止服务: $COMPOSE_CMD down"
    echo "     - 更新镜像: $COMPOSE_CMD pull && $COMPOSE_CMD up -d"
    if [ "$API_STATUS" = true ]; then
        echo "  4. API 访问地址: http://$API_HOST:$API_PORT"
    fi
    echo ""
    print_info "遇到问题？查看文档: https://github.com/OmniHelm/Emby-bot"
    echo ""
}

# 运行主函数
main
