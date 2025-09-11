all : st_improvements.pdf mt_improvements.pdf
st_improvements.pdf :
	./plot.py measure_st.sh-78953.txt --pluto ../pluto/measure_st.sh-78869.txt  --mcts ../mcts/data.csv

mt_improvements.pdf :
	./plot.py measure_mt.sh-79199.txt --pluto ../pluto/measure_mt.sh-78896.txt --mcts ../mcts/data-mt.csv

comparison.pdf:
	./plot2.py measure_st.sh-78953.txt ../pluto/measure_st.sh-78869.txt ../mcts/data-st.csv measure_mt.sh-79199.txt ../pluto/measure_mt.sh-78896.txt ../mcts/data-mt.csv
