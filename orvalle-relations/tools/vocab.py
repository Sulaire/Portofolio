"""The closed vocabularies the map is allowed to colour by.

Everything here is a *machine* value. The human phrase a writer actually wrote
travels beside it as `label` and is never normalised away — `subordinate she
cannot remove` is better writing than `rival` and the map shows both: the kind
picks the colour, the label is what you read.

Nothing in this file guesses. `wiki_map.py` grew a SYNONYMS table and an
`infer_type()` that matched substrings against prose, which is how `hatred`
ended up painted neutral grey: the vocabulary was open, so the renderer had to
gamble. Closing it here means an unknown value is reported at build time and
fixed at the source, once.
"""

# ── Sentiment: how they FEEL. One axis. ──────────────────────────────
# facet -> the kinds that share its colour.  Order is the legend order.
FACETS = {
    "love":       ("Amor / romance",        ["love"]),
    "kin":        ("Sangre",                ["kin"]),
    "loyalty":    ("Lealtad / devoción",    ["devotion", "sworn-loyalty"]),
    "friendship": ("Amistad / confianza",   ["friendship", "trust"]),
    "political":  ("Alianza política",      ["ally", "cautious-ally"]),
    "regard":     ("Estima / admiración",   ["admiration", "respect"]),
    "complex":    ("Complejo / ambivalente", ["complicated", "ambivalent"]),
    "tension":    ("Tensión / rivalidad",   ["rival", "resentment"]),
    "hostility":  ("Hostilidad",            ["contempt", "enemy", "hatred"]),
    "distance":   ("Miedo / lástima",       ["fear", "pity"]),
    "unknown":    ("Sin declarar",          ["unknown"]),
}

KIND_TO_FACET = {k: f for f, (_, kinds) in FACETS.items() for k in kinds}
KINDS = set(KIND_TO_FACET)

# How far the sidebar bar fills, and which way it leans.
#
# This is a property of the VOCABULARY WORD, not a measurement of a particular
# relationship. `hatred` is a stronger word than `rival` in every sentence it
# appears in, so the bar can say so honestly. What it deliberately is not is
# the old per-pair `value`: nobody could assign −100..+100 consistently, the
# wiki has no such scale, and 67 of the old map's 142 edges carried a 0 that
# the bar then drew as "neutral" when it meant "nobody said".
#
# weight 0..1 fills the bar; valence −1/0/+1 picks the side and the colour.
KIND_WEIGHT = {
    "love": 1.0, "hatred": 1.0, "devotion": .95, "sworn-loyalty": .95,
    "enemy": .85, "kin": .8, "trust": .75, "friendship": .75, "contempt": .7,
    "admiration": .6, "resentment": .6, "rival": .6, "respect": .55,
    "ally": .55, "fear": .5, "complicated": .45, "cautious-ally": .4,
    "pity": .35, "ambivalent": .3, "unknown": 0.0,
}

KIND_VALENCE = {
    "love": 1, "kin": 0, "devotion": 1, "sworn-loyalty": 1,
    "friendship": 1, "trust": 1, "ally": 1, "cautious-ally": 1,
    "admiration": 1, "respect": 1, "complicated": 0, "ambivalent": 0,
    "rival": -1, "resentment": -1, "contempt": -1, "enemy": -1,
    "hatred": -1, "fear": -1, "pity": 0, "unknown": 0,
}

# Spelling variants that already exist in the vault. This is a MIGRATION aid,
# not a licence to keep inventing: `lint_relations.py` reports every use so the
# article can be fixed, and the table should shrink to nothing.
LEGACY_SPELLINGS = {
    "sworn loyalty": "sworn-loyalty",
    "cautious ally": "cautious-ally",
    "old friendship": "friendship",
    "lost friend": "friendship",
    "frustrated friendship": "friendship",
    "father of": "kin",
    "progenitor": "kin",
    "brother, mutual contempt": "contempt",
    "elder brother, mutual contempt": "contempt",
    "killed and sealed by": "enemy",
    "killed by": "enemy",
    "intends to kill": "enemy",
    "absorbed his error": "complicated",
    "forced counterpart": "complicated",
    "uneasy ally": "cautious-ally",
    "subordinate she cannot remove": "rival",
    "rival across the two blood seats": "rival",
    "dissenter": "rival",
    "obstacle": "rival",
    "confronted by": "rival",
    "former liege": "complicated",
    "fixed point": "devotion",
    "worshipped as god": "devotion",
    "unknowing contact": "unknown",
    "sought": "unknown",
    "called it": "unknown",
    "the mechanism": "unknown",
    "contemplative wing": "unknown",
    "militant wing": "unknown",
}

# ── Structure: what they ARE to each other. The second axis. ─────────
BOND_FAMILY = {
    "parent": "blood", "child": "blood", "sibling": "blood", "twin": "blood",
    "spouse": "blood", "lover": "blood", "kin": "blood",
    "ancestor": "blood", "descendant": "blood",
    "liege": "power", "vassal": "power", "commander": "power",
    "subordinate": "power", "master": "power", "apprentice": "power",
    "owner": "power", "captive": "power", "patron": "power", "client": "power",
    "retainer": "power", "principal": "power",
    "friend": "chosen", "peer": "chosen", "rival": "chosen",
    "guardian": "chosen", "ward": "chosen",
    "handler": "info", "informant": "info",
}
BONDS = set(BOND_FAMILY)

BOND_INVERSE = {
    "parent": "child", "child": "parent", "sibling": "sibling", "twin": "twin",
    "spouse": "spouse", "lover": "lover", "kin": "kin",
    "ancestor": "descendant", "descendant": "ancestor",
    "liege": "vassal", "vassal": "liege",
    "commander": "subordinate", "subordinate": "commander",
    "master": "apprentice", "apprentice": "master",
    "owner": "captive", "captive": "owner",
    "patron": "client", "client": "patron",
    "retainer": "principal", "principal": "retainer",
    "friend": "friend", "peer": "peer", "rival": "rival",
    "guardian": "ward", "ward": "guardian",
    "handler": "informant", "informant": "handler",
}

BOND_ES = {
    "parent": "progenitor", "child": "hijo/a", "sibling": "hermano/a",
    "twin": "gemelo/a", "spouse": "cónyuge", "lover": "amante", "kin": "pariente",
    "ancestor": "antepasado", "descendant": "descendiente",
    "liege": "señor", "vassal": "vasallo", "commander": "capitán",
    "subordinate": "subordinado", "master": "maestro", "apprentice": "discípulo",
    "owner": "dueño", "captive": "cautivo", "patron": "patrón", "client": "cliente",
    "retainer": "servidor jurado", "principal": "a quien sirve",
    "friend": "amigo", "peer": "par", "rival": "rival",
    "guardian": "tutor", "ward": "pupilo",
    "handler": "enlace", "informant": "informante",
}

BOND_FAMILY_ES = {
    "blood": "Sangre y casa", "power": "Mando y servicio",
    "chosen": "Elegido", "info": "Canal de información",
}

# ── Spanish for the sentiment kinds, so the reader never meets a slug ──
KIND_ES = {
    "love": "amor", "kin": "sangre", "devotion": "devoción",
    "sworn-loyalty": "lealtad jurada", "friendship": "amistad",
    "trust": "confianza", "ally": "aliado", "cautious-ally": "aliado cauto",
    "admiration": "admiración", "respect": "respeto",
    "complicated": "complicada", "ambivalent": "ambivalente",
    "rival": "rivalidad", "resentment": "resentimiento",
    "contempt": "desprecio", "enemy": "enemistad", "hatred": "odio",
    "fear": "miedo", "pity": "lástima", "unknown": "sin declarar",
}


def normalise_kind(raw):
    """(kind, was_legacy). Returns (None, False) for anything unrecognised.

    Never guesses. An unknown value comes back as None so the caller can
    report it rather than quietly colouring it grey.
    """
    if not raw:
        return None, False
    s = str(raw).strip().lower()
    if s in KINDS:
        return s, False
    if s in LEGACY_SPELLINGS:
        return LEGACY_SPELLINGS[s], True
    hyphened = s.replace(" ", "-")
    if hyphened in KINDS:
        return hyphened, True
    return None, False


# Colours live beside the vocabulary they colour, and are emitted into the
# renderer at build time. Keeping a second copy in the HTML is what let the
# two drift apart.
FACET_COLOUR = {
    "love":       "#E8608F",
    "kin":        "#C97E9A",
    "loyalty":    "#E0A431",
    "friendship": "#5FBE6E",
    "political":  "#5AA8D0",
    "regard":     "#7FC4B0",
    "complex":    "#8A70C0",
    "tension":    "#E07A34",
    "hostility":  "#D24444",
    "distance":   "#7E8C9A",
    "unknown":    "#5A544A",
}

BOND_COLOUR = {
    "blood":  "#C97E9A",
    "power":  "#C9973A",
    "chosen": "#7FA88C",
    "info":   "#8F7AB0",
}
