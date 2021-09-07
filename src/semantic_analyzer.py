from enum import Enum
import os
import sys
from typing import FrozenSet, no_type_check_decorator
from anytree import RenderTree, Node
from anytree.node import nodemixin

class TYPES(Enum):
    INT = 2
    DOUBLE = 3
    STRING = 4
    UNARY = 5
    BOOL = 6
    VOID = 7
    ERRONEOUS_TYPE = -1,
    NON_TYPE = 1 # for other terms that has no type like as int, double, string or function

class SemanticAnalyzer():

    def __init__(self, parse_tree, info_log_file, trees_out_file):

        self.parse_tree = parse_tree
        self.info_log_file = info_log_file
        self.trees_out_file = trees_out_file
        symbol_table_file = open("symbol_table.tb", "r", encoding="utf-8")
        self.symbol_table = dict()
        self.init_table =  dict()
        self.func_param_table = dict()
        self.id_index = 0
        self.previous_looks = dict()

        for line in symbol_table_file.readlines():

            splitted = line.split(",") 
            id = splitted[1][:-1]
            type_ = splitted[0]

            if not id in self.symbol_table:
                self.symbol_table[id] = type_
            else:
                print(f">> ID : \"{id}\" is already defined in \"{self.symbol_table[id]}\" but it tried to assign as \"{type_}\" type again..\n")
                sys.exit()

    def look_up(self, id):
        try:
            return self.symbol_table[id]
        except KeyError:
            print(f">> ID : {id} is not defined..\n")
            sys.exit()        

    def init_var(self, id):
        self.init_table[id] = True


    def check_var(self, id):
        
        if id in self.init_table:
            return True
        else:
            print(f">> Semantic error : Variable \"{id}\" may not be initialized..\n")
            return False
    
    def define_leaf_child_type(self, token_class, node):
        
        if token_class == "ID":

            t = self.look_up(node.v)

            if t == "INT":
                return TYPES.INT
            elif t == "DOUBLE":
                return TYPES.DOUBLE
            elif t == "STRING":
                return TYPES.STRING
            else:
                return TYPES.NON_TYPE

        elif token_class == "INT-VAR" or token_class == "INT" :
            return TYPES.INT
        elif token_class == "DOUBLE-VAR" or token_class == "DOUBLE":
            return TYPES.DOUBLE
        elif token_class == "STRING-VAR" or token_class == "STRING":
            return TYPES.STRING
        elif (token_class == "EQ") or (token_class == "NE") or (token_class == "GT") or (token_class == "GE") or (token_class == "LT") or (token_class == "LE"):
            return TYPES.BOOL 
        elif token_class == "INCREMENT" or token_class == "DECREMENT":
            return TYPES.UNARY
        else:
            return TYPES.NON_TYPE

    def visit(self, node):
            
        if len(node.children) != 0: # it is a parent node
            for child in node.children:
                self.visit(child)
            #node.name ==
        elif len(node.children) == 0: # leaf child
            self.assign_attr_leaf(node)
            return
        
        # all children type defined here in parent
        # type system rules for each type of parent
        if node.name == "TERM":
            single_child = node.children[0]
            #print(single_child.name)
            child_attr = single_child.t
            self.synthesize_attr(node, child_attr)
            return

        # statement type specific rules begin
        elif node.name == "decl_stmt":
            #print(node.name)
            children = node.children

            if (children[0].t == children[1].t == TYPES.INT) or (children[0].t == children[1].t == TYPES.DOUBLE) or (children[0].t == children[1].t == TYPES.STRING): 
                self.assign_attr_non_leaf(node, TYPES.VOID)
            else:
                self.assign_attr_non_leaf(node, TYPES.ERRONEOUS_TYPE)
                self.print_error(node, "")

            return

        # variable_type = TERM.TYPE
        elif node.name == "variable_type":
            #print(node.name)
            single_child = node.children[0]
            child_attr = single_child.t
            self.synthesize_attr(node, child_attr)


        elif node.name == "decl_stmt_end":
            #print(node.name)
            children = node.children

            if (children[0].t == children[1].t == TYPES.INT):
                self.synthesize_attr(node, TYPES.INT)
            elif(children[0].t == children[1].t == TYPES.DOUBLE):
                self.synthesize_attr(node, TYPES.DOUBLE)
            elif(children[0].t == children[1].t == TYPES.STRING):
                self.synthesize_attr(node, TYPES.STRING)
            elif(children[0].t == TYPES.DOUBLE and children[1].t == TYPES.INT):
                self.synthesize_attr(node, TYPES.DOUBLE)
            elif(children[0].t == TYPES.INT and children[1].t == TYPES.NON_TYPE):
                self.synthesize_attr(node, TYPES.INT)
            else:
                self.assign_attr_non_leaf(node, TYPES.ERRONEOUS_TYPE)
                self.print_error(node, f">> Assignment type error on \"{node.name}\"")

        
        # there is no need to check children 0 because it should be always a non-type terminal.
        elif node.name == "decl_stmt_body":
            #print(node.name)
            children = node.children
            id_v = node.parent.children[0].children[0].v
            self.init_var(id_v)

            if (children[1].t == TYPES.INT):
                self.synthesize_attr(node, TYPES.INT)
            elif(children[1].t == TYPES.DOUBLE):
                self.synthesize_attr(node, TYPES.DOUBLE)
            elif(children[1].t == TYPES.STRING): 
                self.synthesize_attr(node, TYPES.STRING)
            else:
                self.assign_attr_non_leaf(node, TYPES.ERRONEOUS_TYPE)
                self.print_error(node, "")

        elif node.name == "assignment_operators":
            #print(node.name)
            single_child = node.children[0]
            self.synthesize_attr(node, single_child.t)
        
        elif node.name == "arithm_operators":
            #print(node.name)
            single_child = node.children[0]
            self.synthesize_attr(node, single_child.t)

        elif node.name == "simple_expr":
            #print(node.name)
            single_child = node.children[0]
            self.synthesize_attr(node, single_child.t)

        elif node.name == "arithm_simple_expr":
            #print(f"{node.children}")

            node_s = node.children[0].children[0]
            node_name = node_s.name
            
            if node_name == "ID":
                self.check_var(node_s.v)

            
            if len(node.children) == 1:
                self.synthesize_attr(node, node.children[0].t)
            else:
                first_child = node.children[0]
                if first_child.t == TYPES.NON_TYPE:
                    second_child = node.children[1]
                    self.synthesize_attr(node, second_child.t)
                else:
                    self.synthesize_attr(node, first_child.t)
        
        elif node.name == "arithm_expr":
            #print(node.name)
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if TYPES.DOUBLE in all_types:
                self.synthesize_attr(node, TYPES.DOUBLE)
            else:
                self.synthesize_attr(node, TYPES.INT)

        # It should have arithm simple expression as second child 
        # and first child always has to be a arithm operators
        elif node.name == "arithm_expr_end":
            #print(node.name)
            second_child = node.children[1]
            self.synthesize_attr(node, second_child.t)

        elif node.name == "compound_stmt":
            # second child always a n_stmt so it should synthesis type from its second child
            second_child = node.children[1]
            self.synthesize_attr(node, second_child.t)

        elif node.name == "n_stmts":
            
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)
        
        elif node.name == "n_stmt":
            first_child = node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "if_stmt":

            all_types = []

            for child in node.children:
                all_types.append(child.t)
            
            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                if TYPES.BOOL in all_types:
                    self.synthesize_attr(node, TYPES.VOID)
                else: # if there is no child with BOOL type
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

        elif node.name == "bool_expr":
            
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                if TYPES.BOOL in all_types:
                    self.synthesize_attr(node, TYPES.BOOL)
                else:
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
                    
        elif node.name == "bool_expr_start_variations":
            
            first_child = node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "simple_bool_expr":
            
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                if TYPES.BOOL in all_types:
                    self.synthesize_attr(node, TYPES.BOOL)
                else:
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

        elif node.name == "relational_operators":
            first_child = node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "bool_expr_continue":

            if node.children == None:
                self.synthesize_attr(node, TYPES.NON_TYPE)
            else:
                all_types = []
                for child in node.children:
                    try:
                        all_types.append(child.t)
                    except Exception as e:
                        if child.name == "bool_expr_continue":
                            continue

                if TYPES.ERRONEOUS_TYPE in all_types:
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
                else:
                    if TYPES.BOOL in all_types:
                        self.synthesize_attr(node, TYPES.BOOL)
                    else:
                        self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)


        elif node.name == "stmts":
                all_types = []
                for child in node.children:
                    all_types.append(child.t)

                if TYPES.ERRONEOUS_TYPE in all_types:
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
                else:
                    self.synthesize_attr(node, TYPES.VOID)

        elif node.name == "flex_start":
                all_types = []
                for child in node.children:
                    all_types.append(child.t)

                if TYPES.ERRONEOUS_TYPE in all_types:
                    self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
                else:
                    self.synthesize_attr(node, TYPES.VOID)
                    print("Semantic analysis (Type Checking) process succesfully completed..\n")

        elif node.name == "if_stmt_end":
            second_child = node.children[1]
            self.synthesize_attr(node, second_child.t)

        elif node.name == "unary_operators":
            first_child =node.children[0]
            self.synthesize_attr(node, first_child.t)
        
        elif node.name == "iter_spec":
            first_child = node.children[0]
            
            id_v = first_child.children[0].v
            self.check_var(id_v)

            if (first_child.t == TYPES.INT) or (first_child.t == TYPES.DOUBLE):
                self.synthesize_attr(node, TYPES.VOID)
            else:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

        elif node.name == "assign_stmt_start":
            
            # id
            first_child = node.children[0]
            
            id_v = first_child.children[0].v
            self.init_var(id_v)

            # var_type (arithn_simple_expr)
            third_child = node.children[2]

            if first_child.t == third_child.t:
                self.synthesize_attr(node, first_child.t)
            else:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
        
        elif node.name == "num_variable_type":
            first_child =  node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "for_decl":
            self.synthesize_attr(node, node.children[0].t)
        
        elif node.name == "for_decl_start":
            
            id_v = node.children[1].children[0].v
            self.init_var(id_v)
            
            self.synthesize_attr(node, node.children[0].t)
        
        elif node.name == "for_stmt":
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if  TYPES.ERRONEOUS_TYPE in all_types:
                self.symbol_table(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)
        
        elif node.name == "loop_stmt":
            all_types = []
            for child in node.children:
                all_types.append(child.t)

            if  TYPES.ERRONEOUS_TYPE in all_types:
                self.symbol_table(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)

        elif node.name == "ufa_common_stmt":

            first_child = node.children[0]

            second_child = node.children[1]

            if ((first_child.t == TYPES.INT) or (first_child.t == TYPES.DOUBLE)) and second_child.t == TYPES.UNARY:
                self.synthesize_attr(node, TYPES.VOID)
            elif first_child.t == TYPES.NON_TYPE and second_child.t != TYPES.UNARY:
                self.synthesize_attr(node, TYPES.VOID)
            elif (first_child.t ==  second_child.t == TYPES.INT) or (first_child.t ==  second_child.t == TYPES.DOUBLE) or (first_child.t ==  second_child.t == TYPES.STRING):
                # initialization statement
                self.synthesize_attr(node, first_child.t)
            else:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

        elif node.name == "ufa_common_stmt_continue":

            first_child = node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "unary_continue":
            
            # check variable initialized or not
            id_v = node.parent.parent.children[0].children[0].v
            self.check_var(id_v)

            first_child = node.children[0]
            self.synthesize_attr(node, first_child.t)

        elif node.name == "assign_stmt_wo_id":

            # add new initialized variable ID to init table
            id_v = node.parent.parent.children[0].children[0].v
            self.init_var(id_v)
            
            second_child = node.children[1]
            self.synthesize_attr(node, second_child.t)

        elif node.name == "func_init_stmt":
            
            id_v = node.children[1].children[0].v
            self.init_var(id_v)

            # func params types entry creation
            func_name = id_v
            params_list_node = node.children[3]
            func_params_type_arr = []

            if params_list_node.name == "params_list":
                func_params_type_arr.append(params_list_node.children[0].t)
                if len(params_list_node.children) > 1:
                    params_list_continue = params_list_node.children[1]

                    for idx, child_ in enumerate(params_list_continue.children):
                        if idx % 2 != 0:
                            func_params_type_arr.append(child_.t)
                    

            self.func_param_table[func_name] = func_params_type_arr # func_param_table -> { call : [ INT, DOUBLE, ....] }

            all_types = []
            for child in node.children:
                all_types.append(child.t)
            
            if  TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)

        elif node.name == "param_decl":

            id_v = node.children[1].children[0].v
            id_t = node.children[1].children[0].t
            # check id is initialized or not
            if not id_v in self.init_table:
                self.init_var(id_v)
            else:
                print(f">> ID : \"{id_v}\" is already defined in \"{self.symbol_table[id_v]}\" but it tried to assign as \"{id_t}\" type again..\n")

            first_child = node.children[0]
            second_child = node.children[1]

            if first_child.t == second_child.t:
                self.synthesize_attr(node, first_child.t)
            else:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

        elif node.name == "params_list_continue":
            # variable
            second_child = node.children[1]
            self.synthesize_attr(node, second_child.t)

        elif node.name == "params_list":
            all_types = []
            for child in node.children:
                all_types.append(child.t)
            
            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID) 

        elif node.name == "func_call_continue":

            # check variable initialized or not
            id_v = node.parent.parent.children[0].children[0].v
            self.check_var(id_v)

            # paramaters' types comperison
            func_name = id_v

            func_params_arr = self.func_param_table[func_name]

            func_given_params_arr = []
            
            params_value_list_node = node.children[1]

            if params_value_list_node.name == "params_values_list":
                func_given_params_arr.append(params_value_list_node.children[0].t)
                if len(params_value_list_node.children) > 1:
                    params_value_list_continue_node = params_value_list_node.children[1]

                    for idx, child_ in enumerate(params_value_list_continue_node.children):
                        if (idx & 1) == 1: # 01111 & 00001 = 00001 or 00000
                            func_given_params_arr.append(child_.t)
            
            l_func_given_params = len(func_given_params_arr)
            l_func_params = len(func_params_arr)
            
            if l_func_params != l_func_given_params:
                print(f">> Function \"{func_name}\" called with incompatible number of parameters,\n>> It called with {l_func_given_params} number of parameters but it should be called with {l_func_params} number of parameters..\n")
            else:
                for idx, (param, given_param) in enumerate(zip(func_params_arr,func_given_params_arr)):
                    if param != given_param:
                        print(f">> Function \"{func_name}\" called with wrong type parameter as \"{str(given_param)[6:]}\" at index {idx}, it should be \"{str(param)[6:]}\" type..\n")

            all_types = []
            for child in node.children:
                all_types.append(child.t)
            
            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)

        elif node.name == "params_value_list_continue":
            all_types = []
            for child in node.children:
                all_types.append(child.t)
            
            if TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)
            else:
                self.synthesize_attr(node, TYPES.VOID)

        elif node.name == "params_values_list":
            all_types = []
            for child in node.children:
                all_types.append(child.t)
            
            if not TYPES.ERRONEOUS_TYPE in all_types:
                self.synthesize_attr(node, TYPES.VOID)
            else:
                self.synthesize_attr(node, TYPES.ERRONEOUS_TYPE)

    def compute_logic_mult(self, node):
        and_res = 1
        for child in node.children:
            and_res *= child.t
        
        return and_res

    def synthesize_attr(self, node, child_attr):
        node.t = child_attr

    def assign_attr_non_leaf(self, node, attr):
        node.t = attr

    def assign_attr_leaf(self, node):
        node.t = self.define_leaf_child_type(node.name, node)
            
    def print_error(self, node, error_message):
        print(error_message)
        #sys.exit()

    def debug_render_tree(self, node):
        self.info_log_file.write("\n\nSemantic Analysis Tree ;\n\n")
        self.trees_out_file.write("\n\nSemantic Analysis Tree ;\n\n")
        for pre, fill, node in RenderTree(node):
            try:
                """self.info_log_file.write(f"{pre}{node.t.name}\n")
                self.info_log_file.flush()"""
                self.trees_out_file.write(f"{pre}{node.t.name}\n")
                self.trees_out_file.flush()
            except AttributeError:
                #print("Attribute error")
                return

        self.info_log_file.close()
        self.trees_out_file.close()