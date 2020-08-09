import json
from random import shuffle, seed
from collections import defaultdict
import click


@click.command()
@click.argument("file", type=click.File("r"))
@click.option("--n-inspect", default=50)
def cli(file, n_inspect):
    dataset_to_ids = defaultdict(list)
    id_to_split = {}
    for line in file:
        data = json.loads(line)
        dataset_to_ids[data["dataset"]].append(data["id"])
    for dataset in dataset_to_ids:
        seed(0)
        shuffle(dataset_to_ids[dataset])
        l = len(dataset_to_ids[dataset])
        ntrain = int(0.8 * l)
        ntest = (l - ntrain)//2
        ndev = l - ntrain - ntest
        ids = iter(dataset_to_ids[dataset])
        for _, id_ in zip(range(ntrain), ids):
            id_to_split[id_] = "train"
        for _, id_ in zip(range(ntest), ids):
            id_to_split[id_] = "test"
        for _, id_ in zip(range(ndev), ids):
            id_to_split[id_] = "dev"
        try:
            next(ids)
        except StopIteration:
            pass
        else:
            raise RuntimeError("Leftover item")
    file.seek(0)
    for line in file:
        data = json.loads(line)
        data["split"] = id_to_split[data["id"]]
        data["steps"].append("split")
        print(json.dumps(data))


if __name__ == "__main__":
    cli()
