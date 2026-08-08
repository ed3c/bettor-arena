#!/usr/bin/env bash
# Prove this module is relocatable, instead of asserting it in prose.
#
# The claim under test: copy the module anywhere, under any name, at any depth, and its core
# gate still means something. That cannot be shown by running the gate where it already lives
# -- there, every host assumption is satisfied by accident.
#
# So: build a throwaway host, copy the module in under a different name at a different depth,
# and run it there. Then break it, once per failure mode, and require the specific exit code
# back. A positive control alone cannot distinguish "the checks passed" from "the checks
# resolved nothing and returned success", which is exactly how a relocation refactor fails.
#
# Needs only python3 and git. Never calls a model: the subagent boundary proof runs under
# OPENWIKI_DRY_RUN, the same mechanism the gate itself uses.
#
# Run:  bash <module>/port/test_relocation.sh
# Exit: 0 all controls behaved · 1 some control did not

set -u

MODULE_SRC=$(cd "$(dirname "$0")/.." && pwd -P)
PASS=0
FAIL=0

# mktemp -d, never a fixed path under the repo: a fixture that lives in the tree is one more
# thing that can drift, and this test's whole point is to start from nothing.
SANDBOX=$(mktemp -d "${TMPDIR:-/tmp}/repo-wiki-relocation-XXXXXX") || exit 1
trap 'chmod -R u+w "$SANDBOX" 2>/dev/null; rm -rf "$SANDBOX"' EXIT

HOST="$SANDBOX/host"
# Deliberately not "kb-ingest", and deliberately not at depth 1. If anything still resolves
# by assuming either, it fails here rather than in someone else's repo six months from now.
MODULE="$HOST/vendor/third_party/wiki-port"

mkdir -p "$MODULE"
cp -R "$MODULE_SRC/." "$MODULE/"
# The source tree's own declaration would drag skill-bettor's profiles into a host that has
# none of them. Each case below writes the declaration it needs.
GATE="$MODULE/check_repo_wiki_converge.py"

git -C "$HOST" init -q
git -C "$HOST" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init

declare_profiles() { printf '%s\n' "$1" > "$MODULE/host-profile.json"; }

# Run the gate and compare its exit code to what this case is supposed to produce.
expect() {
  local label="$1" want="$2" got
  python3 "$GATE" >/dev/null 2>&1
  got=$?
  if [ "$got" = "$want" ]; then
    PASS=$((PASS + 1)); printf '[ok]   %-46s exit=%s\n' "$label" "$got"
  else
    FAIL=$((FAIL + 1)); printf '[BAD]  %-46s exit=%s want=%s\n' "$label" "$got" "$want"
  fi
}

echo "module copied to: $MODULE"
echo "--- positive control ---"
declare_profiles '{"profiles":[]}'
expect "core only, renamed, depth 3, foreign host" 0

echo "--- negative controls: the declaration ---"
mv "$MODULE/host-profile.json" "$MODULE/hp.away"
expect "declaration missing -> cannot tell" 3
mv "$MODULE/hp.away" "$MODULE/host-profile.json"

declare_profiles '{"profiles":["repodocs"]}'
expect "profile name misspelled -> cannot tell" 3

declare_profiles 'this is not json'
expect "declaration malformed -> cannot tell" 3

declare_profiles '{"host":"x"}'
expect "declaration has no profiles key -> cannot tell" 3

echo "--- negative controls: the core claims ---"
declare_profiles '{"profiles":[]}'

ASSET="$MODULE/openwiki/init.system.md"
cp "$ASSET" "$SANDBOX/asset.orig"
# One word, inside the official body: the kind of edit that reads as harmless.
python3 - "$ASSET" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text(encoding="utf-8")
needle = "Do not document every file or target a page count"
assert needle in t, "fixture drifted: spot-check line absent from the official prompt"
p.write_text(t.replace(needle, "Do not document every file or target a page budget"), encoding="utf-8")
PY
expect "official prompt text tampered" 1
cp "$SANDBOX/asset.orig" "$ASSET"

printf 'a local note\n' > "$MODULE/openwiki/notes.md"
expect "extra file inside openwiki/" 1
rm "$MODULE/openwiki/notes.md"

mv "$MODULE/openwiki/subagents/answer-verifier.md" "$SANDBOX/verifier.away"
expect "upstream asset missing" 1
mv "$SANDBOX/verifier.away" "$MODULE/openwiki/subagents/answer-verifier.md"

mv "$MODULE/port/openwiki_post.py" "$SANDBOX/post.away"
expect "post-processing executable missing" 1
mv "$SANDBOX/post.away" "$MODULE/port/openwiki_post.py"

mv "$MODULE/skill/SKILL.md" "$SANDBOX/skill.away"
expect "operating manual missing" 1
mv "$SANDBOX/skill.away" "$MODULE/skill/SKILL.md"

chmod -x "$MODULE/port/openwiki_subagent.sh"
expect "subagent runner not executable" 1
chmod +x "$MODULE/port/openwiki_subagent.sh"

echo "--- host-skill-links profile, on a host that is not skill-bettor ---"
mkdir -p "$HOST/.agents/skills" "$HOST/.claude/skills"
ln -s ../../vendor/third_party/wiki-port/skill "$HOST/.agents/skills/openwiki-port"
ln -s ../../vendor/third_party/wiki-port/skill "$HOST/.claude/skills/openwiki-port"
declare_profiles '{"profiles":["host-skill-links"]}'
expect "both host links are symlinks into the module" 0

# The failure this profile exists to catch: a copy instead of a link. Two files that agree
# today and silently diverge the first time someone edits one.
rm "$HOST/.claude/skills/openwiki-port"
cp -R "$MODULE/skill" "$HOST/.claude/skills/openwiki-port"
expect "a host link replaced by a real copy" 1
rm -rf "$HOST/.claude/skills/openwiki-port"
ln -s ../../vendor/third_party/wiki-port/skill "$HOST/.claude/skills/openwiki-port"

rm "$HOST/.agents/skills/openwiki-port"
expect "a declared host link missing entirely" 1

echo "--- skill-bettor-layout profile: stale-root scan derives from ALLOWED_ROOTS ---"
declare_profiles '{"profiles":["skill-bettor-layout"]}'
expect "layout profile green on a foreign host" 0

# The failure the dynamic derivation exists to catch: a committed doc naming SOME OTHER
# machine's checkout. A hardcoded known-roots list cannot flag a root it has never heard
# of; deriving "foreign" from ALLOWED_ROOTS can. The path is assembled so this script
# never carries a literal home root itself.
FOREIGN_ROOT="$(printf '/Us%s' 'ers/otherbox/elsewhere/tool')"
cp "$MODULE/skill/SKILL.md" "$SANDBOX/skillmd.orig"
printf '\nrun %s\n' "$FOREIGN_ROOT" >> "$MODULE/skill/SKILL.md"
expect "doc names a foreign checkout root" 1
cp "$SANDBOX/skillmd.orig" "$MODULE/skill/SKILL.md"

echo
echo "controls behaving: $PASS · misbehaving: $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "PASS: the module is relocatable, and its core checks still fail when they should"
