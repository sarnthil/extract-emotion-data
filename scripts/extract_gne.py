import re
import json
import os

from cause_io import Instance, tokens_and_roles_from_text_and_annotations

meta = {"domain": "headlines", "annotation": "crowdsourcing"}

dataset = "gne"

role_annotations = ["cause", "cue", "experiencer", "target"]


def extract():
    with open("sources/gne/gne.jsonl") as f:
        for line in f:
            data = json.loads(line)
            text = data["headline"]
            tags = []
            headline = text
            emotion = data["annotations"]["dominant_emotion"]["gold"]
            annotations = {}
            for role in role_annotations:
                if len(data["annotations"][role]["gold"]) == 0:
                    annotation_for_role = []
                else:
                    annotation_for_role = data["annotations"][role]["gold"][0]
                if annotation_for_role == ["none"]:
                    annotation_for_role = []
                (
                    tokens,
                    role_annotation,
                ) = tokens_and_roles_from_text_and_annotations(
                    headline, annotation_for_role
                )
                annotations[role] = role_annotation
                tags.append(f"{role}-{['no', 'yes'][bool(annotation_for_role)]}")
            yield Instance(
                text=text,
                emotions=[emotion],
                tokens=tokens,
                tags=tags,
                annotations=annotations,
            )
