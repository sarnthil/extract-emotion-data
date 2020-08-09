import re
import csv
from pathlib import Path
from cause_io import (
    tokens_from_text_and_annotations,
    Instance,
)

TOKEN = re.compile(r"http\S+|(?:#|@)?[\w']+|[^\s\w]+")


class AnnotationError(Exception):
    def __init__(self, string):
        self.string = string


def simple_tokenize(string):
    return TOKEN.findall(string)


columnmap = {
    "cause": (
        "q8 what reason can be deduced from the tweet for the"
        "emotion what is the cause of the emotion"
    ).replace(" ", ""),
    "emotion": "q2whatemotionchooseoneoftheoptionsfrombelowthatbestrepresentstheemotion",
    "target": "q6towardswhomorwhatinotherwordswhoorwhatisthetargetoftheemotion",
    "experiencer": "q1whoisfeelingorwhofeltanemotioninotherwordswhoisthesourceoftheemotion",
    "cue": "fontcolorolivetweetertweetfontbrq7whichwordsinthetweethelpidentifyingtheemotion",
}

role_annotations = ["cause", "cue", "target", "experiencer"]


def process_line(line, role, err_handler=None):
    unitid = line["unitid"]
    text = line["tweet"]
    role_value = line[columnmap[role]]
    if not text:
        err_handler.write(f"NOTEXT\t{unitid}\t{text}\t{role_value}\n")
        raise AnnotationError("no text")
    emotions = [
        emo.strip() for emo in line[columnmap["emotion"]].strip().split(" or ")
    ]
    if not emotions:
        emotions = ["noemo"]
    yield emotions
    yield text

    role_value = role_value.replace("&", "&amp")
    if role_value not in text:
        if "," in role_value and all(
            part.strip() in text for part in role_value.split(",")
        ):
            annotations = [part.strip() for part in role_value.split(",")]
        elif ";" in role_value and all(
            part.strip() in text for part in role_value.split(";")
        ):
            annotations = [part.strip() for part in role_value.split(";")]
        else:
            annotations = []
            if err_handler:
                err_handler.write(
                    f"NOANNOTATION\t{unitid}\t{text}\t{role_value}\n"
                )
            # raise AnnotationError("can't find annotation")
    else:
        annotations = [role_value]
    yield {"annotations": annotations}
    yield tokens_from_text_and_annotations(text, annotations)


def extract():
    for batch in "12":
        with open(
            Path("sources")
            / "electoral-tweets"
            / "Annotated-US2012-Election-Tweets"
            / "Questionnaire2"
            / f"Batch{batch}"
            / "AnnotatedTweets.txt"
        ) as f:
            reader = csv.DictReader(f, dialect="excel-tab")
            with open("workdata/errors-et.tsv", "w") as err:
                for line in reader:
                    try:
                        if line["tweet"] is None:
                            continue

                        annotations = {}
                        for role in role_annotations:
                            processor = process_line(line, role, err_handler=err)
                            emotions = next(processor)
                            text = next(processor)
                            extra = next(processor)
                            (
                                tokens,
                                annotations[role],
                            ) = zip(
                                *next(processor)
                            )
                        yield Instance(
                            text=text,
                            emotions=emotions,
                            tokens=tokens,
                            # extra=extra,
                            annotations=annotations,
                        )
                    except AnnotationError as e:
                        continue


meta = {"domain": "tweets", "annotation": "crowdsourcing"}
dataset = "electoral_tweets"
