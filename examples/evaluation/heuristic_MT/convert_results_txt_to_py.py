
f = open("results_heuristic_mt_genoa.py", "w")
f1 = open("heuristic_mt_genoa.txt")

f.write("speedups={\n")
line = f1.readline()
while line != "":
    line = line.strip()
    if line == "[STARTING NEW APP]":
        line = f1.readline().strip()
        name = line.split("/")[-1]
    if "Baseline measure" in line:
        bl = float(line.split(": ")[-1])
    if "Tiling with size 32: " in line:
        nv = float(line.split(": ")[-1])
        spd = bl/nv
        f.write("\"%s_baseline\": %f,\n"%(name, bl))
        f.write("\"%s_modified\": %f,\n"%(name, nv))
        f.write("\"%s_speedup\": %f,\n\n"%(name, spd))
    line = f1.readline()
f.write("}\n")
