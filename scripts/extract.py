import sys
import json


extractors = ["reman", "eca", "gne", "emotion_stimulus", "electoral_tweets"]

for extractor in extractors:
    extractor = __import__(f"extract_{extractor}")
    for i, instance in enumerate(extractor.extract()):
        data = {
            "dataset": extractor.dataset,
            "id": f"{extractor.dataset}-{i}",
            "emotions": instance.emotions,
            "text": instance.text,
            "tokens": instance.tokens,
            "annotations": {
                anno_name: instance.annotations[anno_name] for anno_name in instance.annotations
            },
            "meta": extractor.meta,
            "steps": ["extract"],
            "tags": [],
        }
        for anno in data["annotations"]:
            assert len(data["tokens"]) == len(data["annotations"][anno])
        # if hasattr(instance, "clauses"):  # FIXME
        #     data["clauses"] = instance.clauses
        if hasattr(instance, "tags"):
            data["tags"].extend(instance.tags)
        if hasattr(instance, "extra"):
            data["extra"] = instance.extra

        json.dump(data, sys.stdout)
        print()
