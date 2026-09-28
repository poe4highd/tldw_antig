#!/bin/bash
# 将 deploy/ 下的 systemd 单元与 rt 命令注册到用户环境（幂等，可重复执行）
#   ~/.config/systemd/user/<unit>  -> <repo>/deploy/systemd/<unit>
#   ~/bin/rt                       -> <repo>/deploy/bin/rt
# 已存在的普通文件会先移到 ~/.config/systemd/user/backup-<时间戳>/
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
REPO_DIR="$(dirname "$DEPLOY_DIR")"
EXPECTED_REPO="$HOME/projects/tldw_antig"   # 单元文件中 %h/projects/tldw_antig 的锚点
UNIT_DIR="$HOME/.config/systemd/user"
BIN_DIR="$HOME/bin"

if [ "$REPO_DIR" != "$EXPECTED_REPO" ]; then
    echo "拒绝执行：只能从生产主仓库 $EXPECTED_REPO 运行（当前 $REPO_DIR）。" >&2
    echo "worktree 中的改动需先合并到 main。" >&2
    exit 1
fi

BACKUP_DIR="$UNIT_DIR/backup-$(date +%Y%m%d%H%M%S)"

link() {
    local src="$1" dst="$2"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        mkdir -p "$BACKUP_DIR"
        mv "$dst" "$BACKUP_DIR/"
        echo "备份 $dst -> $BACKUP_DIR/"
    fi
    ln -sfn "$src" "$dst"
    echo "链接 $dst -> $src"
}

mkdir -p "$UNIT_DIR" "$BIN_DIR"
chmod +x "$DEPLOY_DIR"/bin/*
for unit in "$DEPLOY_DIR"/systemd/*; do
    link "$unit" "$UNIT_DIR/$(basename "$unit")"
done
link "$DEPLOY_DIR/bin/rt" "$BIN_DIR/rt"

systemctl --user daemon-reload
echo "完成。单元内容变更需重启对应服务生效，例如：rt restart tldw-backend"
