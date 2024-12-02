import io
import os
import ast
import csv
import math
import keyword
import tokenize
import statistics
from io import BytesIO
from radon.raw import analyze
from collections import deque
from collections import Counter
from radon.metrics import h_visit, ComplexityVisitor, mi_visit
from NodeTypeDict import NodeTypeDict

#logger
class Logger:
    log_file_path = "../../logs/log.log" # or any other path

    if not os.path.exists("../../logs"):
        os.makedirs("../../logs")

    @classmethod
    def error_log(cls, s: str):
        with open(cls.log_file_path, "a") as error_f:
            error_f.write(f"Error: {s}\n")

    @classmethod
    def info_log(cls, s: str):
        with open(cls.log_file_path, "a") as info_f:
            info_f.write(f"Info: {s}\n")

nan = math.nan
default_values = [nan, -1, -1.0]

class CodeMetricsExtractor:
    def __init__(self, code):
        # library-independent
        self.code: str = code
        self.radon_raw_metrics = self._get_radon_metrics()
        self.line_length = self._get_line_length()
        self.whitespaces = self._get_num_whitespaces()
        self.empty_lines = self._get_empty_lines()
        self.code_length = len(code)
        

        # ast-dependent
        self.tree = self._get_ast()
        self.num_functions = self._get_num_functions()
        self.functions_params = self._get_functions_params()

        # tokenize-dependent
        self.tokens = self._get_tokens()
        self.keywords = self._get_keywords()

        
        self.metrics = {}
        self.metrics.update({
            'avgLineLength': self._get_avg_line_length(),
            'avgFunctionLength': self._get_avg_function_length(), 
            'avgIdentifierLength': self._get_avg_identifier_length(),    
            'avgParams': self._get_avg_func_params(),
            'branchingFactor': self._get_branching_factor(),
            'stdDevLineLength': self._get_line_length_stdev(), 
            'stdDevNumParams': self._get_func_params_stdev(),

            'cyclomaticComplexity': self._get_radon_cyclomatic_complexity(),
            'maintainabilityIndex': self._get_radon_maintainability_index(),
            'maxDecisionTokens': self._get_max_decision_tokens(),
            'maxDepthASTNode': self._get_max_ast_node_depth(), 
            'nestingDepth': self._get_max_nesting_depth(),
            'sloc': self.radon_raw_metrics.sloc, 
            #"LLOCSLOC": self.llocsloc(),
            'numStatementsDensity': self._get_num_statements_density(),
            'numVariablesDensity': self._get_num_variables_density(), 
            'numFunctionsDensity': self._get_functions_density(), 
            'numInputStmtsDensity': self._get_input_statements_density(), 
            'numAssignmentStmtDensity': self._get_assignment_statements_density(), 
            'numFunctionCallsDensity': self._get_function_calls_density(), 
            'numClassesDensity': self._get_num_classes_density(), 
            'numLiteralsDensity': self._get_literals_density(),
            'numKeywordsDensity': self._get_num_keywords_density(),

            "emptylines": self._get_empty_lines(),
            "whitespaces": self._get_num_whitespaces(),
        })

        #self.metrics.update(self.ntype_avg_depths())
        self.metrics.update(self._get_node_type_avg_depth()) 
        #self.metrics.update(self.ntype_term_freq())
        self.metrics.update(self._get_node_type_term_frequency())   
        #self.metrics.update(self._get_keywords_density())


        if self.code_length == 0 or not self.code.strip():
            Logger.error_log("File is empty or contains only whitespaces")
        elif self.tree is None:
            Logger.error_log("Failed to parse code to ast.")
        elif self.tokens is None:
            Logger.error_log("Failed to tokenize code.")
        elif self.radon_raw_metrics is None:
            Logger.error_log("Failed to calculate Radon metrics.")
        else:
            #self._get_radon_dependent_metrics()
            #self._get_library_independent_metrics()
            #self._get_ast_dependent_metrics()
            #self._get_tokenize_dependent_metrics()  
            pass
            
    def _get_radon_dependent_metrics(self):
        """
        Returns metrics that require importing radon library
        """
        if self.radon_raw_metrics is not None:
            self.metrics.update({ 
 
                'cyclomaticComplexity': self._get_radon_cyclomatic_complexity(), 
                'maintainabilityIndex': self._get_radon_maintainability_index(),
                'sloc': self.radon_raw_metrics.sloc, 
                #'numVariablesDensity': self._get_num_variables_density(), 
                'numFunctionsDensity': self._get_functions_density(), 
                #'numInputStmtsDensity': self._get_input_statements_density(), 
                'numAssignmentStmtDensity': self._get_assignment_statements_density(), 
                #'numFunctionCallsDensity': self._get_function_calls_density(), 
                'numStatementsDensity': self._get_num_statements_density(), 
                'numClassesDensity': self._get_num_classes_density(),                 
        })

    def _get_ast_dependent_metrics(self):
        """
        Returns metrics that require importing ast module
        """
        if self.tree is not None:
            self.metrics.update(self._get_node_type_term_frequency()) 
            #self.metrics.update(self._get_node_type_avg_depth()) 
            self.metrics.update(self.ntype_avg_depths()) 

            self.metrics.update({
                'maxDepthASTNode': self._get_max_ast_node_depth(), 
                'branchingFactor': self._get_branching_factor(),
                'maxDecisionTokens': self._get_max_decision_tokens(), 
                #'numLiteralsDensity': self._get_literals_density(),
                'nestingDepth': self._get_max_nesting_depth(),
                'avgParams': self._get_avg_func_params(), 
                #'stdDevNumParams': self._get_func_params_stdev(), 
                'avgFunctionLength': self._get_avg_function_length(), 
                'avgIdentifierLength': self._get_avg_identifier_length(), 
            })

    def _get_tokenize_dependent_metrics(self):
        """
        Returns metrics that require importing tokenize module
        """
        if self.tokens is not None:
            self.metrics.update({'numKeywordsDensity': self._get_num_keywords_density()})
            self.metrics.update(self._get_keywords_density())

    def _get_library_independent_metrics(self):
        """
        Returns metrics that do not require importing any library/module
        """
        self.metrics.update({ 
            'stdDevLineLength': self._get_line_length_stdev(), 
            'avgLineLength': self._get_avg_line_length(),
    })
        

##########################################################################
    def llocsloc(self):
        return analyze(self.code).lloc / analyze(self.code).sloc 

    def _get_ast(self):
        """Returns the ast of the code"""
        try:
            return ast.parse(self.code)
        except SyntaxError:
            Logger.error_log("Failed to parse code to ast. Returning None for ast")
            return None
        
    def _get_tokens(self):
        """Returns the tokens of the code using the tokenize module"""
        try:
            return tokenize.tokenize(BytesIO(self.code.encode('utf-8')).readline)
        except tokenize.TokenError:
            Logger.error_log("Failed to tokenize code. Returning None for tokens")
            return None
    
    def _get_keywords(self):
        """ Returns the occurrences of each keyword in the code """
        if self.tokens is None:
            Logger.error_log("Failed to tokenize code. Returning empty dictionary for keywords")
            return None
        keywords = {}
        tokens = self._get_tokens()
        comment_state = False
        try:
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    comment_state = True
                elif token.type == tokenize.NL or token.type == tokenize.NEWLINE:
                    comment_state = False
                elif token.string in keyword.kwlist and not comment_state:
                    if token.string not in keywords:
                        keywords[token.string] = 1
                    else:
                        keywords[token.string] += 1
        except:
            Logger.error_log("Failed to tokenize code. Returning empty dictionary for keywords")
            return {}
        return keywords
    
    def _get_radon_metrics(self):
        """ Returns the raw metrics calculated by Radon """
        try:
            return analyze(self.code)
        except:
            Logger.error_log("Failed to calculate Radon metrics. Returning None")
            return None

    def _get_line_length(self):
        """ Returns the length of characters in each line of the code """
        lines = self.code.split('\n')
        # lines = code.split('\n')
        lines_length = [len(line) for line in lines]
        return lines_length
    
    def _get_num_whitespaces(self):
        """ Returns the total occurrences of spaces (spaces, newlines) in the code """
        return round(sum(1 for char in self.code if char.isspace()) / self.radon_raw_metrics.sloc, 2)
    
    def _get_empty_lines(self):
        """ Returns the total occurrences of empty lines in the code """
        return round(sum(1 for line in self.code.splitlines() if line.strip() == "") / self.radon_raw_metrics.sloc)
    
    def _get_avg_line_length(self):
        """ Returns the average length of characters in each line of code """
        if len(self.line_length) == 0:
            Logger.error_log(f"No code lines. Returning default value: {default_values[0]} for avg_line_length")
            return default_values[0]
        else:
            return round(sum(self.line_length) / len(self.line_length), 2)
    
    def _get_line_length_stdev(self):
        """ Returns the standard deviation of the length of characters in each line of the code"""
        return round(statistics.stdev(self.line_length), 2) if len(self.line_length) > 1 else 0
    
    def _get_max_decision_tokens(self):
        """ Returns the maximum number of tokens in a decision path """
        decision_path_tokens = []
        max_decision_tokens = 0

        try:
            for node in ast.walk(self.tree):
                if isinstance(node, (ast.If, ast.For, ast.While)):
                    if isinstance(node, ast.If) or isinstance(node, ast.While):
                        condition = ast.get_source_segment(self.code, node.test) 
                    elif isinstance(node, ast.For):
                        condition = ast.get_source_segment(self.code, node)
                    tokens = self._get_for_loop_tokens(condition)
                    decision_path_tokens.append(tokens)
            if decision_path_tokens:
                max_decision_tokens = max(len(tokens) for tokens in decision_path_tokens)
            return max_decision_tokens
        except Exception as e:
            Logger.error_log(f"Failed to get max_decision_tokens: {e}. Returning default value: {default_values[0]} for max_decision_tokens")
            return default_values[0]
        
    def _get_for_loop_tokens(self, condition):
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
    
    def _get_literals_density(self):
        """
        Calculates the logarithm of the total occurrences of literals 
        divided by the length of the code in terms of characters.

        Returns:
            float: The logarithm of the total occurrences of literals divided by the length of the code
        """
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for literals_density")
            return default_values[0]
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for literals_density")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for literals_density")
            return default_values[0]
        literals_sum = sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.Constant))
        sum_div_by_length = literals_sum / self.radon_raw_metrics.sloc
        return round(sum_div_by_length, 2)
    
    def _get_num_functions(self):
        """ Returns the total number of functions in the code """
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for num_functions")
            return default_values[0]
        return sum(isinstance(node, ast.FunctionDef) for node in ast.walk(self.tree))
    
    def _get_functions_params(self):
        """ Returns the parameters of each function in the code """
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for functions_params")
            return default_values[0]
        arguments_per_function = []
        for node in ast.walk(self.tree): 
            if isinstance(node, ast.FunctionDef):
                arguments_per_function.append(len(node.args.args)) 
        return arguments_per_function
    
    def _get_max_nesting_depth(self):
        """ Returns the maximum nesting depth of loops, conditional statements, and functions in the code"""
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for max_nesting_depth")
            return default_values[0]
        max_nesting_depth = 0
        queue = deque([(self.tree, 0)])
        while queue:
            node, depth = queue.popleft()            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.FunctionDef)):
                max_nesting_depth = max(max_nesting_depth, depth)            
            for child_node in ast.iter_child_nodes(node):
                queue.append((child_node, depth + 1))
        return max_nesting_depth
    
    def _get_max_nesting_function(self):
        """Returns the maximum nesting depth of functions in the code"""
        max_nesting_function = 0
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for max_nesting_function")
            return default_values[0]
        queue = deque([(self.tree, 0)])
        while queue:
            node, depth = queue.popleft()
            if isinstance(node, ast.FunctionDef):
                max_nesting_function = max(max_nesting_function, depth)
            for child_node in ast.iter_child_nodes(node):
                queue.append((child_node, depth + 1))
        return max_nesting_function
    
    def _get_branching_factor(self):
        """
        Returns the average branching factor of the AST. 
        The branching factor is the number of children of each parent node.
        The average branching factor is the total number of branches divided by the total number of parent nodes.
        """
        #use a queue for BFS
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for branching_factor")
            return default_values[0]
        queue = deque([self.tree])
        branches = []

        while queue:
            current_node = queue.popleft()
            current_node_branches = sum(1 for _ in ast.iter_child_nodes(current_node))
            if current_node_branches > 0:
                branches.append(current_node_branches)
            #add children to the queue for further processing
            queue.extend(ast.iter_child_nodes(current_node))

        total_branches = sum(branches)
        total_parent_nodes = len(branches)
        average_branching_factor = round((total_branches / total_parent_nodes), 2) if total_parent_nodes != 0 else 0
        return average_branching_factor
    
    def _get_avg_func_params(self):
        """Returns the average number of parameters of each function in the code"""
        if self.functions_params == default_values[0]:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for avg_func_params")
            return default_values[0]
        return round(sum(self.functions_params) / len(self.functions_params), 2) if len(self.functions_params) > 0 else 0.0
    
    def _get_func_params_stdev(self):
        """ Returns the standard deviation of the parameters of each function in the code"""
        if self.functions_params == default_values[0]:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for func_params_stdev")
            return default_values[0]
        return round(statistics.stdev(self.functions_params), 2) if len(self.functions_params) > 1 else 0
    
    def _get_max_ast_node_depth(self, node=None, max_depth=0):
        """Returns the maximum depth (distance from root to leaf nodes) of the AST"""
        max_depth = 0
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for max_ast_node_depth")
            return default_values[0]
        queue = deque([(self.tree, 0)])
        while queue:
            current_node, depth = queue.popleft()
            max_depth = max(max_depth, depth)
            for child_node in ast.iter_child_nodes(current_node):
                queue.append((child_node, depth + 1))
        return max_depth
    
    def _get_input_statements_density(self):
        """ Returns the total number of input statements divided by source code lines """
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for num_input_statements")
            return default_values[0]
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_input_statements")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_input_statements")
            return default_values[0]
        num_input_statements = sum(isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'input' for node in ast.walk(self.tree))
        return round((num_input_statements / self.radon_raw_metrics.sloc), 2)
    
    def _get_assignment_statements_density(self):
        """ Returns the total number of assignment statements divided by source code lines """
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_assignment_statements")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_assignment_statements")
            return default_values[0]
        assignment_statements = sum(isinstance(node, ast.Assign) for node in ast.walk(self.tree))
        return round((assignment_statements / self.radon_raw_metrics.sloc), 2)
    
    def _get_function_calls_density(self):
        """ Returns the total number of function calls divided by source code lines """
        function_calls = sum(isinstance(node, ast.Call) for node in ast.walk(self.tree))
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_function_calls")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_function_calls")
            return default_values[0]
        return round((function_calls / self.radon_raw_metrics.sloc), 2)
    
    def _get_num_statements_density(self):
        """ Returns the total number of statements divided by source code lines """
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_statements")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_statements")
            return default_values[0]
        num_statements = sum(isinstance(node, ast.stmt) for node in ast.walk(self.tree))
        return round((num_statements / self.radon_raw_metrics.sloc), 2)
    
    def _get_avg_function_length(self):
        """ Returns the average length of functions in the code """
        function_lengths = []
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for avg_function_length")
            return default_values[0]
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                function_length = node.end_lineno - node.lineno
                function_lengths.append(function_length)
        return round(sum(function_lengths) / len(function_lengths), 2) if len(function_lengths) > 0 else 0.0
    
    def _get_avg_identifier_length(self):
        """ Returns the average length of identifiers in the code """
        identifiers = set()
        lengths = []
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for avg_identifier_length")
            return default_values[0]
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                identifiers.add(node.id)
        lengths = [len(identifier) for identifier in identifiers]
        return round(sum(lengths) / len(lengths), 2) if len(lengths) > 0 else 0.0
    
    def _get_num_classes_density(self):
        """ Returns the total number of classes divided by source code lines """
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_classes_density")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_classes_density")
            return default_values[0]
        num_classes = sum(isinstance(node, ast.ClassDef) for node in ast.walk(self.tree))
        return round(num_classes / self.radon_raw_metrics.sloc, 2)
    
    def _get_node_type_term_frequency(self):
        """
        Returns the term frequency (frequency of node type with respect to the total number of nodes)
        of each node type in the AST excluding leaves
        """
        term_frequency = {}
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning empty dictionary for node_type_term_frequency")
            return term_frequency
        
        node_types = [node.__class__.__name__ for node in ast.walk(self.tree) if list(ast.iter_child_nodes(node))]
        frequency = Counter(node_types)
        term_frequency = {'nttf_' + k : v for k,v in frequency.items()}
        return term_frequency
    
    def _get_node_type_avg_depth(self):
        """Returns the average depth of each node type excluding leaves in the AST"""
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning empty dictionary for node_type_avg_depth")
            return {}

        node_queue = deque([(self.tree, 0)])
        depth_dict = {}

        while node_queue:
            current_node, depth = node_queue.popleft()
            node_type = type(current_node).__name__
            if node_type not in depth_dict:
                depth_dict[node_type] = []
            depth_dict[node_type].append(depth) 
            # add child nodes to the queue for further processing
            for child_node in ast.iter_child_nodes(current_node):
                if list(ast.iter_child_nodes(child_node)): #exclude child leaves
                    node_queue.append((child_node, depth + 1))

        average_type_depths = {
            node_type: round(sum(depths) / len(depths), 2)
            for node_type, depths in depth_dict.items()
        }

        average_type_depths = {'ntad_' + k: v for k,v in average_type_depths.items()}
        return average_type_depths
    
    def _get_num_keywords_density(self):
        """ Returns the log of the total occurrences of keywords in the code 
        divided by the length of the code in terms of characters. """
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for keywords_density")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for keywords_density")
            return default_values[0]
        keywords_sum = sum(self.keywords.values())
        sum_div_by_length = keywords_sum / self.radon_raw_metrics.sloc
        return round(sum_div_by_length, 2)

    def _get_keywords_density(self):
        """Returns the count of each keyword in the code divided by source code lines"""
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning empty dictionary for keywords_density")
            return {}
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning empty dictionary for keywords_density")
            return {}
        keywords_density = {k: round((v / self.radon_raw_metrics.sloc), 2) for k,v in self.keywords.items()}
        # sort the dictionary by key alphabetically
        keywords_density = {k + "_Density": v for k, v in sorted(keywords_density.items(), key=lambda item: item[0])}
        return keywords_density
    
    def _get_radon_halsted_metrics(self):
        """ Returns the Halsted metrics calculated by Radon """
        try:
            h_metrics = h_visit(self.code)
            return {
                'numberOfDistinctOperators': h_metrics.total.h1, 
                'numberOfDistinctOperands': h_metrics.total.h2, 
                'totalNumberOfOperators': h_metrics.total.N1, 
                'totalNumberOfOperands': h_metrics.total.N2,
            }
        except:
            Logger.error_log("Failed to calculate Halsted metrics. Returning default values for all (12) Halsted metrics")
            return {
                'numberOfDistinctOperators': default_values[0],
                'numberOfDistinctOperands ': default_values[0],
                'totalNumberOfOperators': default_values[0],
                'totalNumberOfOperands': default_values[0],
            }

    def _get_radon_cyclomatic_complexity(self):
        """ Returns the Cyclomatic Complexity calculated by Radon """
        try:
            cc = ComplexityVisitor.from_code(self.code)
            return cc.total_complexity
        except:
            Logger.error_log(f"Failed to calculate Cyclomatic Complexity. Returning default value: {default_values[0]} for cyclomatic_complexity")
            return default_values[0]   

    def _get_radon_maintainability_index(self):
        """ Returns the Maintainability Index calculated by Radon """
        try:
            mi = mi_visit(self.code, False)
            return mi
        except:
            Logger.error_log(f"Failed to calculate Maintainability Index. Returning default value: {default_values[0]} for maintainability_index")
            return default_values[0]
    
    def _get_functions_density(self):
        """ 
        Returns the total number of functions divided by the source code lines
        """
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate functions density. Returning default value: {default_values[0]} for functions_density")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"sloc is 0. Returning default value: {default_values[0]} for functions_density")
            return default_values[0]
        return round(self.num_functions / (self.radon_raw_metrics.sloc), 2)    
    
    def _get_num_variables_density(self):
        """ Returns the total number of assignment variables divided by source code lines """
        variables = set()
        if self.tree is None:
            Logger.error_log(f"Failed to parse code to ast. Returning default value: {default_values[0]} for num_variables")
            return default_values[0]
        if self.radon_raw_metrics is None:
            Logger.error_log(f"Failed to calculate Radon metrics. Returning default value: {default_values[0]} for num_variables")
            return default_values[0]
        if self.radon_raw_metrics.sloc == 0:
            Logger.error_log(f"File is empty (code length is 0). Returning default value: {default_values[0]} for num_variables")
            return default_values[0]
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.add(target.id)
        return round((len(variables) / self.radon_raw_metrics.sloc), 2)
    
    def ntype_avg_depths(self):
        depth_dict = {}
        curr_depth = 1
        node_queue = deque([ast.parse(self.tree)])

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

        for eachNode in ast.walk(self.tree):
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
 
def get_uniform_metrics(metrics_list):
    unique_metrics = set()
    for metrics in metrics_list:
        for metric in metrics.keys():
            unique_metrics.add(metric)
    
    for metrics in metrics_list:
        for metric in unique_metrics:
            if metric not in metrics:
                metrics[metric] = 0
        file = metrics.pop('filename')
        
        metrics['filename'] = file
        
        if file.startswith('human'):
            metrics['label'] = 0
        elif file.startswith('ai'):
            metrics['label'] = 1
    return metrics_list

#save metrics to csv
def save_metrics_to_csv(metrics, file_path):
    print(f"Saving metrics to {file_path}")
    print(metrics)
    if metrics:
        with open(file_path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)

project_dir = os.path.dirname(os.path.abspath(__file__))
training_dir = os.path.join(project_dir, "TrainingData")
input_path =  training_dir
output_file = os.path.join(project_dir, "ownset_features.csv")

def extract_metrics(path = input_path):
    metrics_list = []
    for file in os.listdir(path):
        if file.endswith(".py"):
            Logger.info_log(f"Extracting metrics for: {file}")
            with open(os.path.join(path, file), "r") as f:
                code = f.read()
            extracted_metrics = CodeMetricsExtractor(code)
            metrics = extracted_metrics.metrics  
            Logger.info_log(f"Metrics extracted for: {file}\n\n")  
            if extracted_metrics.metrics:
                metrics.update({'filename': file})
                metrics_list.append(metrics)

    uniform_metrics = get_uniform_metrics(metrics_list)
    #save_metrics_to_csv(uniform_metrics, output_file)
    return uniform_metrics


#extract_metrics(input_path)s