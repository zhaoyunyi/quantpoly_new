#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "${OPENSPECW_SKIP_PATH_BOOTSTRAP:-0}" != "1" ]; then
  for extra_bin in /opt/homebrew/bin /usr/local/bin; do
    case ":$PATH:" in
      *":$extra_bin:"*) ;;
      *)
        if [ -d "$extra_bin" ]; then
          PATH="$PATH:$extra_bin"
        fi
        ;;
    esac
  done
fi

candidate_paths=()
if command -v openspec >/dev/null 2>&1; then
  candidate_paths+=("$(command -v openspec)")
fi
candidate_paths+=(
  "$ROOT_DIR/node_modules/.bin/openspec"
  "$HOME/.local/bin/openspec"
  "$HOME/.codex/bin/openspec"
)

for candidate in "${candidate_paths[@]}"; do
  if [ -x "$candidate" ]; then
    exec "$candidate" "$@"
  fi
done

if [ "${OPENSPECW_NO_NPX_FALLBACK:-0}" != "1" ] && command -v npx >/dev/null 2>&1; then
  exec npx -y @fission-ai/openspec@latest "$@"
fi

echo "openspec CLI 未安装或不在 PATH 中。" >&2
echo "当前仓库未内置 openspec 二进制，请在已安装 openspec 的环境中重试：" >&2
echo "  openspec $*" >&2
echo "可检查的常见位置：" >&2
for candidate in "${candidate_paths[@]}"; do
  echo "  - $candidate" >&2
done
exit 127
