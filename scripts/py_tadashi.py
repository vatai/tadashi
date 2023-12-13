import isl
import pet
import os
print(os.environ["LD_LIBRARY_PATH"])

def get_may_dependence(scop):
    access = isl.union_access_info(scop.get_may_reads())
    access = access.set_may_source(scop.get_may_writes())
    access = access.set_must_source(scop.get_must_writes())
    access = access.set_schedule(scop.get_schedule())
    return access.compute_flow().get_may_dependence()


def lex_pos(deltas):
    deltas_max = deltas.as_set().lexmax().plain_multi_val_if_fixed()
    for i in range(deltas_max.size()):
        val = deltas_max.at(i)
        if val.is_neg():
            return False
        if val.is_pos():
            return True
    return False


def main(path):
    scop = pet.scop.extract_from_C_source(path, "f")
    dependence = get_may_dependence(scop)
    schedule = isl.union_map("[N] -> { S_0[i, j] -> [j, i] }")
    print(f"{schedule=}")
    deltas = dependence.apply_domain(schedule).apply_range(schedule).deltas()
    print(f"{lex_pos(deltas)=}")


if __name__ == "__main__":
    path = "/barvinok/polyhedral-tutor/examples/matmul.c"
    main(path)
