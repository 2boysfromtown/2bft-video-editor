"""Lint captions, plans, notes and SRTs against the brand-truth rules before delivery.

usage: brand_lint.py <files or folders ...> [--numbers]
  .py   only string literals are checked (comments are editor notes)
  .srt  .txt .md  every line
Flags (all ISSUE - a human decides; a word he really said may stay if it is not a claim):
  BANNED-WORD   guru, hack, secret, game-changer, "trust me", guaranteed, overnight
  INCOME        earn / income / revenue / salary / profit / kamai / lakh / crore / ₹ / Rs / $ / "per month" / client pricing
  COURSE-PITCH  course, enrol, seats, cohort, webinar, masterclass, coupon, discount, "limited offer", "DM me"
  NUMBER        (--numbers) every caption string in a plan with a digit: each must be confirmed by two transcription passes
The engine's caption syntax ({mint}, {$yellow} ...) is stripped before matching.
"""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

RULES = [
    ('BANNED-WORD', r'\b(gurus?|hack(s|ing|er)?|secrets?|game[- ]?changer|trust me|guarantee[ds]?|overnight)\b'),
    ('INCOME', r'(\b(earn(s|ed|ing)?|income|revenue|salary|profits?|kamai|kamaya|kamata|kamaate|kamaye|lakhs?|crores?|per month|monthly|/month|mahine (ke|ka|mein))\b'
               r'|₹|\brs\.?\s?\d|\$\s?\d|\d+\s*(k|hazaar|hajaar|thousand)\b[^.\n]{0,40}\b(rupa?ye?|rupees|rs|le raha|leta|charge|client)\b'
               r'|\bclient se\b[^.\n]{0,40}\ble\b)'),
    ('COURSE-PITCH', r'\b(course|enrol+(ment)?|seats?|cohort|webinar|masterclass|coupon|discount|limited offer|dm me)\b'),
]
STRIP = re.compile(r'[{}^*~_]|=#[0-9A-Fa-f]{6}:|(?<=\{)[!$~]')
STR_LIT = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
SKIP_KEYS = re.compile(r"^(layout|type|anchor|fill|color|track|side|name|size|ease|kind|mode|at|in|out|dt|src|tag|font|align|v_|clean|vface)$")


def texts(path):
    ext = os.path.splitext(path)[1].lower()
    for n, line in enumerate(open(path, encoding='utf-8-sig', errors='replace'), 1):
        if ext == '.py':
            if line.lstrip().startswith('#'):
                continue
            for m in STR_LIT.finditer(line):
                s = m.group(1) if m.group(1) is not None else m.group(2)
                if len(s) < 3 or SKIP_KEYS.match(s) or re.fullmatch(r'[\w./\\:-]+\.(mp4|wav|png|jpg|json|py)', s) or re.fullmatch(r'[a-z_]+', s):
                    continue
                yield n, s, True
        elif ext == '.srt':
            if re.match(r'^\d+\s*$', line) or '-->' in line:
                continue
            yield n, line.rstrip('\n'), True
        else:
            yield n, line.rstrip('\n'), False


def main():
    paths = []
    numbers = '--numbers' in sys.argv
    for a in [x for x in sys.argv[1:] if x != '--numbers']:
        if os.path.isdir(a):
            for root, _, fs in os.walk(a):
                paths += [os.path.join(root, f) for f in fs if f.lower().endswith(('.py', '.srt', '.txt', '.md'))]
        else:
            paths.append(a)
    hits = 0
    for p in sorted(paths):
        for n, s, spoken in texts(p):
            clean = STRIP.sub('', s)
            for code, rx in RULES:
                for m in re.finditer(rx, clean, re.I):
                    if re.search(r'\bnot\s+$', clean[:m.start()], re.I):  # "builders, not gurus" is the brand line itself
                        continue
                    hits += 1
                    print(f'{p}:{n}: {code}: "{m.group(0)}"  | {clean.strip()[:110]}')
            if numbers and spoken and p.lower().endswith('.py') and re.search(r'\d', clean) and ' ' in clean.strip():
                print(f'{p}:{n}: NUMBER (confirm with two passes): {clean.strip()[:110]}')
    print(f'{hits} brand flags in {len(paths)} files' + (' - read each one: a flag is a question, not a verdict' if hits else ''))


if __name__ == '__main__':
    main()
