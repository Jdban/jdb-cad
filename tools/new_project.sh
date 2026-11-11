#!/usr/bin/env bash
# Start a new project folder from the template.
# Usage: tools/new_project.sh <folder-name> <ID letter> "<one-line description>"
#   e.g. tools/new_project.sh bee-vac B "Bee vacuum intake port"
set -euo pipefail
cd "$(dirname "$0")/.."
NAME="${1:?folder name}"; LETTER="${2:?ID letter, e.g. B}"; DESC="${3:-$NAME}"
[[ -e "$NAME" ]] && { echo "$NAME already exists"; exit 1; }
SCRIPT="${NAME//-/_}.py"

mkdir -p "$NAME"/{original,photos,out}
sed -e "s/\"X1\"/\"${LETTER}1\"/g" -e "s/bracket.py/${SCRIPT}/g" examples/bracket.py > "$NAME/$SCRIPT"

cat > "$NAME/NOTES.md" <<EOF
# ${DESC}

## What it is
(What the part does, where it mounts, what failed before.)

## Contact points
(Every place the part touches the real object, and whether it's settled:
fit-test each uncertain one before printing the full part.)

## Constraints learned

## Decisions
EOF

cat > "$NAME/PARTS.md" <<EOF
# ${DESC}: parts log

Prefix: **${LETTER}**. Every printed part has its ID engraved. Freeze printed
versions: \`../tools/cad ${SCRIPT} freeze <ID> "<date>, <material>"\`.

| ID | File | Printed | What it is | Result |
|---|---|---|---|---|
EOF

cat > "$NAME/tracker.json" <<EOF
{
  "project": "${DESC}",
  "status": "Just started: need photos and measurements.",
  "items": [
    {"kind": "photo", "state": "need", "what": "The part and where it mounts, with a ruler in the photo", "how": "A couple of angles; a ruler or tape lying next to it."},
    {"kind": "measure", "state": "need", "what": "Existing model files", "how": "Tinkercad STL (or the old part's file). Is it exactly the version you printed? Any older versions?"}
  ]
}
EOF
echo "created $NAME/ ($SCRIPT, NOTES.md, PARTS.md, tracker.json, original/, photos/, out/)"
echo "IDs: ${LETTER}1, ${LETTER}2, ...  Try: cd $NAME && ../tools/cad $SCRIPT list"
