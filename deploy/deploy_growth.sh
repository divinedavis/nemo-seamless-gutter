#!/usr/bin/env bash
# Show — and optionally close — the gap between the growth engine committed to
# this repository and the one actually running on the droplet.
#
# WHY THIS EXISTS
#
# The docroot (/var/www/nemo-seamless-gutter) is not a git checkout, and
# growth/publish_state.sh only ever copies droplet -> repo. Nothing copies the
# other way. So a fix committed here does nothing until a human copies the file
# across, and there is no signal in the published snapshot to say whether that
# happened: snapshot.py emits a `code_version` fingerprint block designed to
# answer exactly this question, but snapshot.py is itself one of the stale
# files, so the diagnostic is undeployed along with everything it would report.
#
# The result, as of 2026-08-30, is a droplet running a file-by-file patchwork:
# techniques.py looks current, snapshot.py predates 2026-08-07 (its published
# output has no `code_version`, no `keywords.ranked`, no `gsc.pages` and none of
# the `log_*`/`crawl_*` series that SERIES has listed since 08-15), and
# review.py predates 2026-08-29 (it restamped the six unfounded `works: true`
# verdicts again this morning). Nobody can tell which is which without hashing
# the files, so this hashes the files.
#
# USAGE, on the droplet:
#
#   git -C /root/nemo-repo fetch origin main
#   git -C /root/nemo-repo reset --hard origin/main
#   bash /root/nemo-repo/deploy/deploy_growth.sh            # report only
#   bash /root/nemo-repo/deploy/deploy_growth.sh --apply    # copy the stale ones
#
# The report is the useful half and is safe to run any time — it is read-only
# and it is the answer to "is my fix live?". --apply is the second half.
#
# WHAT IT WILL NOT TOUCH
#
# Only *.py files under growth/, plus growth_daily.py at the root. The engine's
# runtime state — techniques.json, keywords.json, results.jsonl, state.json —
# lives in the same directory, is owned by the droplet, is gitignored, and is
# the record of everything the engine has ever decided. Copying a repo copy of
# any of those over the live one would destroy it, so this only ever copies .py.
set -euo pipefail

DOCROOT="${WEB_ROOT:-/var/www/nemo-seamless-gutter}"
SRC="${NEMO_CLONE:-/root/nemo-repo}"
APPLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --root)  DOCROOT="$2"; shift ;;
    --from)  SRC="$2"; shift ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

[ -d "$SRC/growth" ]     || { echo "no growth/ in source $SRC" >&2; exit 1; }
[ -d "$DOCROOT/growth" ] || { echo "no growth/ in docroot $DOCROOT" >&2; exit 1; }

hash_of() { [ -f "$1" ] && sha256sum "$1" | cut -c1-12 || echo "--------ABSENT"; }

# Relative paths, source-side. growth_daily.py is the cron entrypoint and lives
# at the root, not under growth/, but it is engine code and goes stale the same
# way — it was the file whose fix on 2026-08-26 restarted the run.
FILES=$(cd "$SRC" && ls growth/*.py 2>/dev/null; [ -f "$SRC/growth_daily.py" ] && echo growth_daily.py)

stale=0
total=0
printf '%-34s %-14s %-14s %s\n' FILE REPO DROPLET STATE
printf '%-34s %-14s %-14s %s\n' ---- ---- ------- -----
for rel in $FILES; do
  total=$((total + 1))
  a=$(hash_of "$SRC/$rel")
  b=$(hash_of "$DOCROOT/$rel")
  if [ "$a" = "$b" ]; then
    state="ok"
  elif [ "$b" = "--------ABSENT" ]; then
    state="MISSING"; stale=$((stale + 1))
  else
    state="STALE"; stale=$((stale + 1))
  fi
  printf '%-34s %-14s %-14s %s\n' "$rel" "$a" "$b" "$state"
done

echo
echo "$stale of $total engine file(s) differ from the repository."

if [ "$stale" -eq 0 ]; then
  echo "The droplet is running what is committed. Nothing to do."
  exit 0
fi

if [ "$APPLY" -eq 0 ]; then
  echo "Report only. Re-run with --apply to copy the differing files across."
  echo "Nothing was written."
  exit 0
fi

STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="$DOCROOT/growth/.deploy-bak-$STAMP"
mkdir -p "$BACKUP"
echo "Backing up the current engine to $BACKUP"

for rel in $FILES; do
  a=$(hash_of "$SRC/$rel")
  b=$(hash_of "$DOCROOT/$rel")
  [ "$a" = "$b" ] && continue
  if [ -f "$DOCROOT/$rel" ]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$DOCROOT/$rel" "$BACKUP/$rel"
  fi
  mkdir -p "$DOCROOT/$(dirname "$rel")"
  cp -a "$SRC/$rel" "$DOCROOT/$rel"
  echo "  deployed $rel"
done

echo
echo "Done. Sanity check before the next 06:00 run:"
echo "  cd $DOCROOT && python3 -c 'import growth.snapshot, growth.review, growth.techniques'"
echo
echo "Tomorrow's snapshot.json should gain a top-level 'code_version' block."
echo "If it does not, this did not take and the import above is where to look."
echo "To undo: cp -a $BACKUP/growth/*.py $DOCROOT/growth/"
