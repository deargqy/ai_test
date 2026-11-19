#!/bin/zsh
set -eu
cd -- "${0:A:h}"
game_id="${1:-cats}"
if [[ "$game_id" == *[^a-z0-9_-]* || ! -f "games/$game_id/game.json" ]]; then
  echo "找不到游戏配置 games/$game_id/game.json" >&2
  exit 1
fi
profile="$PWD/games/$game_id/game.json"
umask 077
mkdir -p .stream-control
binary="$PWD/.stream-control/SteamWindow"
source_file="$PWD/tools/SteamWindow.swift"
if [[ ! -x "$binary" || "$source_file" -nt "$binary" ]]; then
  build="$(mktemp -d "$PWD/.stream-control/build.XXXXXX")"
  trap 'rm -f "$build/SteamWindow"; rmdir "$build"' EXIT
  /usr/bin/xcrun swiftc -parse-as-library -module-cache-path "$PWD/.stream-control/module-cache" "$source_file" -o "$build/SteamWindow"
  mv "$build/SteamWindow" "$binary"
  rmdir "$build"
  trap - EXIT
fi
game_name="$("$binary" --check-profile "$profile")"
echo "将连接《$game_name》的游戏窗口；需要启动时由 Steam 处理。"
echo "首次使用可能出现 macOS 屏幕录制或辅助功能授权提示。"
echo "连续空闲 15 分钟后退出。操作期间会自动切换到已编译的新版本，按 Control-C 可提前结束。"
directory="$PWD/.stream-control"
# 旧版启动器会直接进入窗口工具；仅在它持有本项目锁、且运行的是已替换的文件时交接。
if [[ -e "$directory/session.lock" ]]; then
  holder="$(/usr/sbin/lsof -t -- "$directory/session.lock" 2>/dev/null || true)"
  if [[ "$holder" == <-> ]]; then
    previous="$(/usr/sbin/lsof -a -p "$holder" -d txt -Fin 2>/dev/null |
      /usr/bin/awk -v path="$binary" '/^i/ {inode=substr($0,2)} $0=="n"path {print inode; exit}')"
    if [[ -n "$previous" && "$previous" != "$(/usr/bin/stat -f '%i' "$binary")" ]]; then
      kill -TERM "$holder"
      for attempt in {1..20}; do
        kill -0 "$holder" 2>/dev/null || break
        sleep 0.1
      done
    fi
  fi
fi
child=""
stop_child() {
  if [[ -n "$child" ]]; then
    kill -TERM "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
    child=""
  fi
}
trap 'stop_child' EXIT
trap 'exit 0' INT TERM
while true; do
  version="$(/usr/bin/stat -f '%i' "$binary")"
  "$binary" "$directory" "$profile" &
  child=$!
  while kill -0 "$child" 2>/dev/null; do
    if [[ "$(/usr/bin/stat -f '%i' "$binary")" != "$version" ]]; then
      stop_child
      break
    fi
    sleep 1
  done
  if [[ -n "$child" ]]; then
    wait "$child"
    exit $?
  fi
done
