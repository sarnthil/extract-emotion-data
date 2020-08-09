import os
from io import StringIO
import re
from collections import defaultdict, Counter
from itertools import zip_longest, chain
from xml.etree.ElementTree import parse, Element
from xml.parsers import expat

from cause_io import (
    Instance,
    tokens_from_text_and_annotations,
    despacify,
)

oldcreate = expat.ParserCreate
expat.ParserCreate = lambda encoding, sep: oldcreate(encoding, None)

FUCKERY = re.compile(r"###([^#]+)#\d#")


def fix_xml(filename):
    """Remove BOM and solve xml issues."""
    io = StringIO()
    io.write("<root>")
    with open(filename) as f:
        for line in f:
            if "xml version" in line:
                continue
            io.write(line.replace("\uFEFF", ""))
        io.write("</root>")
    io.seek(0)
    return io


def unfuck(string):
    return FUCKERY.sub(r"\1", string)


def extract():
    text_to_info = defaultdict(lambda: defaultdict(set))
    for part in ["train", "test"]:
        fixed = fix_xml(f"sources/eca/{part}.xml")
        tree = parse(fixed)
        document = tree.find("{http://www.w3.org/2009/10/emotionml}emotionml")
        for i, document in enumerate(
            document.iterfind("{http://www.w3.org/2009/10/emotionml}emotion")
        ):
            emotion = document.find(
                "{http://www.w3.org/2009/10/emotionml}category"
            ).attrib["name"]
            clauses = []
            identifier = []
            for clause in document.iterfind(
                "{http://www.w3.org/2009/10/emotionml}clause"
            ):
                text = clause.find("{http://www.w3.org/2009/10/emotionml}text")
                if text is None:
                    # some clauses contain no text...
                    continue
                text = text.text
                identifier.append(text)
                cause = clause.find(
                    "{http://www.w3.org/2009/10/emotionml}cause"
                )
                if cause is None:
                    clauses.append([(word, "O") for word in text.split()])
                else:
                    cause_text = despacify(cause.text)
                    cause_text = unfuck(cause_text)
                    clauses.append(
                        tokens_from_text_and_annotations(text, [cause_text])
                    )
            identifier = despacify(" ".join(identifier))
            if not clauses or not identifier:
                continue
            text_to_info[identifier]["clauses"] = clauses
            text_to_info[identifier]["emotions"].add(emotion)

    for identifier in sorted(text_to_info):
        emotions = list(text_to_info[identifier]["emotions"])
        text = identifier
        clauses = text_to_info[identifier]["clauses"]
        tokens, causes = zip(*chain.from_iterable(clauses))
        yield Instance(
            emotions=emotions,
            text=text,
            # clauses=clauses,
            tokens=tokens,
            annotations={"cause": causes},
        )


meta = {"domain": "literature", "annotation": "expert"}
dataset = "eca"
