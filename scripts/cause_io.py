import re
from types import SimpleNamespace


class Instance(SimpleNamespace):
    pass


def despacify(string):
    return re.sub(r"\s+", " ", string.replace("\n", " "))


def iobify(mutant):
    state = "O"
    for token in re.findall(r"◊[^◊]+◊|\S+", mutant):
        if "◊" in token:
            token = token.strip("◊")
            state = "BI"[state != "O"]
        else:
            state = "O"
        yield (token, state)


def adjust_edges(outer, inner):
    """
    outer: foo bar bat ham spam
    inner: ar bat ha
    returns: bar bat ham
    """
    # :(
    # assert inner in outer, f"WTF: {inner} NOT IN {outer}"
    orig_outer = outer
    outer = outer.lower()
    inner = inner.lower()
    left = outer.find(inner)
    right = left + len(inner)
    while left != 0 and outer[left-1] != " ":
        left -= 1
    while right != len(outer) and outer[right] != " ":
        right += 1
    return orig_outer[left:right]


def replace(match):
    return re.sub(
        r"([^\s]+)", r"◊\1◊", match.string[match.start() : match.end()]
    )


def tokens_from_text_and_annotations(text, annotations):
    # 1567 / 8964 cases give us problems (we don't find the annotation)
    global BAD, TOTAL
    text = despacify(text).strip()
    orig_text = text
    for annotation in annotations:
        annotation = despacify(annotation).strip()
        annotation = adjust_edges(text, annotation)
        text = re.sub(
            rf"(^|\s){re.escape(annotation)}(\s|$)",
            replace,
            text,
            flags=re.IGNORECASE,
        )

    return list(iobify(text))

def tokens_and_roles_from_text_and_annotations(text, annotations):
    """ [(foo, bar), (ham, spam)] -> ([foo, ham], [bar, spam])"""
    data = tokens_from_text_and_annotations(text, annotations)
    return [x[0] for x in data], [x[1] for x in data]
