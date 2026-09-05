#!/usr/bin/env python3
"""Check the vault's relationship data against the closed vocabulary.

This is the tool that makes `vocab.py`'s SYNONYMS table shrink. The old
pipeline normalised free-prose relation values downstream, inside
`wiki_map.py`, with a synonym table and a substring-matching `infer_type()`.
That is the wrong end: the renderer cannot know that `subordinate she cannot
remove` means `rival`, so it guessed, and `hatred` — a value the vault used
for weeks — was painted neutral grey because nobody had added it to a second
table in a second file.

Fixing it at the source costs one word per article and removes the guessing
entirely.

Exit code is 1 if anything needs a human, so it can gate a build.

Usage:  python3 lint_relations.py <vault-dir> [--fix-spellings]
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_map import (link_target, load_vault, parse_relationship_prose, slug)
from vocab import KINDS, LEGACY_SPELLINGS, normalise_kind

BOLD = "\033[1m" if sys.stdout.isatty() else ""
OFF = "\033[0m" if sys.stdout.isatty() else ""


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    fix = "--fix-spellings" in sys.argv

    arts, alias = load_vault(root)
    chars = {s: a for s, a in arts.items() if a["fm"].get("type") == "character"}

    unknown = defaultdict(list)      # value -> [article]
    legacy = defaultdict(list)
    declared = defaultdict(set)      # article -> {target}
    noted = defaultdict(set)
    dangling = []
    shapes = []
    no_kind = []

    for stem, art in chars.items():
        rels = art["fm"].get("relations") or {}
        if isinstance(rels, list):
            shapes.append(stem)
            rels = {t: None for t in rels if t}
        elif not isinstance(rels, dict):
            shapes.append(stem)
            rels = {}

        for raw_target, raw_kind in rels.items():
            tgt = link_target(raw_target, alias)
            if tgt not in chars:
                dangling.append((stem, str(raw_target)))
                continue
            declared[stem].add(tgt)
            if raw_kind is None:
                no_kind.append((stem, tgt))
                continue
            kind, was_legacy = normalise_kind(raw_kind)
            if kind is None:
                unknown[str(raw_kind)].append(stem)
            elif was_legacy:
                legacy[str(raw_kind)].append(stem)

        for raw_target, note, secret in parse_relationship_prose(art["body"]):
            tgt = link_target(raw_target, alias)
            if tgt in chars:
                noted[stem].add(tgt)
            elif raw_target:
                dangling.append((stem, raw_target))

    # A relationship the article describes in prose but never types. The map
    # can draw it, but it has to draw it grey, and grey is most of what the
    # graph currently looks like.
    described_untyped = sorted(
        (a, b) for a, ts in noted.items() for b in ts if b not in declared.get(a, ()))

    # One-sided: A declares B, B never declares A. The reader sees "sin
    # declarar" on one end of 40% of the graph and reasonably assumes the
    # tool is broken rather than the data incomplete.
    all_pairs = {(a, b) for a, ts in declared.items() for b in ts}
    all_pairs |= {(a, b) for a, ts in noted.items() for b in ts}
    one_sided = sorted(p for p in all_pairs if (p[1], p[0]) not in all_pairs)

    problems = 0

    def head(n, text):
        nonlocal problems
        problems += n
        print(f"\n{BOLD}{text}{OFF}")

    if unknown:
        head(sum(len(v) for v in unknown.values()),
             f"Fuera de vocabulario ({sum(len(v) for v in unknown.values())}) "
             "— elige un valor de la lista y guarda tu frase en la nota")
        for value, arts_ in sorted(unknown.items()):
            print(f"  {value!r}")
            for a in arts_:
                print(f"      {a}")
        print(f"\n  Vocabulario válido: {', '.join(sorted(KINDS))}")

    if legacy:
        n = sum(len(v) for v in legacy.values())
        head(n, f"Grafías heredadas ({n}) — se traducen solas hoy, "
                "pero cada una es una entrada que mantener en vocab.py")
        for value, arts_ in sorted(legacy.items()):
            print(f"  {value!r} → {LEGACY_SPELLINGS.get(value.lower(), '?')}"
                  f"   ({', '.join(arts_)})")

    if shapes:
        head(len(shapes), f"`relations:` mal formado ({len(shapes)}) "
                          "— debe ser un mapa `Nombre: tipo`, no una lista")
        for s in shapes:
            print(f"  {s}")

    if dangling:
        head(len(dangling), f"Destinos sin artículo ({len(dangling)})")
        for a, b in sorted(set(dangling)):
            print(f"  {a} → {b}")

    if no_kind:
        head(len(no_kind), f"Declaradas sin tipo ({len(no_kind)})")
        for a, b in no_kind:
            print(f"  {a} → {b}")

    if described_untyped:
        head(0, f"Descritas en prosa pero sin tipo ({len(described_untyped)}) "
                "— se dibujan en gris «sin declarar»")
        for a, b in described_untyped[:25]:
            print(f"  {a} → {b}")
        if len(described_untyped) > 25:
            print(f"  … y {len(described_untyped) - 25} más")

    if one_sided:
        head(0, f"Declaradas por un solo lado ({len(one_sided)} de "
                f"{len(all_pairs)}) — el otro extremo sale «sin declarar»")
        for a, b in one_sided[:25]:
            print(f"  {a} → {b}    (falta {b} → {a})")
        if len(one_sided) > 25:
            print(f"  … y {len(one_sided) - 25} más")

    if fix and legacy:
        n = 0
        for stem in {a for arts_ in legacy.values() for a in arts_}:
            p = arts[stem]["path"]
            text = p.read_text(encoding="utf-8")
            out = text
            for value in legacy:
                target = LEGACY_SPELLINGS.get(value.lower())
                if not target:
                    continue
                # only inside the frontmatter, only as a `key: value` line
                out = re.sub(rf"^(\s+[^:\n]+:\s*){re.escape(value)}\s*$",
                             rf"\g<1>{target}", out, flags=re.M)
            if out != text:
                p.write_text(out, encoding="utf-8")
                n += 1
        print(f"\n{BOLD}--fix-spellings:{OFF} {n} archivos reescritos. "
              "Revisa el diff antes de commitear.")

    print(f"\n{BOLD}{problems} problema(s) que necesitan una decisión humana.{OFF}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
