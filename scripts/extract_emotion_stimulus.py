import re
import json
from cause_io import Instance

role = "cause"
pB = re.compile(r"^<[^>]+>")
pE = re.compile(r"<[^>]+>$")
emotion_pattern = re.compile(r"^<([^>]+)>")
tag_pattern = re.compile(r"<[^>]+?>")


def process_line(line):
    yield emotion_pattern.findall(line)[0]
    line = pB.sub("", pE.sub("", line))
    line = line.replace("<cause>", " <cause> ")
    line = line.replace(r"<\cause>", r" <\cause> ")
    state = "O"
    yield line
    for word in line.split():
        if word == "<cause>":
            state = "B"
            continue
        elif word == "<\cause>":
            state = "O"
            continue
        else:
            yield (word, state)
            if state == "B":
                state = "I"


def extract():
    for filename in [
        "sources/emotion-stimulus/emotion-cause/Dataset/Emotion Cause.txt",
        "sources/emotion-stimulus/emotion-cause/Dataset/No Cause.txt",
    ]:
        with open(filename) as f:
            for line in f:
                processor = process_line(line)
                emotion = next(processor)
                text_proc = next(processor)
                text = tag_pattern.sub("", text_proc.strip())
                tokens, causes = zip(*processor)
                yield Instance(
                    text=text,
                    tokens=tokens,
                    emotions=[emotion],
                    extra={"line": line},
                    annotations={"cause": causes},
                )


meta = {
    "domain": "framenet",
    "annotation": "expert",
}
dataset = "emotion-stimulus"
