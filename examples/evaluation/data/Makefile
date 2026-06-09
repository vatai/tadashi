data:
	scp fugaku:tadashi-results.tgz fugaku:ml4t-results.tgz .
	tar xvf tadashi-results.tgz
	tar xvf ml4t-results.tgz

analyze:
	python3 collect_results.py
	MPLCONFIGDIR=/tmp/matplotlib python3 report_results.py

test:
	python3 -m unittest -v test_analysis.py

clean:
	rm -rf `find -maxdepth 1 -mindepth 1 -type d` *.tgz

.PHONY: data analyze test clean
