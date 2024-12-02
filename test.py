import ast
import tokenize 
import io


print("-------------------------------------------")
def _get_for_loop_tokens(condition):
        split = 1
        while True:
            try:
                split_parts = condition.split(':', split)
                if split == 1:
                    condition_split = split_parts[0]
                else:
                    condition_split = ":".join(split_parts[:split])
                tokens = tokenize.tokenize(io.BytesIO(condition_split.encode('utf-8')).readline)
                tokens = [token.string.strip() for token in tokens if token.string.strip() and token.string.strip() not in ('if', 'while', 'for', 'utf-8')]
                return tokens
            except tokenize.TokenError:
                if ":" in condition[split + 1:]:
                    split += 1
                else:
                    return []

code = "if false: kk=2\nelif(true): k = 2;\ni = 8"
code2 = "for i in range(2): print(h);"
tree = ast.parse(code)

for eachNode in ast.walk(tree):
    if(type(eachNode) is ast.If or type(eachNode) is ast.While):
        con = ast.get_source_segment(code, eachNode.test)
        tokens = _get_for_loop_tokens(con)
        print(tokens)
    elif(type(eachNode) is ast.For): 
        con = ast.get_source_segment(code, eachNode)
        tokens = _get_for_loop_tokens(con)
        print(tokens)






# %%
from NodeTypeDict import NodeTypeDict
import ast
from collections import deque

def n_gram2(tree):
    n_gram_dict = {}
    curr_node = None
    prev_node = None

    for eachNode in ast.walk(tree):
        curr_node = type(eachNode).__name__

        if(curr_node in NodeTypeDict):
            if(prev_node != None):
                n_gram_name = NodeTypeDict[prev_node] + "_" + NodeTypeDict[curr_node]

                if(n_gram_name not in n_gram_dict):
                    n_gram_dict[n_gram_name] = 1
                else : n_gram_dict[n_gram_name] += 1

            prev_node = curr_node
        else: prev_node = None

    n_gram_freq = { "nG_" + n_gram_type: round(ngrams / len(n_gram_dict), 2) for n_gram_type, ngrams in n_gram_dict.items() }

    if n_gram_dict:
        return n_gram_freq
    else: return {}


def n_gram(tree):
    n_gram_dict = {}
    curr_node = "disregard"
    prev_node = "disregard"
    node_queue = deque([ast.parse(tree)])

    while node_queue:
        node = node_queue.popleft()

        if(node == None): 
            continue
        curr_node = type(node).__name__

        if(curr_node in NodeTypeDict):
            if(prev_node != "disregard"):
                n_gram_name = NodeTypeDict[prev_node] + "_" + NodeTypeDict[curr_node]

                if(n_gram_name not in n_gram_dict):
                    n_gram_dict[n_gram_name] = 1
                else : n_gram_dict[n_gram_name] += 1
            
            prev_node = curr_node
        else: prev_node = "disregard"

        for eachChild in ast.iter_child_nodes(node):
            if(list(ast.iter_child_nodes(eachChild))): 
                node_queue.append(eachChild) 
            else: node_queue.append(None)
    
    n_gram_freq = { "nG_" + n_gram_type: round(ngrams / len(n_gram_dict), 2) for n_gram_type, ngrams in n_gram_dict.items() }

    if n_gram_dict:
        return n_gram_freq
    else: return {}

code = """ 
def func():
    i = 2 + 3
    for i in range(2+2):
        x += 2
y= myfunc()
"""
tree = ast.parse(code)
erg2 = n_gram2(tree)
erg = n_gram(tree)
print(erg)
print(erg2)

qu = deque([ast.parse(tree)])
while qu:
    eachNode = qu.popleft()
    print(type(eachNode).__name__)
    for eachChild in ast.iter_child_nodes(eachNode):
        if(list(ast.iter_child_nodes(eachChild))): 
            qu.append(eachChild) 

#for eachNode in ast.walk(tree):
 #   print(type(eachNode).__name__)







# %%
import ast
from collections import deque
from NodeTypeDict import NodeTypeDict

def n_gram(tree):
    n_gram_dict = {}
    
    def name_finder(curr_node):
        possible_names = []

        for eachChild in ast.iter_child_nodes(curr_node):
            q = deque([eachChild])

            while q:
                node = q.popleft()
                node_name = type(node).__name__
                if(node_name in NodeTypeDict):
                    possible_names.append(NodeTypeDict[node_name])
                else:
                    for eachChild2 in ast.iter_child_nodes(node):
                        q.append(eachChild2)

        return possible_names

    for eachNode in ast.walk(tree):
        if(type(eachNode).__name__ not in NodeTypeDict): continue
        possible_names = name_finder(eachNode)

        for eachName in possible_names:
            n_gram_name = NodeTypeDict[type(eachNode).__name__] + "_" + eachName

            if(n_gram_name not in n_gram_dict): 
                n_gram_dict[n_gram_name] = 1
            else: n_gram_dict[n_gram_name] += 1

    n_gram_freq = { "nG_" + n_gram_type: round(ngrams / len(n_gram_dict), 2) for n_gram_type, ngrams in n_gram_dict.items() }

    if n_gram_dict:
        return n_gram_freq
    else: return {}

code = """ 
a = 2
c = 3
"""
tree = ast.parse(code)

print(n_gram(tree))

qu = deque([tree])
while qu:
    eachNode = qu.popleft()
    print(type(eachNode).__name__)
    for eachChild in ast.iter_child_nodes(eachNode):
        #if(list(ast.iter_child_nodes(eachChild))): 
            qu.append(eachChild) 


# %%
import ast
import tokenize
from io import StringIO

code = """x = 'hallo'
for i in range(10):
    print("2")
    if(x == "h"): print(x)"""

tree = ast.parse(code)
sloc = len(code.split("\n"))

def string_quotation1(tree):
    strings = []

    for eachNode in ast.walk(tree):
        if(type(eachNode) is ast.Constant and type(eachNode.value) is str): strings.append(eachNode.value)
    
    return strings

def string_quotation_types(code):
    single_quoted_strings = []
    double_quoted_strings = []

    tokens = tokenize.generate_tokens(StringIO(code).readline)
    
    for token in tokens:
        if token.type == tokenize.STRING:
            string_value = token.string
            if string_value.startswith("'") or string_value.startswith("'''"):
                single_quoted_strings.append(string_value)
            elif string_value.startswith('"') or string_value.startswith('"""'):
                double_quoted_strings.append(string_value)
    
    return single_quoted_strings, double_quoted_strings


#for eachNode in ast.walk(tree):
    #print(type(eachNode).__name__)


print(string_quotation1(tree))
print(string_quotation_types(code))

# %%
import numpy as np
dic = {"1": 1, "2": np.nan}

for eachitem in dic.values():
    if(eachitem is np.nan):
        print(eachitem)
# %%
