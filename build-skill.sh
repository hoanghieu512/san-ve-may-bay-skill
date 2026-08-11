#!/usr/bin/env bash
# Dong goi skill/ve-may-bay-noi-dia/ thanh file .skill de Save vao tai khoan Claude.
# Chan viec dong goi neu version o frontmatter va version o body lech nhau.
set -euo pipefail

cd "$(dirname "$0")"
NAME=ve-may-bay-noi-dia
SRC="skill/$NAME/SKILL.md"
OUT="$NAME.skill"

[ -f "$SRC" ] || { echo "khong tim thay $SRC"; exit 1; }

# version trong frontmatter: metadata.version
VER=$(awk '/^---$/{n++; next} n==1 && /^[[:space:]]*version:/ {
  sub(/^[[:space:]]*version:[[:space:]]*/, ""); gsub(/"/, ""); print; exit }' "$SRC")

[ -n "$VER" ] || { echo "FAIL: khong doc duoc metadata.version trong $SRC"; exit 1; }

# dong tuong ung o body, dang: **v1.0.0** · cap nhat ...
grep -q "^\*\*v$VER\*\*" "$SRC" || {
  echo "FAIL: frontmatter ghi version $VER nhung body khong co dong '**v$VER**'"
  echo "      sua cho khop roi chay lai — hai cho phai cung so"
  exit 1
}

rm -f "$OUT"
find "skill/$NAME" -name '.DS_Store' -delete
(cd skill && zip -q -r -X "../$OUT" "$NAME")

echo "da tao $OUT — version $VER"
echo "nho: git tag v$VER && git push --tags"
