"""
python manage.py compile_translations

Turns locale/<lang>/LC_MESSAGES/django.po into django.mo.
Pure Python — works on Windows without installing GNU gettext.
Run it after editing any .po file, then restart the server.
"""
import ast
import struct
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def parse_po(path):
    """Returns {msgid: msgstr}. Supports multi-line strings; skips fuzzy and empty entries."""
    entries, msgid, msgstr, current, fuzzy = {}, None, None, None, False

    def flush():
        nonlocal msgid, msgstr, fuzzy
        if msgid is not None and msgstr is not None and (msgstr or msgid == "") and not fuzzy:
            entries[msgid] = msgstr
        msgid, msgstr, fuzzy = None, None, False

    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
        elif line.startswith("msgid "):
            if msgstr is not None:
                flush()
            msgid, current = ast.literal_eval(line[6:]), "id"
        elif line.startswith("msgstr "):
            msgstr, current = ast.literal_eval(line[7:]), "str"
        elif line.startswith('"'):
            text = ast.literal_eval(line)
            if current == "id":
                msgid += text
            elif current == "str":
                msgstr += text
        elif not line:
            flush()
    flush()
    return entries


def write_mo(entries, path):
    keys = sorted(entries)
    ids = b""
    strs = b""
    offsets = []
    for k in keys:
        kb, vb = k.encode("utf-8"), entries[k].encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\0"
        strs += vb + b"\0"
    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
    output += struct.pack(f"{len(koffsets)}i", *koffsets)
    output += struct.pack(f"{len(voffsets)}i", *voffsets)
    output += ids + strs
    Path(path).write_bytes(output)


class Command(BaseCommand):
    help = "Compile .po translation files to .mo (no gettext needed)"

    def handle(self, *args, **options):
        found = 0
        for base in settings.LOCALE_PATHS:
            for po in Path(base).glob("*/LC_MESSAGES/*.po"):
                entries = parse_po(po)
                write_mo(entries, po.with_suffix(".mo"))
                found += 1
                self.stdout.write(f"  {po.parent.parent.name}: {len(entries) - 1} strings → {po.with_suffix('.mo').name}")
        if found:
            self.stdout.write(self.style.SUCCESS(f"Compiled {found} language file(s). Restart the server to see changes."))
        else:
            self.stdout.write(self.style.WARNING("No .po files found in LOCALE_PATHS."))
