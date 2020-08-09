from collections import defaultdict, Counter
from itertools import zip_longest
from xml.etree.ElementTree import parse

from cause_io import Instance


def join_spans(spans):
    last = None
    for s2, e2 in sorted(set(spans)):
        if not last:
            last = s2, e2
            continue
        s1, e1 = last
        if e1 < s2:
            yield last
            last = s2, e2
            continue
        last = s1, e2
    if last:
        yield last


def span_borders(span, text):
    return (
        span.text == text[int(span.attrib["cbegin"]) : int(span.attrib["cend"])]
    )


def clean_text(string):
    return string.replace("\t", " ")


def offsets_from_relations(relations, id_to_span, side="target"):
    offsets = []
    for relation in relations:
        # source_span = id_to_span[relation.attrib["source_annotation_id"]]  # cue
        # target_span = id_to_span[
        #     relation.attrib["target_annotation_id"]
        # ]  # target/experiencer/...
        # ಠ_ಠ
        # assert span_borders(source_span, text)
        # assert span_borders(target_span, text)

        try:
            offsets.append(
                (
                    int(
                        id_to_span[
                            relation.attrib[f"{side}_annotation_id"]
                        ].attrib["cbegin"]
                    ),
                    int(
                        id_to_span[
                            relation.attrib[f"{side}_annotation_id"]
                        ].attrib["cend"]
                    ),
                )
            )
        except KeyError:
            pass  # ಠ_ಠ
    return list(join_spans(offsets))


def annotations_from_offsets(text, offsets):
    offset = 0
    role_annotations, tokens = [], []
    state = "O"
    for word in text.split(" "):
        if not word:
            offset += 1
            continue
        start = offset
        end = start + len(word)
        tokens.append(word)
        if any(ostart < end and oend > start for (ostart, oend) in offsets):
            state = "BI"[state in "BI"]
        else:
            state = "O"
        role_annotations.append(state)
        offset += 1 + len(word)
    return tokens, role_annotations


def extract():
    tree = parse("sources/reman/reman-version1.0.xml")

    for document in tree.iterfind("document"):
        text = document.find("text").text.replace("\t", " ")
        id_to_span = {
            span.attrib["annotation_id"]: span
            for span in document.find("adjudicated")
            .find("spans")
            .iterfind("span")
        }
        role_relations = defaultdict(list)
        for relation in (
            document.find("adjudicated").find("relations").iterfind("relation")
        ):
            relation_type = relation.attrib["type"]
            # if relation_type != "cause":
            #     continue
            role_relations[relation_type].append(relation)

        annotations = {}
        for role in role_relations:
            offsets = offsets_from_relations(
                role_relations[role], id_to_span, side="target"
            )
            tokens, annotations[role] = annotations_from_offsets(text, offsets)

        emotions = set()
        cue_offsets = defaultdict(list)
        for span in document.find("adjudicated").find("spans").iterfind("span"):
            if "negated" in span.attrib.get("modifier", ""):
                continue
            if span.attrib["type"] not in {
                "joy",
                "sadness",
                "disgust",
                "anger",
                "surprise",
                "fear",
                "anticipation",
                "trust",
                "other",  # ಠ_ಠ
            }:
                continue

            emotions.add(span.attrib["type"])
            cue_offsets[span.attrib["type"]].append((int(span.attrib["cbegin"]), int(span.attrib["cend"])))

        for emotion in cue_offsets:
            tokens, annotations[f"cue-{emotion}"] = annotations_from_offsets(text, cue_offsets[emotion])

        if not emotions:
            emotions = ["noemo"]

        yield Instance(
            text=text,
            tokens=tokens,
            emotions=list(emotions),
            annotations=annotations,
        )


meta = {"domain": "literature", "annotation": "expert"}
dataset = "reman"
