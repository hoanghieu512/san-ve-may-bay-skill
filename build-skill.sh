#!/usr/bin/env bash
# Dong goi skill/ve-may-bay-noi-dia/ thanh file .skill de Save vao tai khoan Claude.
set -euo pipefail

cd "$(dirname "$0")"
NAME=ve-may-bay-noi-dia
OUT="$NAME.skill"

[ -f "skill/$NAME/SKILL.md" ] || { echo "khong tim thay skill/$NAME/SKILL.md"; exit 1; }

rm -f "$OUT"
find "skill/$NAME" -name '.DS_Store' -delete
(cd skill && zip -q -r -X "../$OUT" "$NAME")

echo "da tao $OUT"
unzip -l "$OUT" | tail -3
