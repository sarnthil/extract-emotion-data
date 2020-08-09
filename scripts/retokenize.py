# [(token1, tag1), (token2, tag2), ...] -> [(token1_fixed, tag1), ...]
import json
import spacy
import fileinput
from twokenize import tokenizeRawTweetText as twok

nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger", "parser"])


def dehtmlentitify(text):
    return text.replace("&amp", "&").replace("&lt", "<").replace("&gt", ">")


def realign(new, old, tags):
    new = list(reversed(new))
    old = list(reversed(old))
    tags = list(reversed(tags))
    while new or old:
        n = new.pop()
        o = old.pop()
        t = tags.pop()
        if n == o:
            yield t
            continue
        if o.startswith(n):
            yield t
            old.append(o[len(n) :])
            tags.append(t if t != "B" else "I")
            continue
        assert False, f"Tokenizer joined stuff seperated by spaces: {o} vs {n}"
    assert not any([new, old, tags])


def spacytok(text):
    return [word.text for word in nlp(text)]


def tokenize(tokens, annotations, tokenizer=spacytok):
    tokens_orig = tokens
    text = dehtmlentitify(" ".join(tokens_orig))
    tokens_orig = text.split(" ")
    tokenized = tokenizer(text)  # list of tokens
    assert text.replace(" ", "") == "".join(
        tokenized
    ), f"Original: <{text.split()}>, New: <{tokenized}>"
    return tokenized, {
        role: list(realign(tokenized, tokens_orig, annotations[role]))
        for role in annotations
    }

for line in fileinput.input():
    data = json.loads(line)
    if data["meta"]["domain"] == "tweets":
        data["tokens"], data["annotations"] = tokenize(data["tokens"], data["annotations"], tokenizer=twok)
    else:
        data["tokens"], data["annotations"] = tokenize(data["tokens"], data["annotations"])
    data["steps"].append("tokenize")
    print(json.dumps(data))
