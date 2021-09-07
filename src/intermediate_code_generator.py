from sys import setdlopenflags
from anytree import RenderTree
import os

class IntermediateCodeGenerator():

    def __init__(self, parse_tree, lexixal_analyzer):
        self.parse_tree = parse_tree
        self.parsed_leafs = []
        self.lexical_rules = lexixal_analyzer.lexical_rules
        self.conventions = self.get_token_values_list()
        self.var_temps = dict()
        self.generated_three_address_codes = []
        self.three_address_code_file = open(os.path.join(os.getcwd(),"three_address_code"), "w")

    def get_token_values_list(self):
        conventions = dict()
        tokens_file = open("tokens.tk","r")
        for line in tokens_file.readlines():
            splitted = line.split(",")
            conventions[splitted[0]] = splitted[1][:-1]

        return conventions

    def handle_names(self, ast_part):

        names_handled_ast = []
        decl_var_id = ""
        
        if not ast_part[0] in self.var_temps:
            self.var_temps[ast_part[0]] = f"t{len(self.var_temps.keys())}"

        names_handled_ast.append(self.var_temps[ast_part[0]])

        for idx, item in enumerate(ast_part[1:]):
            if item in self.var_temps:
                ast_part[idx+1] = self.var_temps[item]
        
        for item in ast_part[1:]:
            names_handled_ast.append(item)

        return names_handled_ast

    def generate_three_address_codes(self):

        for pre, fill, node in RenderTree(self.parse_tree):

            if node.parent:
                if node.name == "decl_stmt":
                    # create three address code
                    if self.does_contain_rule(node, "decl_stmt_end"):
                        self.create_assign_three_address(node)

    def create_if_three_address(self, node):
        pass

    def create_assign_three_address(self, node):

        leafs = []
        
        for prev, fill, node in RenderTree(node):
            if node.parent.name == "TERM":
                if node.name == "ID" or node.name == "STRING-VAR" or node.name == "INT-VAR" or node.name == "DOUBLE-VAR":
                    leafs.append(node.v)
                else:
                    leafs.append(node.name)
        
        ast_part = leafs[1:len(leafs)-1]
        ast_part = self.convert_token_classes_to_values(ast_part)
        ast_part = self.handle_names(ast_part)
        self.three_address_code_file.write(" ".join(ast_part)+"\n")

    def convert_token_classes_to_values(self, ast_arr):
        
        for idx, item in enumerate(ast_arr):
            if item in self.lexical_rules.keys():
                ast_arr[idx] = self.conventions[item]

        return ast_arr

    def does_contain_rule(self, node, rule_name):
        
        for pre, fill, node in RenderTree(node):
            if rule_name == node.name:
                return True

        return False