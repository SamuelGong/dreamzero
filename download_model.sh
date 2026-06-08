#!/bin/bash

# ================= 配置区域 =================
REPO_ID="Wan-AI/Wan2.1-I2V-14B-480P"
SAVE_DIR="models--Wan-AI--Wan2.1-I2V-14B-480P"
DOMAIN="https://hf-mirror.com"
# ============================================

mkdir -p "$SAVE_DIR"

# 创建两个临时文本作为队列
TODO_LIST="/tmp/hf_todo_$(date +%s).txt"
DONE_LIST="/tmp/hf_done_$(date +%s).txt"
touch "$TODO_LIST" "$DONE_LIST"

# 初始化：将根目录树页面加入待扫描队列
echo "tree/main" > "$TODO_LIST"

echo "正在使用内网安全模式递归扫描 ${REPO_ID} 的完整目录树..."

while [ -s "$TODO_LIST" ]; do
    # 弹出队列第一行
    CURRENT_PATH=$(head -n 1 "$TODO_LIST")
    sed -i '1d' "$TODO_LIST"

    # 去重校验
    if grep -qF "$CURRENT_PATH" "$DONE_LIST"; then continue; fi
    echo "$CURRENT_PATH" >> "$DONE_LIST"

    URL="${DOMAIN}/${REPO_ID}/${CURRENT_PATH}"

    # 抓取网页源码
    HTML=$(curl -k -s -L "$URL")
    if [ -z "$HTML" ]; then continue; fi

    # 通过管道 (<<<) 将 HTML 作为标准输入传入 Python
    PARSE_RESULT=$(python3 -c "
import sys
from html.parser import HTMLParser

repo_id = '$REPO_ID'
dirs = set()
files = set()

class HFParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    dir_prefix = f'/{repo_id}/tree/main/'
                    file_prefix = f'/{repo_id}/resolve/main/'

                    if value.startswith(dir_prefix):
                        sub_dir = value[len(f'/{repo_id}/'):].strip('/')
                        if sub_dir and sub_dir != 'tree/main':
                            dirs.add(sub_dir)
                    elif value.startswith(file_prefix):
                        sub_file = value[len(file_prefix):].strip('/')
                        if sub_file:
                            files.add(sub_file)

parser = HFParser()
parser.feed(sys.stdin.read())

print('DIRS:' + ','.join(dirs))
print('FILES:' + ','.join(files))
" <<< "$HTML")

    # 分离出解析到的文件夹和文件
    DETECTED_DIRS=$(echo "$PARSE_RESULT" | grep '^DIRS:' | cut -d':' -f2 | tr ',' '\n')
    DETECTED_FILES=$(echo "$PARSE_RESULT" | grep '^FILES:' | cut -d':' -f2 | tr ',' '\n')

    # 1. 将新发现的子文件夹塞进待扫描队列
    if [ -n "$DETECTED_DIRS" ]; then
        echo "$DETECTED_DIRS" >> "$TODO_LIST"
    fi

    # 2. 遍历并下载当前层级发现的所有文件
    if [ -n "$DETECTED_FILES" ]; then
        echo "$DETECTED_FILES" | while read -r RAW_FILE_PATH; do
            if [ -z "$RAW_FILE_PATH" ]; then continue; fi

            # 核心修复：切除 URL 中可能包含的 ?download=true 后缀，获取纯净的文件名
            FILE_PATH=$(echo "$RAW_FILE_PATH" | cut -d'?' -f1)

            DOWNLOAD_URL="${DOMAIN}/${REPO_ID}/resolve/main/${RAW_FILE_PATH}"
            TARGET_FILE="${SAVE_DIR}/${FILE_PATH}"
            TARGET_DIR=$(dirname "${TARGET_FILE}")

            # 断点续传去重：若文件已存在且大小不为 0，跳过
            if [ -s "$TARGET_FILE" ]; then
                echo "文件已存在，跳过: ${FILE_PATH}"
                continue
            fi

            mkdir -p "${TARGET_DIR}"
            echo "--------------------------------------------------------"
            echo "正在下载: ${FILE_PATH}"
            echo "--------------------------------------------------------"

            # 依次检测本地下载器
            if command -v aria2c &> /dev/null; then
                aria2c --check-certificate=false \
                       -x 16 \
                       -s 16 \
                       -j 4 \
                       -c \
                       -d "${TARGET_DIR}" \
                       -o "$(basename "${FILE_PATH}")" \
                       "${DOWNLOAD_URL}"
            elif command -v wget &> /dev/null; then
                # wget 显式指定保存的文件名
                wget --no-check-certificate -c -O "$TARGET_FILE" "$DOWNLOAD_URL"
            else
                # curl 显式指定保存的文件名
                curl -k -L -C - --create-dirs -o "$TARGET_FILE" "$DOWNLOAD_URL"
            fi
        done
    fi
done

# 移除临时队列
rm -f "$TODO_LIST" "$DONE_LIST"

echo "========================================================"
echo "下载彻底完成！资产及权重已100%同步。路径: ${SAVE_DIR}"
echo "========================================================"