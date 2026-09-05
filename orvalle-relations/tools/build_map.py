#!/usr/bin/env python3
"""Build the relationship map's data from the wiki vault, and only the vault.

`wiki_map.py` merged the vault with the card layer under
`/home/claude/project/content`. Since the freeze the cards are not maintained
and `Meta/CURRENT_STATE.md` says the wiki is the only living surface, so a
generator that still needs them can only reproduce their staleness. This one
reads `Articles/**.md` and nothing else, which also removes the second source
of truth that made `value` and `note` live somewhere the wiki could not see.

Emits `map-data.json`:

    nodes[]    one per character, plus one per group (realm, faction)
    edges[]    one per pair, carrying BOTH perspectives explicitly
    groups[]   the up: tree, which is also the semantic-zoom hierarchy
    facets{}   the filter axes, split out of the flat `tags` list
    reveals[]  the ordered reveal points the spoiler slider walks

Usage:  python3 build_map.py <vault-dir> [out.json]
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocab import (BOND_COLOUR, BOND_ES, BOND_FAMILY, BOND_FAMILY_ES,
                   BOND_INVERSE, FACETS, KIND_ES, KIND_TO_FACET,
                   FACET_COLOUR, normalise_kind)

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]")
# A relationship paragraph: `**[[Target]]** — prose` or `**Target** — prose`,
# continuing over wrapped lines until a blank line or the next entry.
REL_HEAD = re.compile(r"^\*\*(?:\[\[([^\]|]+)(?:\|[^\]]+)?\]\]|([^*]+))\*\*\s*[—–-]\s*(.*)$")
SECTION = re.compile(r"^##+\s*(.+?)\s*$", re.M)

# `tags` is one flat list holding three different axes. Splitting it is what
# lets a filter say "realm = Arvela" without also matching "status = frozen".
REALMS = {"Arvela", "Kurogane", "Yongxi", "Starbreeze", "Selmaren", "Nadir"}
STATUS_TAGS = {"provisional name", "post-mvp", "frozen", "mvp", "Title"}


def slug(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def strip_links(s):
    return WIKILINK.sub(lambda m: m.group(2) or m.group(1), s)


def load_vault(root):
    """Every article, keyed by filename stem, with an alias index beside it."""
    arts, alias = {}, {}
    for p in sorted((root / "Articles").rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        try:
            fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
        except yaml.YAMLError:
            fm = {}
        if not isinstance(fm, dict):
            fm = {}
        body = text[m.end():] if m else text
        stem = p.stem
        arts[stem] = {"fm": fm, "body": body, "path": p,
                      "section": p.parent.name}
        alias[slug(stem)] = stem
        for a in (fm.get("aliases") or []):
            if a:
                alias.setdefault(slug(a), stem)
    return arts, alias


def link_target(raw, alias):
    """Resolve a wikilink or bare name to an article stem, or None."""
    if not raw:
        return None
    name = strip_links(str(raw)).strip().strip("'\"")
    return alias.get(slug(name))


def secret_spans(body):
    """Character ranges covered by a `[!secret]` callout.

    A callout is a blockquote: it runs from its `> [!secret]` line to the first
    line that is not a `>` continuation. Anything inside is material the world
    does not openly know, which is what the reveal default keys on.
    """
    spans, lines, pos = [], body.split("\n"), 0
    starts = []
    for i, line in enumerate(lines):
        starts.append(pos)
        pos += len(line) + 1
    i = 0
    while i < len(lines):
        if re.match(r"^\s*>\s*\[!secret\]", lines[i]):
            j = i
            while j + 1 < len(lines) and lines[j + 1].lstrip().startswith(">"):
                j += 1
            spans.append((starts[i], starts[j] + len(lines[j])))
            i = j
        i += 1
    return spans


def in_secret(spans, idx):
    return any(a <= idx < b for a, b in spans)


def intro(body):
    """The lead paragraph. The wiki's own style guide promises it is two or
    three sentences saying who they are, which is exactly a hover card."""
    body = re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
    for block in body.split("\n\n"):
        b = block.strip()
        if not b or b.startswith((">", "#", "|", "-", "*")):
            continue
        return re.sub(r"\s+", " ", strip_links(b)).strip()
    return ""


def parse_relationship_prose(body):
    """Yield (target_raw, note, secret, secret_note) from `## Relationships`.

    Entries wrap over several lines, so a line-at-a-time reader loses most of
    every note. Collect until the next bold-lead entry.

    An entry OWNS the callouts that follow it, up to the next entry. That is
    how the vault actually authors a hidden relationship — the public reading
    in open prose, then a `[!secret]` underneath saying what is really going
    on — and it is what the reveal level keys on. Testing whether the entry's
    own first line sits inside a callout finds nothing, because it never does.
    """
    heads = [(m.start(), m.group(1)) for m in SECTION.finditer(body)]
    start = end = None
    for i, (pos, title) in enumerate(heads):
        if title.strip().lower() == "relationships":
            start = pos
            end = heads[i + 1][0] if i + 1 < len(heads) else len(body)
            break
    if start is None:
        return
    block = body[start:end]
    base = start
    lines = block.split("\n")
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    i = 0
    while i < len(lines):
        m = REL_HEAD.match(lines[i].strip())
        if not m:
            i += 1
            continue
        target = (m.group(1) or m.group(2) or "").strip()
        parts = [m.group(3).strip()]
        j = i + 1
        while j < len(lines):
            nxt = lines[j].strip()
            if not nxt or REL_HEAD.match(nxt) or nxt.startswith(("#", ">")):
                break
            parts.append(nxt)
            j += 1
        note = re.sub(r"\s+", " ", " ".join(parts)).strip()

        # everything from here to the next entry belongs to this relationship
        k = j
        while k < len(lines) and not REL_HEAD.match(lines[k].strip()) \
                and not lines[k].startswith("#"):
            k += 1
        tail = "\n".join(lines[j:k])
        secret = None
        sm = re.search(r"^\s*>\s*\[!secret\]-?\s*(.*?)$((?:\n\s*>.*)*)",
                       tail, re.M)
        if sm:
            knowers = re.sub(r"^Known to:\s*", "", strip_links(sm.group(1))).strip()
            hidden = re.sub(r"^\s*>\s?", "", sm.group(2), flags=re.M)
            secret = {"knowers": knowers,
                      "note": re.sub(r"\s+", " ", strip_links(hidden)).strip()}
        yield target, note, secret
        i = j


def short_label(note, limit=46):
    """The first clause of a note, for the arrow label. FFXVI's Grand Cast
    labels its arrows in three or four words; the vocabulary slug is for the
    colour, this is for the reader."""
    if not note:
        return None
    first = re.split(r"[.;:]|\s—\s|\s–\s", strip_links(note).strip())[0]
    first = first.strip().strip(",").strip()
    if not first or len(first) > limit:
        return None
    return first[0].lower() + first[1:]


def facets_of(fm, stem):
    tags = [str(t) for t in (fm.get("tags") or []) if t]
    realm = next((t for t in tags if t in REALMS), None)
    status = [t for t in tags if t in STATUS_TAGS]
    subtype = [t for t in tags if t not in REALMS and t not in STATUS_TAGS]
    if not realm and fm.get("nation"):
        realm = strip_links(str(fm["nation"])).strip("'\"")
    return {"realm": realm, "subtype": subtype, "status": status}


# ── build ────────────────────────────────────────────────────────────
def build(root):
    arts, alias = load_vault(root)
    report = {"unknown_kinds": Counter(), "legacy_spellings": Counter(),
              "unresolved_targets": Counter(), "one_sided": [],
              "unstructured_sections": [], "shape_deviations": Counter(),
              "secret_readings": 0}

    chars = {s: a for s, a in arts.items() if a["fm"].get("type") == "character"}

    # ── nodes ────────────────────────────────────────────────────────
    nodes = {}
    for stem, art in chars.items():
        fm, body = art["fm"], art["body"]
        fac = link_target(fm.get("faction"), alias)
        f = facets_of(fm, stem)
        # An article's `up:` chain is the semantic-zoom hierarchy: Nations >
        # Arvela > The Crown > Vareth. Walking it here means the renderer gets
        # the tree for free and never has to guess a grouping.
        chain, seen, cur = [], set(), stem
        while cur and cur not in seen:
            seen.add(cur)
            up = arts.get(cur, {}).get("fm", {}).get("up")
            nxt = link_target(up, alias)
            if not nxt:
                break
            chain.append(nxt)
            cur = nxt
        nodes[stem] = {
            "id": slug(stem), "stem": stem,
            "name": strip_links(str(fm.get("aliases", [stem])[0]
                                    if False else stem)),
            "aliases": [str(a) for a in (fm.get("aliases") or [])],
            "title": None,
            "faction": slug(fac) if fac else None,
            "factionLabel": fac,
            "realm": f["realm"],
            "people": strip_links(str(fm.get("people") or "")).strip("'\"") or None,
            "subtype": f["subtype"], "statusTags": f["status"],
            "status": fm.get("status"),
            "dead": bool(fm.get("died")),
            "state": (fm.get("state") or None),
            "brief": intro(body),
            "upChain": [slug(c) for c in chain],
            "upLabels": chain,
            "secrets": len(secret_spans(body)),
            "unresolved": len(re.findall(r">\s*\[!unresolved\]", body)),
            "magic": [strip_links(str(x)) for x in (fm.get("magic") or []) if x],
        }

    # ── edges ────────────────────────────────────────────────────────
    # One record per unordered pair, holding both directions explicitly. The
    # old shape stored `type` plus an optional `reverseType`, which made the
    # source's reading structurally privileged and left 40% of the graph
    # rendering as "sin declarar" purely because nobody had written the pair
    # from the other side.
    pairs = {}

    def side(a, b):
        key = tuple(sorted((a, b)))
        if key not in pairs:
            pairs[key] = {"a": key[0], "b": key[1],
                          "a_to_b": None, "b_to_a": None, "bond": None,
                          "sources": []}
        return pairs[key], ("a_to_b" if key[0] == a else "b_to_a")

    def put(src, tgt, kind, label, note, reveal, origin, secret=None):
        rec, slot = side(src, tgt)
        cur = rec[slot]
        # Frontmatter states the kind; prose states the note. Merge rather
        # than let whichever ran last win.
        if cur is None:
            rec[slot] = {"kind": kind, "label": label, "note": note,
                         "reveal": reveal, "secret": secret}
        else:
            if kind and (cur["kind"] is None or cur["kind"] == "unknown"):
                cur["kind"] = kind
            if note and not cur["note"]:
                cur["note"] = note
            if label and not cur["label"]:
                cur["label"] = label
            if secret and not cur.get("secret"):
                cur["secret"] = secret
            cur["reveal"] = max(cur["reveal"], reveal)
        if origin not in rec["sources"]:
            rec["sources"].append(origin)

    for stem, art in chars.items():
        fm, body = art["fm"], art["body"]
        spans = secret_spans(body)

        # (1) frontmatter `relations:` — a kind, no note, one direction.
        # One article writes it as a bare list of links with no kind at all
        # (Yurael). Accept it as "declared, kind unstated" and report it,
        # rather than crashing the build or silently dropping four edges.
        raw_relations = fm.get("relations") or {}
        if isinstance(raw_relations, list):
            report["shape_deviations"][stem] += 1
            raw_relations = {t: None for t in raw_relations if t}
        elif not isinstance(raw_relations, dict):
            report["shape_deviations"][stem] += 1
            raw_relations = {}
        for raw_target, raw_kind in raw_relations.items():
            tgt = link_target(raw_target, alias)
            if tgt not in chars:
                report["unresolved_targets"][f"{stem} → {raw_target}"] += 1
                continue
            kind, legacy = normalise_kind(raw_kind)
            if kind is None:
                if raw_kind is not None:
                    report["unknown_kinds"][f"{raw_kind}  ({stem})"] += 1
                kind = "unknown"
            elif legacy:
                report["legacy_spellings"][f"{raw_kind} → {kind}"] += 1
            label = None
            if str(raw_kind).strip().lower() not in (kind, "unknown"):
                label = str(raw_kind).strip()  # keep the writer's own phrase
            put(stem, tgt, kind, label, None, 1, "frontmatter")

        # (2) the `## Relationships` prose — a note, and its reveal level
        structured = False
        for raw_target, note, secret in parse_relationship_prose(body):
            structured = True
            tgt = link_target(raw_target, alias)
            if tgt not in chars:
                report["unresolved_targets"][f"{stem} → {raw_target}"] += 1
                continue
            # Reveal default, derived rather than invented. The relationship
            # itself is public (1) — the article states it in open prose. What
            # a `[!secret]` under it adds is a second, truer reading of the
            # same relationship, and THAT is what level 3 unlocks. So the edge
            # exists at 1 and CHANGES at 3, which is the behaviour the wiki's
            # own spoiler policy asks for: record the false version openly and
            # the true one in the callout. Hiding the edge instead would leave
            # a visible hole, and a hole is itself a spoiler.
            put(stem, tgt, None, short_label(note), strip_links(note),
                1, "prose", secret)
            if secret:
                report["secret_readings"] += 1
        if not structured and re.search(r"^##+\s*Relationships", body, re.M):
            report["unstructured_sections"].append(stem)

    # (3) structural bonds, read from the fields that already imply them
    def bond(a, b, kind):
        if a in chars and b in chars:
            rec, slot = side(a, b)
            rec["bond"] = kind if slot == "a_to_b" else BOND_INVERSE.get(kind, kind)

    # ── reveal overlay, if the vault has one ─────────────────────────
    overlay_path = root / "Data" / "reveals.yaml"
    overlay = {}
    if overlay_path.exists():
        overlay = yaml.safe_load(overlay_path.read_text()) or {}
    for key, lvl in (overlay.get("relations") or {}).items():
        a, _, b = key.partition("|")
        rec = pairs.get(tuple(sorted((a.strip(), b.strip()))))
        if rec:
            for s in ("a_to_b", "b_to_a"):
                if rec[s]:
                    rec[s]["reveal"] = int(lvl)

    # one-sided report
    for (a, b), rec in pairs.items():
        if bool(rec["a_to_b"]) != bool(rec["b_to_a"]):
            who = a if rec["a_to_b"] else b
            other = b if rec["a_to_b"] else a
            report["one_sided"].append(f"{who} → {other}")

    edges = []
    for (a, b), rec in sorted(pairs.items()):
        for s in ("a_to_b", "b_to_a"):
            if rec[s] and rec[s]["kind"] is None:
                rec[s]["kind"] = "unknown"
        edges.append({
            "a": nodes[a]["id"], "b": nodes[b]["id"],
            "aToB": rec["a_to_b"], "bToA": rec["b_to_a"],
            "bond": rec["bond"],
            "reveal": min([d["reveal"] for d in (rec["a_to_b"], rec["b_to_a"]) if d]),
            "hasSecret": any(d.get("secret") for d in (rec["a_to_b"], rec["b_to_a"]) if d),
        })

    # ── groups: the up: tree, which the renderer collapses at low zoom ──
    groups = {}
    for stem, n in nodes.items():
        if n["factionLabel"]:
            gid = slug(n["factionLabel"])
            g = groups.setdefault(gid, {
                "id": gid, "label": n["factionLabel"], "kind": "faction",
                "realm": n["realm"], "members": []})
            g["members"].append(n["id"])
            if not g["realm"]:
                g["realm"] = n["realm"]

    # ── node reveal: you meet a character when you meet their first edge ──
    first_seen = defaultdict(lambda: 99)
    for e in edges:
        first_seen[e["a"]] = min(first_seen[e["a"]], e["reveal"])
        first_seen[e["b"]] = min(first_seen[e["b"]], e["reveal"])
    for n in nodes.values():
        n["reveal"] = first_seen.get(n["id"], 1)
        n["degree"] = sum(1 for e in edges if n["id"] in (e["a"], e["b"]))

    return nodes, edges, groups, report


# ── layout ───────────────────────────────────────────────────────────
# A drawn character is not a dot, it is a label box: the name, the faction
# under it, and the circle. Roughly this many pixels, and packing dots instead
# of boxes is why the dense realm still read as a pile after relaxation — the
# circles were comfortably apart and the names were on top of each other.
LABEL_W, LABEL_H = 132, 46


def layout(nodes, edges, groups, seed=7):
    """Deterministic, hierarchy-first, then relaxed against label boxes.

    The live force simulation is why the old map was unreadable: it settled at
    1538x3138 in a 1260x764 canvas, put the whole world in 29% of the width,
    and settled somewhere different on every load, so no reader could ever
    build a mental map of it. Positions are computed once, here, and shipped.
    The map stops moving and starts being a place.
    """
    import math

    by_realm = defaultdict(list)
    for n in nodes.values():
        by_realm[n["realm"] or "—"].append(n)

    # Each realm gets an area proportional to its population, so Arvela — half
    # the cast — does not get the same wedge as Nadir, which has one member.
    # Equal slices are most of why the old centre looked like a pile.
    realms = sorted(by_realm, key=lambda r: (-len(by_realm[r]), r))
    def radius_for(count):
        return math.sqrt(count * LABEL_W * LABEL_H / math.pi) * 1.35

    # Ring big enough that the two largest realms do not touch.
    sized = [(r, radius_for(len(by_realm[r]))) for r in realms]
    outer = [(r, rad) for r, rad in sized if r != "—"]
    ring = (sum(rad for _, rad in outer) / math.pi) * 1.25 if outer else 0

    placed, realm_centres = {}, {}
    total = sum(len(by_realm[r]) for r in realms if r != "—") or 1
    angle = -math.pi / 2
    for r, rad in sized:
        members = by_realm[r]
        if r == "—":
            # No realm is not a territory: those characters belong in the
            # middle, not in a wedge of their own.
            realm_centres[r] = (0.0, 0.0)
            continue
        span = 2 * math.pi * len(members) / total
        mid = angle + span / 2
        cx, cy = math.cos(mid) * ring, math.sin(mid) * ring
        realm_centres[r] = (cx, cy)
        angle += span

    # Inside a realm, factions are neighbourhoods; inside a faction,
    # phyllotaxis keeps the cluster round at any size with nothing to tune.
    for r, members in by_realm.items():
        rcx, rcy = realm_centres[r]
        by_fac = defaultdict(list)
        for n in members:
            by_fac[n["factionLabel"] or "—"].append(n)
        facs = sorted(by_fac, key=lambda f: (-len(by_fac[f]), f))
        spread = radius_for(len(members)) * 0.62
        for fi, f in enumerate(facs):
            if len(facs) == 1:
                fcx, fcy = rcx, rcy
            else:
                a = 2 * math.pi * fi / len(facs) - math.pi / 2
                fcx = rcx + math.cos(a) * spread
                fcy = rcy + math.sin(a) * spread
            group = sorted(by_fac[f], key=lambda n: (-n["degree"], n["stem"]))
            for k, n in enumerate(group):
                rr = 0.62 * LABEL_W * math.sqrt(k)
                th = k * 2.39996
                placed[n["id"]] = [fcx + math.cos(th) * rr,
                                   fcy + math.sin(th) * rr * 0.72]

    # Relaxation. Seeded, fixed iteration count, so two builds of the same
    # vault produce byte-identical coordinates and the map is in the same
    # place tomorrow as it was today.
    anchors = {i: list(p) for i, p in placed.items()}
    adj = [(e["a"], e["b"]) for e in edges if e["a"] in placed and e["b"] in placed]
    keys = sorted(placed)
    # Separation is measured in label boxes, not radii: the ellipse is wide
    # and short because that is the shape of a name with a faction under it.
    ax, ay = LABEL_W * 0.92, LABEL_H * 1.15
    for step in range(420):
        t = 1 - step / 420
        for a, b in adj:
            pa, pb = placed[a], placed[b]
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            d = math.hypot(dx, dy) or 1
            pull = (d - 260) * 0.010 * t
            ux, uy = dx / d * pull, dy / d * pull
            pa[0] += ux; pa[1] += uy
            pb[0] -= ux; pb[1] -= uy
        for i in range(len(keys)):
            pa = placed[keys[i]]
            for j in range(i + 1, len(keys)):
                pb = placed[keys[j]]
                dx, dy = (pb[0] - pa[0]) / ax, (pb[1] - pa[1]) / ay
                d2 = dx * dx + dy * dy
                if 1e-6 < d2 < 1:
                    d = math.sqrt(d2)
                    push = (1 - d) * 0.5
                    ux, uy = dx / d * push * ax, dy / d * push * ay
                    pa[0] -= ux; pa[1] -= uy
                    pb[0] += ux; pb[1] += uy
        for k in keys:
            p, a = placed[k], anchors[k]
            p[0] += (a[0] - p[0]) * 0.03
            p[1] += (a[1] - p[1]) * 0.03

    # Normalise to a positive origin so the renderer never meets a negative
    # bounding box.
    minx = min(p[0] for p in placed.values()) - LABEL_W
    miny = min(p[1] for p in placed.values()) - LABEL_H
    for n in nodes.values():
        p = placed.get(n["id"])
        if p:
            n["x"], n["y"] = round(p[0] - minx, 1), round(p[1] - miny, 1)
    for g in groups.values():
        pts = [placed[m] for m in g["members"] if m in placed]
        if pts:
            g["x"] = round(sum(p[0] for p in pts) / len(pts) - minx, 1)
            g["y"] = round(sum(p[1] for p in pts) / len(pts) - miny, 1)

    out = {}
    for r, (cx, cy) in realm_centres.items():
        pts = [placed[n["id"]] for n in by_realm[r] if n["id"] in placed]
        out[r] = {"x": round(sum(p[0] for p in pts) / len(pts) - minx, 1),
                  "y": round(sum(p[1] for p in pts) / len(pts) - miny, 1),
                  "r": round(radius_for(len(by_realm[r])), 1),
                  "count": len(by_realm[r])}
    return out


def render_html(data, template, out):
    """Inline the data and the vocabulary into the single-file map.

    The vocabulary is emitted from `vocab.py` rather than restated in the
    template, because the old map kept its colour table in the HTML by hand
    and it drifted: `hatred` existed in the vault for weeks and was painted
    neutral grey because nobody had added it in both places.
    """
    js = "\n".join([
        f"const FACET_COLOUR = {json.dumps(FACET_COLOUR)};",
        f"const FACET_LABEL = {json.dumps({k: v[0] for k, v in FACETS.items()}, ensure_ascii=False)};",
        f"const KIND_TO_FACET = {json.dumps(KIND_TO_FACET)};",
        f"const KIND_ES = {json.dumps(KIND_ES, ensure_ascii=False)};",
        f"const BOND_FAMILY = {json.dumps(BOND_FAMILY)};",
        f"const BOND_COLOUR = {json.dumps(BOND_COLOUR)};",
        f"const BOND_ES = {json.dumps(BOND_ES, ensure_ascii=False)};",
        f"const BOND_FAMILY_ES = {json.dumps(BOND_FAMILY_ES, ensure_ascii=False)};",
        f"const BOND_INVERSE = {json.dumps(BOND_INVERSE)};",
    ])
    html = Path(template).read_text(encoding="utf-8")
    # `</script>` inside the JSON payload would close the host tag early
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/", payload).replace("/*__VOCAB__*/", js)
    Path(out).write_text(html, encoding="utf-8")
    return len(html)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out = Path(sys.argv[2] if len(sys.argv) > 2 else root / "map-data.json")
    nodes, edges, groups, report = build(root)
    realms = layout(nodes, edges, groups)

    data = {
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": edges,
        "groups": sorted(groups.values(), key=lambda g: g["id"]),
        "realms": realms,
        "reveals": [
            {"level": 1, "label": "Lo público"},
            {"level": 2, "label": "Lo que se rumorea"},
            {"level": 3, "label": "Lo secreto"},
        ],
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tpl = Path(__file__).resolve().parent / "template.html"
    html_out = out.parent / "orvalle-map.html"
    size = render_html(data, tpl, html_out)

    print(f"→ {out}")
    print(f"→ {html_out}  ({size/1024:.0f} KB, sin dependencias externas)")
    print(f"  {len(nodes)} personajes · {len(edges)} pares · {len(groups)} facciones")
    both = sum(1 for e in edges if e["aToB"] and e["bToA"])
    print(f"  reciprocidad: {both}/{len(edges)} ({100*both//max(1,len(edges))}%)")
    withsec = sum(1 for e in edges if e["hasSecret"])
    print(f"  lecturas secretas: {report['secret_readings']} "
          f"en {withsec} relaciones ({100*withsec//max(1,len(edges))}%)")

    print("\n── a corregir en el vault ──")
    if report["unknown_kinds"]:
        print(f"  {sum(report['unknown_kinds'].values())} relations: fuera de vocabulario")
        for k, c in report["unknown_kinds"].most_common(12):
            print(f"     {k}")
    if report["legacy_spellings"]:
        print(f"  {sum(report['legacy_spellings'].values())} grafías heredadas")
        for k, c in report["legacy_spellings"].most_common(8):
            print(f"     {c}x  {k}")
    if report["unresolved_targets"]:
        print(f"  {len(report['unresolved_targets'])} destinos sin artículo")
        for k, _ in report["unresolved_targets"].most_common(8):
            print(f"     {k}")
    if report["one_sided"]:
        print(f"  {len(report['one_sided'])} relaciones declaradas por un solo lado")
        for k in report["one_sided"][:8]:
            print(f"     {k}")
    if report["shape_deviations"]:
        print(f"  {len(report['shape_deviations'])} artículos con `relations:` mal formado")
        for k, _ in report["shape_deviations"].most_common():
            print(f"     {k}  (lista de enlaces sin tipo)")
    if report["unstructured_sections"]:
        print(f"  {len(report['unstructured_sections'])} secciones Relationships en prosa libre")
        print(f"     {', '.join(report['unstructured_sections'])}")


if __name__ == "__main__":
    main()
