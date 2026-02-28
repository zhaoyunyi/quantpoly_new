#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/openspecw.sh"

if [ ! -x "$SCRIPT" ]; then
  echo "script missing or not executable: $SCRIPT" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

cat >"$fake_bin/openspec" <<'EOF'
#!/usr/bin/env bash
printf 'fake-openspec %s\n' "$*"
EOF
chmod +x "$fake_bin/openspec"

PATH="$fake_bin:$PATH" "$SCRIPT" validate sample-change --strict >"$tmp_dir/ok.log"
grep -q "fake-openspec validate sample-change --strict" "$tmp_dir/ok.log" \
  || { echo "expected wrapper to delegate to openspec from PATH" >&2; exit 1; }

rm -f "$fake_bin/openspec"
cat >"$fake_bin/npx" <<'EOF'
#!/usr/bin/env bash
printf 'fake-npx %s\n' "$*"
EOF
chmod +x "$fake_bin/npx"

PATH="$fake_bin:/usr/bin:/bin" HOME="$tmp_dir/home" "$SCRIPT" validate sample-change --strict >"$tmp_dir/npx.log"
grep -q "fake-npx -y @fission-ai/openspec@latest validate sample-change --strict" "$tmp_dir/npx.log" \
  || { echo "expected wrapper to fall back to npx" >&2; exit 1; }

PATH="/usr/bin:/bin" HOME="$tmp_dir/home" OPENSPECW_SKIP_PATH_BOOTSTRAP=1 OPENSPECW_NO_NPX_FALLBACK=1 \
  "$SCRIPT" validate sample-change --strict >"$tmp_dir/missing.log" 2>&1 && {
  echo "expected missing openspec failure" >&2
  exit 1
}

grep -q "openspec CLI 未安装或不在 PATH 中" "$tmp_dir/missing.log" \
  || { echo "missing expected wrapper error output" >&2; exit 1; }

echo "openspecw test ok"
