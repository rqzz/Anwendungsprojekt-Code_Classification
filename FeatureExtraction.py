import ast
import radon.complexity
import radon.metrics
from radon.raw import analyze
import numpy as np
import tokenize
import io
import os
from collections import deque, defaultdict
from NodeTypeDict import NodeTypeDict, keywords_dict
import keyword


class FeatureExtractor:

    def __init__(self, code):
        self.code = code
        self.sloc = len(self.code.split("\n"))
        self.astree = ast.parse(self.code)

        self.features= {}
        self.features.update({
            "avgFunctionLength": self.avg_func_length(),
            "avgLineLength": self.avg_line_length(),
            "avgIdentifierLength": self.avg_identifier_length(),
            "avgParameters": self.avg_params(),
            #"avgBranchingFactor": self.avg_branching_factor(),                 #worse
            "stddevLineLength": self.stddev_line_length(),
            #"stddevParams": self.stddev_params(),                              #doesnt change anything
            
            "CyclomaticComplexity": self.cyclomatic_complexity(),
            "MaintainabilityIndex": self.maintainability_index(),
            "maxDecisonTokens": self.max_decision_tokens(),
            "maxAstDepth": self.max_ast_depth(self.astree),
            "maxNestingDepth": self.max_nesting_depth(),
            #"SLOC": self.sloc,

            "emptylines": self.empty_lines(),
            "emptyLineRatio": self.empty_line_ratio(),
            "whitespaceRatio": self.white_space_ratio(),
            "emptyLineDensity": self.empty_line_density(),
            "whiteSpaceDensity": self.white_space_density(),

            "FunctionDensity": self.func_density(),
            "AssignmentDensity": self.assignment_density(),
            "keywordDensity": self.keyword_density(),
            #"ClassDensity": self.class_density(),                               #doesnt change anything
            #"FuncCallDensity": self.funccall_density(),                         #doesnt change anything
            #"UniqueKeywordDensity": self.unique_keyword_density(),               #doesnt change anything before then worse imporved to be no change again
            #"StatementDensity": self.statement_density(),                       #doesnt change anything
            #"AssignmentVariablesDensity": self.assignemnt_variables_density(),  #worse
            #"InputDensity": self.input_density(),                               #worse
            #"LiteralDensity": self.literal_density(),                           #worse
            
        #OWN FEATURES
            "LLOCSLOC": self.llocsloc(),
            "StringQuotation": self.string_quotation(),                          
            #"avgKeywordFrequency": self.avg_keyword_frequency(),                #worse
            #"LibraryUses": self.library_uses(),                                 #worse
            #"avgReassignemnts": self.avg_reassignments(),                       #worse
            #"FuncFuncCallRatio": self.func_funccall_ratio(),                    #doesnt change anything 
            #"AssignAugAssignRatio": self.assign_augassign_ratio(),              #doesnt change anything 
            #"stddevVariableNames": self.stddev_variable_names(),                #worse 
            #"avgVariableUsage": self.avg_variable_usage(),                      #worse
        })

        #self.features.update(self.keyword_frequencies())                         #worse 
        self.features.update(self.ntype_avg_depths())
        self.features.update(self.ntype_term_freq())
        #self.features.update(self.n_gram())
        

    def avg_line_length(self):
        lines = self.code.split("\n")
        lines_length = [len(eachLine) for eachLine in lines]
        return round(sum(lines_length) / len(lines))
    

    def num_func(self):
        num_func = 0
        for eachNode in ast.walk(self.astree):
            if(type(eachNode) == ast.FunctionDef):
                num_func += 1
        return num_func


    def func_density(self):
        return round(self.num_func() / self.sloc, 2)
    

    def avg_func_length(self):
        total_lengths = 0
        for eachNode in ast.walk(self.astree):
            if(type(eachNode) == ast.FunctionDef):    
                total_lengths += eachNode.end_lineno - eachNode.lineno

        if total_lengths:
            return round(total_lengths / self.num_func(), 2)
        else: return 0
    

    def avg_identifier_length(self):
        total_length = 0
        identifiers = 0
        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Name): 
                total_length += len(eachNode.id)
                identifiers += 1

        return round(total_length / identifiers ,2)        
    

    def maintainability_index(self):
        return radon.metrics.mi_visit(self.code, False)
    

    def stddev_line_length(self):
        lines = self.code.split("\n")
        lines_length = [len(eachLine) for eachLine in lines]
        return round(np.std(lines_length, ddof=1), 2)


    def llocsloc(self):
        return analyze(self.code).lloc / analyze(self.code).sloc 
    
   
    def avg_params(self):
        total_params = 0

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.FunctionDef):
                total_params += (len(eachNode.args.args) + len(eachNode.args.kwonlyargs) + len(eachNode.args.posonlyargs))
                total_params += 1 if eachNode.args.vararg else 0
                total_params += 1 if eachNode.args.kwarg else 0 
        
        if total_params:
            return round(total_params / self.num_func(), 2)
        else: return 0


    def avg_branching_factor(self): 
        total_parents = 0 
        total_children = 0

        for eachNode in ast.walk(self.astree):
            children = list(ast.iter_child_nodes(eachNode))
            if(children):
                total_parents += 1
                total_children += len(children)

        if total_children:
            return round(total_children / total_parents, 2)
        else: return 0
        

    def cyclomatic_complexity(self):
        return radon.metrics.ComplexityVisitor(self.code).total_complexity
    

    def keyword_frequencies(self):
        total_keyword_dict = {}
        tokens = tokenize.tokenize(io.BytesIO(self.code.encode('utf-8')).readline)
        total = 0

        for eachToken in tokens:
                total += 1
                keyword_type = keywords_dict[eachToken.string]
                if(keyword_type not in total_keyword_dict):
                    total_keyword_dict[keyword_type] = 1
                else:
                    total_keyword_dict[keyword_type] += 1

        kw_freq = { "kwd_" + kw_type: round(kw_totals / len(total_keyword_dict), 2) for kw_type, kw_totals in total_keyword_dict.items() }

        if total_keyword_dict:
            return kw_freq
        else: return {}


    def avg_keyword_frequency(self):
        frequencies = list(self.keyword_frequencies().values())

        if frequencies:
            return round(sum(frequencies) / len(frequencies), 2)
        else: return 0


    def keyword_density(self):
        total_keyword_dict = {}
        tokens = tokenize.tokenize(io.BytesIO(self.code.encode('utf-8')).readline)

        for eachToken in tokens:
            if(eachToken.string in keyword.kwlist):
                if(eachToken.string not in total_keyword_dict):
                    total_keyword_dict[eachToken.string] = 1
                else:
                    total_keyword_dict[eachToken.string] += 1

        return round(sum(total_keyword_dict.values()) / self.sloc, 2); 
        #if list(tokens):
            #return round(sum(total_keyword_dict.values()) / len(tokens), 2); 
        #else: return 0


    def unique_keyword_density(self): 
        unique_keywords = {}
        tokens = tokenize.tokenize(io.BytesIO(self.code.encode('utf-8')).readline)

        for eachToken in tokens:
            if(eachToken.string in keyword.kwlist):
                if(eachToken not in unique_keywords):
                    unique_keywords[eachToken.string] = 1
                else: unique_keywords[eachToken.string] += 1
        if unique_keywords: return round(len(unique_keywords) / sum(unique_keywords.values()), 2) #anz zeilen ändert hier wieder ergebnis??
        else: return 0


    def max_nesting_depth(self):
        max_nesting_depth = 0
        queue = deque([(self.astree, 0)])
        
        while queue:
            node, nesting_depth = queue.popleft()

            if(type(node) in (ast.If, ast.While, ast.For, ast.FunctionDef, ast.AsyncFunctionDef)):
                max_nesting_depth = max(max_nesting_depth, nesting_depth + 1)
                nesting_depth += 1
            
            for eachChild in ast.iter_child_nodes(node):
                queue.append((eachChild, nesting_depth))
        
        return max_nesting_depth


    def assignment_density(self):
        assignments = 0
        
        for eachNode in ast.walk(self.astree):
            if(eachNode is ast.Assign): assignments += 1

        return round(assignments / self.sloc, 2)
    
    
    def assign_augassign_ratio(self):
        augassignemnts = 0
        assignments = 0

        for eachNode in ast.walk(self.astree):
            if(eachNode is ast.Assign): assignments += 1
            if(eachNode is ast.AugAssign): augassignemnts += 1

        if(augassignemnts and assignments): 
            return round(np.log(augassignemnts / assignments), 2)
        else: return 0


    def class_density(self):
        classes = 0

        for eachNode in ast.walk(self.astree):
            if(eachNode is ast.ClassDef): classes += 1

        return round(classes / self.sloc, 2)
    

    def funccall_density(self):
        func_calls = 0

        for eachNode in ast.walk(self.astree):
            if(eachNode is ast.Call): func_calls += 1

        return round(func_calls / self.sloc, 2)


    def func_funccall_ratio(self):
        func_calls = 0

        for eachNode in ast.walk(self.astree):
            if(eachNode is ast.Call): func_calls += 1

        if func_calls:
            return round(func_calls / self.num_func(), 2)
        else: return 0


    def input_density(self):
        inputs = 0

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Call):
                if(hasattr(eachNode.func, "id") and eachNode.func.id == "input"): inputs += 1

        return round(inputs / self.sloc, 2)


    def literal_density(self):
        literals = 0

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) in (ast.Constant, ast.FormattedValue, ast.JoinedStr, ast.List, ast.Tuple, ast.Set, ast.Dict)):
                literals += 1

        return round(literals / self.sloc, 2)
    

    def statement_density(self):
        statements = 0

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.stmt): statements += 1

        return round(statements / self.sloc, 2)
               

    def assignemnt_variables_density(self):
        variables = []

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Assign):

                for eachTarget in eachNode.targets:
                    if(type(eachTarget) is ast.Tuple):
                        for eachEntry in eachTarget.elts: 
                            if(type(eachEntry) is ast.Name and eachEntry.id not in variables): variables.append(eachEntry.id)

                    elif(type(eachTarget) is ast.Name and eachTarget.id not in variables): variables.append(eachTarget.id)

        return round(len(variables) / self.sloc, 2)
    

    def stddev_params(self):
        params_in_func = []

        for eachNode in ast.walk(self.astree):
            params = 0
            if(type(eachNode) is ast.FunctionDef):
                params += (len(eachNode.args.args) + len(eachNode.args.kwonlyargs) + len(eachNode.args.posonlyargs))
                params += 1 if eachNode.args.vararg else 0 
                params += 1 if eachNode.args.kwarg else 0 
                params_in_func.append(params)

        if params_in_func:
            return round(np.std(params_in_func, ddof=0), 2)
        else: return 0

    
    def stddev_variable_names(self):
        names = set()

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Name): names.add(eachNode.id)
        
        name_lengths = [len(eachName) for eachName in names]

        if name_lengths:
            return round(np.std(name_lengths, ddof=1), 2)
        else: return 0

    
    def avg_variable_usage(self):
        usages = {}

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Name and type(eachNode.ctx) is ast.Load):
                if(eachNode.id not in usages): usages[eachNode.id] = 1
                else: usages[eachNode.id] += 1

        if usages:
            return round(sum(usages.values()) / len(usages) , 2)
        else: return 0


    def avg_reassignments(self):
        reassignments = 0

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Name and type(eachNode.ctx) is ast.Store):
                reassignments += 1
        #reassignments = {k: v for k,v in reassignments.items() if v != 0}

        if reassignments:
            return reassignments
        else: return 0


    def white_space_ratio(self):
        whitespaces = sum(1 for char in self.code if char.isspace())
        non_whitespace_chars = len(self.code) - whitespaces

        #for eachChar in self.code: 
            #if(eachChar.isspace()): whitespaces += 1

        return round((whitespaces / non_whitespace_chars), 2) if non_whitespace_chars > 0 else 0.0 
        #return round(whitespaces / (len(self.code) - whitespaces), 2)
  

    def empty_lines(self):
        emptylines = 0

        for eachLine in self.code.splitlines():
            if(eachLine.strip() == ""): emptylines += 1

        return emptylines 


    def empty_line_ratio(self):
        return round(self.empty_lines() / (self.sloc - self.empty_lines()), 2)
    

    def empty_line_density(self):
        return round(self.empty_lines() / self.sloc, 2)


    def white_space_density(self):
        return round(sum(1 for char in self.code if char.isspace()) / self.sloc, 2)
    

    def library_uses(self):
        uses = 0
        imports = []

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) in (ast.Import, ast.ImportFrom)):
                imports.extend([eachImport.name for eachImport in eachNode.names]) 

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.Attribute and type(eachNode.value) is ast.Name and eachNode.value.id in imports): uses += 1


        return round(uses / self.sloc, 2)


    def string_quotation(self):
        single_quoted_strings = []
        double_quoted_strings = []

        tokens = tokenize.generate_tokens(io.StringIO(self.code).readline)
        
        for token in tokens:
            if token.type == tokenize.STRING:
                string_value = token.string
                if string_value.startswith("'") or string_value.startswith("'''"):
                    single_quoted_strings.append(string_value)
                elif string_value.startswith('"') or string_value.startswith('"""'):
                    double_quoted_strings.append(string_value)
        
        if single_quoted_strings and double_quoted_strings:
            return round(len(double_quoted_strings) / len(single_quoted_strings), 2)    #komm danach ändert??
        elif not single_quoted_strings or not double_quoted_strings: return 100     


    def max_decision_tokens(self):
        decision_path_tokens = []

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

        for eachNode in ast.walk(self.astree):
            if(type(eachNode) is ast.If or type(eachNode) is ast.While):
                condition = ast.get_source_segment(self.code, eachNode.test)  
                tokens = _get_for_loop_tokens(condition)
                decision_path_tokens.append(tokens)

            elif(type(eachNode) is ast.For): 
                condition = ast.get_source_segment(self.code, eachNode)
                tokens = _get_for_loop_tokens(condition)
                decision_path_tokens.append(tokens)

        if decision_path_tokens: 
            return max(len(eachToken) for eachToken in decision_path_tokens)
        else: return 0


    def ntype_avg_depths(self):
        depth_dict = {}
        curr_depth = 1
        node_queue = deque([ast.parse(self.astree)])

        while node_queue:  
            curr_depth_length = len(node_queue)

            for _ in range(curr_depth_length):
                node = node_queue.popleft()
                node_name = type(node).__name__

                if(node_name in NodeTypeDict):
                    if(node_name not in depth_dict): depth_dict[NodeTypeDict[node_name]] = []
                    depth_dict[NodeTypeDict[node_name]].append(curr_depth)

                for eachChild in ast.iter_child_nodes(node):
                    if(list(ast.iter_child_nodes(eachChild))): node_queue.append(eachChild) 

            curr_depth += 1
        
        avg_depths = { "ntad_" + NodeType: round(sum(depth_list) / len(depth_list), 2) for NodeType, depth_list in depth_dict.items() }

        if depth_dict: 
            return avg_depths  
        else: return {}


    def ntype_term_freq(self):
        termfreq_dict = {}
        total_nodes = 0

        for eachNode in ast.walk(self.astree):
            if(list(ast.iter_child_nodes(eachNode))):
                node_name = type(eachNode).__name__

                if(node_name in NodeTypeDict):
                    total_nodes += 1
                    if(node_name not in termfreq_dict): 
                        termfreq_dict[NodeTypeDict[node_name]] = 1
                    else:  termfreq_dict[NodeTypeDict[node_name]] += 1

        if termfreq_dict: 
            return { "tf_" + NodeType: round(nodes, 2) for NodeType, nodes in termfreq_dict.items()}  #with /total_nodes worse
        else: return {}

    
    def max_ast_depth(self, node):
        if not list(ast.iter_child_nodes(node)):  
            return 0
        else:
            return 1 + max(self.max_ast_depth(eachChild) for eachChild in ast.iter_child_nodes(node))


# """     def n_gramfalsch(self):
#         n_gram_dict = {}
#         curr_node = None
#         prev_node = None

#         for eachNode in ast.walk(self.astree):
#             curr_node = type(eachNode).__name__

#             if(curr_node in NodeTypeDict):
#                 if(prev_node != None):
#                     n_gram_name = NodeTypeDict[prev_node] + "_" + NodeTypeDict[curr_node]

#                     if(n_gram_name not in n_gram_dict):
#                         n_gram_dict[n_gram_name] = 1
#                     else : n_gram_dict[n_gram_name] += 1

#                 prev_node = curr_node
#             else: prev_node = None

#         n_gram_freq = { "nG_" + n_gram_type: round(ngrams / len(n_gram_dict), 2) for n_gram_type, ngrams in n_gram_dict.items() }

#         if n_gram_dict:
#             return n_gram_freq
#         else: return {}


#     def n_gram2(self):
#         n_gram_dict = {}
#         curr_node = "disregard"
#         prev_node = "disregard"
#         node_queue = deque([ast.parse(self.astree)])

#         while node_queue:
#             node = node_queue.popleft()

#             if(node == None): 
#                 continue
#             curr_node = type(node).__name__

#             if(curr_node in NodeTypeDict):
#                 if(prev_node != "disregard"):
#                     n_gram_name = NodeTypeDict[prev_node] + "_" + NodeTypeDict[curr_node]

#                     if(n_gram_name not in n_gram_dict):
#                         n_gram_dict[n_gram_name] = 1
#                     else : n_gram_dict[n_gram_name] += 1
                
#                 prev_node = curr_node
#             else: prev_node = "disregard"

#             for eachChild in ast.iter_child_nodes(node):
#                 if(list(ast.iter_child_nodes(eachChild))): 
#                     node_queue.append(eachChild) 
#                 else: node_queue.append(None)
        
#         n_gram_freq = { "nG_" + n_gram_type: round(-np.log(ngrams / len(n_gram_dict)), 2) for n_gram_type, ngrams in n_gram_dict.items() } 

#         if n_gram_dict:
#             return n_gram_freq
#         else: return {} """


    def n_gram(self):
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

        for eachNode in ast.walk(self.astree):
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
        
#endofclass     


def fill_feature_vectors(total_features):
    unique_features = set()
    for eachFeaturedict in total_features:
        for eachFeature in eachFeaturedict.keys():
            if(eachFeature not in unique_features): unique_features.add(eachFeature)
    
    for eachFeaturedict in total_features:
        for eachFeature in unique_features:
            if(eachFeature not in eachFeaturedict): eachFeaturedict[eachFeature] = 0

        filename = eachFeaturedict.pop("filename")
        eachFeaturedict["filename"] = filename
        if(filename.startswith("human")): eachFeaturedict["label"] = 0
        else: eachFeaturedict["label"] = 1


def feature_extraction():
    total_features = []
    project_dir = os.path.dirname(os.path.abspath(__file__))
    training_dir = os.path.join(project_dir, "TrainingData")

    for eachFile in os.listdir(training_dir):
        with open(os.path.join(training_dir, eachFile), "r") as f:
            code = f.read()

        feature_extraction = FeatureExtractor(code)
        features = feature_extraction.features
        #features = feature_extraction.n_gram()
        features.update({'filename': eachFile})
        total_features.append(features)

    fill_feature_vectors(total_features)
    return total_features

        
    
