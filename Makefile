all: workdata/splitted.json

.PHONY: all clean

clean:
	rm -rf workdata/*

workdata:
	mkdir workdata

# extracting datasets
workdata/extracted.json: scripts/extract.py workdata
	python3 scripts/extract.py >workdata/extracted.json

# tokenize datasets
workdata/tokenized.json: scripts/retokenize.py workdata/extracted.json
	python3 scripts/retokenize.py <workdata/extracted.json >workdata/tokenized.json

# split datasets and select instances for manual annotation
workdata/splitted.json: scripts/split.py workdata/tokenized.json
	python3 scripts/split.py workdata/tokenized.json >outputs/splitted.json

# extract clauses from all datasets
# workdata/clausified.json: scripts/clausify.py
# 	python3 scripts/clausify.py workdata/splitted-with-manual.json >workdata/clausified.json
