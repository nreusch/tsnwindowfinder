import re
import sys

first_name = ''
map_start_end_node = {}
lines = []
f = open(sys.argv[1], "r")
for line in f:
    newline = line
    if not line.startswith('#'):
        m = re.findall(r'([a-zA-Z0-9_]+)\s?,\s?([a-zA-Z0-9_]+)', line)
        
        #Create Map
        if m is not None:
            for tpl in m:
                n1_name = tpl[0]
                n2_name = tpl[1]
                map_start_end_node[n1_name] = n2_name
                
                if n1_name.startswith('ES'):
                    first_name = n1_name
        
        #Create String
        newline = line[:line.find(':')+1]
        next_node = map_start_end_node[first_name]
        while not next_node.startswith('ES'):            
            newline += ' ' + first_name + ',' + next_node + ' ;'
            first_name = next_node
            next_node = map_start_end_node[first_name]
            
        newline += ' ' + first_name + ',' + next_node + ' ;'
        
    print(newline)
    lines.append(newline + '\n')
    
f.close()

f = open(sys.argv[1], "w")
f.writelines(lines)
f.close()