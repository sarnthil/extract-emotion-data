import json
import fileinput
import functools
from itertools import groupby

import spacy
from benepar.spacy_plugin import BeneparComponent
from nltk import Tree

nlp = spacy.load("en_core_web_sm", disable=["ner"])
benepar = BeneparComponent("benepar_en2")


def until_convergence(fn):
    @functools.wraps(fn)
    def wrapper(arg, *args, **kwargs):
        old = object()
        new = arg
        while old != new:
            old = new
            new = fn(old, *args, **kwargs)
        return new

    return wrapper


def join_tiny_clauses_with_next(clauses):
    # [["This", "is", "just"], ["because"], ["it", "is", "so"]]
    # [["This", "is", "just"], ["because", "it", "is", "so"]]
    clauses_rev = iter(reversed(clauses))

    fixed = []
    for clause in clauses_rev:
        if len(clause) < 2 and fixed:
            fixed[-1] = clause + fixed[-1]
            continue
        fixed.append(clause)
    return list(reversed(fixed))


@until_convergence
def punctuation_shuffler(clauses):
    def all_punctuation(clause):
        return not any(
            set(word)
            & set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
            for word in clause
        )

    queue = []
    to_prepend = None
    for clause in clauses:
        if not queue:
            queue.append(clause)
            continue
        if clause[0] == '"' and all_punctuation(clause):
            if to_prepend:
                queue.append(to_prepend + clause)
                to_prepend = None
            else:
                queue[-1].append('"')
                to_prepend = clause[1:]
        elif all_punctuation(clause):
            if to_prepend:
                queue[-1].extend(to_prepend + clause)
                to_prepend = None
            else:
                queue[-1].extend(clause)
        elif all_punctuation([clause[0]]) and clause[0] != '"':
            if to_prepend:
                queue.append(to_prepend + clause)
                to_prepend = None
            elif len(clause) <= 3:
                queue[-1].append(clause[0])
                to_prepend = clause[1:]
            else:
                queue[-1].append(clause[0])
                queue.append(clause[1:])
        elif len(clause) <= 3:  # Laura forced me, could be changed two 2
            if to_prepend:
                queue.append(to_prepend + clause)
                to_prepend = None
            else:
                to_prepend = clause
        else:
            if to_prepend:
                clause = to_prepend + clause
                to_prepend = None
            queue.append(clause)
    if to_prepend:
        queue[-1].extend(to_prepend)

    if queue[0] == ['"'] and len(queue) > 1:
        queue.pop(0)
        queue[0].insert(0, '"')

    return queue


for line in fileinput.input():
    data = json.loads(line)

    tokens, tags = list(zip(*data["tokens"]))
    doc = nlp.tokenizer.tokens_from_list(
        [token.replace("(", "-LBR-").replace(")", "-RBR-") for token in tokens]
    )
    nlp.tagger(doc)  # benepar assumes a tagged doc
    nlp.parser(doc)  # needed this to split into sentences
    benepar(doc)

    assert len(doc) == len(
        tags
    ), f"size mismatch: tags:{tags} {len(tags)}, text:{doc} {len(doc)}"

    all_clauses = []

    for sent in doc.sents:
        t = Tree.fromstring(sent._.parse_string)
        all_leaves = t.leaves()
        wordidx2treeidx = [None] * len(all_leaves)
        for i, subtree in enumerate(t.subtrees()):
            if subtree.label() not in ("S", "SBAR", "SBARQ", "SINV", "SQ"):
                continue
            leaves = subtree.leaves()
            whole_tree = " ".join(all_leaves)
            index = whole_tree.index(" ".join(leaves))
            num_prewords = whole_tree[:index].count(
                " "
            )  # how many words before this subtree
            for j in range(num_prewords, num_prewords + len(leaves)):
                wordidx2treeidx[j] = i
        # Now we have a list that corresponds to the words and tells us which
        # word belongs to which subtree

        leaf_agenda = all_leaves[::-1]

        clauses = []
        for stidx, grouper in groupby(wordidx2treeidx):
            grouper = list(grouper)
            clauses.append([leaf_agenda.pop() for _ in range(len(list(grouper)))])

        # Done with naive clause segmentation in sentence based on constituency trees

        clauses = punctuation_shuffler(clauses)
        clauses = join_tiny_clauses_with_next(clauses)

        all_clauses.extend(clauses)

    # align tags with the tokens in the clauses:
    assert sum(len(clause) for clause in all_clauses) == len(tags)
    rtags = list(reversed(tags))
    if "clauses" in data:
        key = "clauses-predicted"
    else:
        key = "clauses"

    data[key] = [
        [
            (token.replace("-LBR-", "(").replace("-RBR-", ")"), rtags.pop())
            for token in clause
        ]
        for clause in all_clauses
    ]
    assert not rtags

    data["steps"].append("clausify")
    print(json.dumps(data))
