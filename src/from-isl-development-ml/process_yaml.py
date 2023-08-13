import yaml
import re
class OptionsPool():
    pass
def node_convert_tile(node, tile_size):
    pattern = r'\((\w+)\)'
    loop_alphabet = re.findall(pattern, node['schedule'])[0]
    temp = node['schedule']
    outer_loop_tile = '({} - ({}) mod {})'.format(loop_alphabet, loop_alphabet, str(tile_size))
    inner_loop_tile = '(({}) mod {})'.format(loop_alphabet, str(tile_size))
    node['schedule'] = re.sub(pattern, outer_loop_tile, temp)
    if 'child' in node.keys():
        t = {'schedule':'', 'child':{}}
        t['child'] =  node['child']
    else:
        t = {'schedule':''}
   
    t['schedule'] = re.sub(pattern, inner_loop_tile, temp)
    node['child'] = t
    print("loop,tile finished!")

def node_convert_reverse(node):
    pattern = r'\[\((\w+)\)\]'
    replacement = r'[(-\1)]'
    node['schedule'] = re.sub(pattern, replacement, node['schedule'])
    print("loop,tile finished!")
    
class process_schedule():
    def __init__(self, yaml_schedule) -> None:
        self.yaml_schedule = yaml_schedule
        self.for_loop_index = dict()
    
    def traverse(self, func, loop_index_list=[], *args, **kwargs):
        node = self.yaml_schedule["child"]
        for i in range(len(loop_index_list)):
            loop_index = loop_index_list[i]
            while True:
                if isinstance(node, list):
                    node = node[loop_index]
                elif "schedule" in node.keys():
                    if i==len(loop_index_list)-1:
                        func(node, *args, **kwargs)
                    else:
                        node = node['child']
                    break   
                elif "child" in node.keys(): 
                    node = node["child"]  
                elif "sequence" in node.keys(): 
                    node = node["sequence"]
                elif "filter" in node.keys(): 
                    node = node["filter"]
                else: 
                    print("key missed")
                    return
        
        
    def tile(self, tile_size, loop_index_list=[]):
        self.traverse(node_convert_tile, loop_index_list, tile_size)
        pass
    
    def unroll(self, loop_index, unroll_size):
        pass
    
    def interchange(self, loop_index_1, loop_index_2):
        pass
    
    def fuse(self, loop_index1=[], loop_index2=[]):
        pass
    
    def reverse(self, loop_index_list=list()):
        node = self.yaml_schedule["child"]
        for i in range(len(loop_index_list)):
            loop_index = loop_index_list[i]
            while True:
                if isinstance(node, list):
                    node = node[loop_index]
                elif "schedule" in node.keys():
                    if i==len(loop_index_list)-1:
                        pattern = r'\[\((\w+)\)\]'
                        replacement = r'[(-\1)]'
                        node['schedule'] = re.sub(pattern, replacement, node['schedule'])
                    else:
                        node = node['child']
                    break   
                elif "child" in node.keys(): 
                    node = node["child"]  
                elif "sequence" in node.keys(): 
                    node = node["sequence"]
                elif "filter" in node.keys(): 
                    node = node["filter"]
                else: 
                    print("key missed")
                    return
        print("loop{},reverse finished!".format(loop_index_list))
            
    def fission(self, loop_index):
        pass
    
    def skew(self, loop_index, skew_parameter):
        pass
    
    
    

    
with open('/barvinok/polyhedral-tutor/src/from-isl-development-ml/demo.yaml', 'r') as file:
    data = yaml.safe_load(file)
    schedule = process_schedule(data)
schedule.reverse([0,0])
schedule.tile(2, [0, 0])
schedule.tile(2, [0])
with open('/barvinok/polyhedral-tutor/src/from-isl-development-ml/demo3.yaml', 'w') as file:
    data = yaml.dump(data, file, default_flow_style=False, sort_keys=False)

print(data)