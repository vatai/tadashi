import re

import yaml


class OptionsPool:
    pass


def node_convert_tile(node, tile_size):
    pattern = r"\((-?\w+)\)"
    loop_alphabet = re.findall(pattern, node["schedule"])[0]
    temp = node["schedule"]
    outer_loop_tile = "({} - ({}) mod {})".format(
        loop_alphabet, loop_alphabet, str(tile_size)
    )
    inner_loop_tile = "(({}) mod {})".format(loop_alphabet, str(tile_size))
    node["schedule"] = re.sub(pattern, outer_loop_tile, temp)
    if "child" in node.keys():
        t = {"schedule": "", "child": {}}
        t["child"] = node["child"]
    else:
        t = {"schedule": ""}

    t["schedule"] = re.sub(pattern, inner_loop_tile, temp)
    node["child"] = t
    print("loop,tile finished!")


def node_mark_parallel(node):
    tmp = node["schedule"]
    node["child"] = {"mark": "parallel", "child": {"schedule": tmp}}


def node_convert_reverse(node):
    pattern = r"\[\((\w+)\)\]"
    replacement = r"[(-\1)]"
    node["schedule"] = re.sub(pattern, replacement, node["schedule"])
    print("loop,reverse finished!")


def node_convert_interchange(node):
    return node


class process_schedule:
    def __init__(self, yaml_schedule) -> None:
        self.yaml_schedule = yaml_schedule
        self.for_loop_index = dict()

    def mark_parallel(self, loop_idx_list):
        self.traverse(node_mark_parallel, loop_idx_list)

    def traverse(self, func, loop_index_list=[], *args, **kwargs):
        node = self.yaml_schedule["child"]
        for i in range(len(loop_index_list)):
            loop_index = loop_index_list[i]
            while True:
                if "schedule" in node.keys():
                    if i == len(loop_index_list) - 1:
                        return func(node, *args, **kwargs)
                    else:
                        node = node["child"]
                    break
                elif "child" in node.keys():
                    node = node["child"]
                elif "sequence" in node.keys():
                    node = node["sequence"]
                    count = -1
                    len_filter = len(node)
                    for t in range(len_filter):
                        if "child" in node[t].keys():
                            count += 1
                        if count == loop_index:
                            node = node[t]
                            break

                elif "filter" in node.keys():
                    node = node["filter"]
                elif isinstance(node, list):
                    # len_filter
                    # while ~ re.match(r'\{ S_\d+\[\] \}', )
                    node = node[loop_index]
                else:
                    print("key missed")
                    return

    def tile(self, tile_size, loop_index_list=[]):
        self.traverse(node_convert_tile, loop_index_list, tile_size)
        pass

    def unroll(self, loop_index, unroll_size):
        pass

    def interchange(self, loop_index_list_1=[], loop_index_list_2=[]):
        node1 = self.traverse(node_convert_interchange, loop_index_list_1)
        node2 = self.traverse(node_convert_interchange, loop_index_list_2)
        pattern = r'\[\((.*?)\)\]'
        loop_alphabet1 = re.findall(pattern, node1['schedule'])[0]
        loop_alphabet2 = re.findall(pattern, node2['schedule'])[0]
        node1['schedule'] = node1['schedule'].replace(loop_alphabet1, loop_alphabet2)
        node2['schedule'] = node2['schedule'].replace(loop_alphabet2, loop_alphabet1)
        
    def fuse(self, loop_index1=[], loop_index2=[]):
        pass

    def reverse(self, loop_index_list=list()):
        self.traverse(node_convert_reverse, loop_index_list)

    def fission(self, loop_index):
        pass

    def skew(self, loop_index, skew_parameter):
        pass


if __name__ == "__main__":
    with open(
        "/barvinok/polyhedral-tutor/src/from-isl-development-ml/demo.yaml", "r"
    ) as file:
        data = yaml.safe_load(file)
        schedule = process_schedule(data)

    # schedule.interchange([0], [0, 0])
    schedule.tile(2, [0])
    schedule.interchange([0], [0, 0])
    # schedule.tile(2, [0])
    with open(
        "/barvinok/polyhedral-tutor/src/from-isl-development-ml/demo3.yaml", "w"
    ) as file:
        data = yaml.dump(
            data, file, default_flow_style=False, sort_keys=False, default_style='"'
        )

    print("finished")
