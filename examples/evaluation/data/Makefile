FUGAKU ?= fugaku
TARBALLS = tadashi-results.tgz ml4t-results.tgz tadashi-check.tgz

data:
	scp $(addprefix $(FUGAKU):,$(TARBALLS)) .
	tar xvf tadashi-results.tgz
	tar xvf ml4t-results.tgz
	mkdir -p evo
	mv st-evo mt-evo evo
	mkdir -p check
	tar xvf tadashi-check.tgz -C check

analyze:
	python3 collect_results.py
	MPLCONFIGDIR=/tmp/matplotlib python3 report_results.py

test:
	python3 -m unittest -v test_analysis.py

clean:
	rm -rf `find -maxdepth 1 -mindepth 1 -type d -not -name check` *.tgz

.PHONY: data analyze test clean
