import os
from re import S
from sys import setprofile
from anytree import Node, RenderTree
from anytree.exporter import DotExporter

class Parser():

    __limit = 10

    def __init__(self,lexical_analyzer, parse_tree_file_name = "trees_out_file.tree"):
        self.lexical_analyzer = lexical_analyzer
        self.c_token_dict = ...
        self.c_token = ... 
        self.error_str = ...
        self.current_stmt = ""
        self.line_count=1
        self.log_tree_indent_c = 0
        self.terminated_tokens = []
        self.info_log_file = open(os.getcwd()+os.sep + "info_log.lg", "w", encoding="utf-8")
        self.parse_tree = Node("flex_start")
        self.parse_tree_file_name = parse_tree_file_name
        self.EOF = False
        self.next_token()
    
    def save_parse_tree_as_file(self):
        
        parse_tree_file = open(self.parse_tree_file_name,"w", encoding="UTF-8")
        parse_tree_file.write("Syntax Analysis Tree ;\n\n")

        for pre, fill, node in RenderTree(self.parse_tree):
            if node.name == "ID" or node.name == "INT-VAR" or node.name == "DOUBLE-VAR" or node.name == "STRING-VAR":
                parse_tree_file.write(f"{pre}{node.name},{node.v}\n")
            else:
                parse_tree_file.write(f"{pre}{node.name}\n")
            parse_tree_file.flush()

        return self.parse_tree, parse_tree_file

    def run(self):

        if self.stmts(self.parse_tree):
            self.print_success_result()    
            return True

        self.print_error_result()
        return False

    def print_success_result(self):
        print("\nSyntax analysis (Parser) process succesfully completed..\n")

    def print_error_result(self):

        error_line = "".join(self.terminated_tokens)

        error_mssg_str = "\nSyntax analysis process (Parser) completed with an error !\n" + \
                                        f"Error Line {self.line_count} -> {error_line.strip()}      Unexpected token -> {self.c_token}\n\n" +\
                                        f"Syntax error : {self.current_stmt}\n" 

        print(error_mssg_str)

    def term(self, t, parent_node=None):

        term = None

        if parent_node is not None:
            term = self.add_node_parse_tree("TERM", parent_node)

        if self.c_token == t:
            if self.c_token == "N-DELIMITER":
                self.line_count+=1
                self.terminated_tokens.clear()

            self.terminated_tokens.append(self.get_value(self.c_token_dict))
            
            if term is not None:
                if t == "ID" or t == "INT-VAR" or t == "DOUBLE-VAR" or t == "STRING-VAR":
                    term = self.add_node_parse_tree(f"{t}", term, attr=self.c_token_dict[t])
                else:
                    term = self.add_node_parse_tree(f"{t}", term)

            self.log("Terminated->",t)
            self.next_token()
            return True

        if term is not None:
            self.remove_node_from_parse_tree(term)
        
        return  False

    # st_delimiters -> ST_DELIMITER st_delimiters | Empty
    def st_delimiters(self):

        self.log("In execution -> ","st-delimiters")

        while self.term("ST-DELIMITER"):
            continue

        return True

    # stn_delimiters -> ST_DELIMITER stn_delimiters | N-DELIMITER stn_delimiters | Empty
    def stn_delimiters(self):

        self.log("In execution -> ","stn-delimiters")

        while self.term("ST-DELIMITER") or self.term("N-DELIMITER"):
            continue
            
        return True

    # single_new_line -> st_delimiters N-DELIMITER st_delimiters | Empty
    def single_new_line(self):

        self.log("In execution -> ","single_new_line")

        count=0
        while self.st_delimiters() and self.term("N-DELIMITER") and self.st_delimiters():
            count+=1
            if count == 1:
                break
                
        return True

    def add_node_parse_tree(self, node_name, parent_node, attr=None):
        return Node(node_name,parent_node, v=attr)

    def remove_node_from_parse_tree(self, node):
        node.parent=None

    # stmts -> n_stmt stmts | func_init_stmt stmts | $ (EOF)
    def stmts(self, parent_node):
        
        stmts = self.add_node_parse_tree("stmts", parent_node)

        self.log("In execution -> ","stmts")

        while (self.stn_delimiters() and self.n_stmt(stmts) and self.stn_delimiters() ) or (self.stn_delimiters() and self.func_init_stmt(stmts) and self.stn_delimiters() ):
            if self.term("EOF",stmts):
                return True
            continue

        if self.term("EOF"):
            self.remove_node_from_parse_tree(stmts)
            self.error(tag="Stmts error",error_message=f"Unexpected variable type -> {self.get_value(self.c_token_dict)}")
            return False
        
    # n_stmts -> stn_delimiters n_stmt stn_delimiters n_stmts | Empty
    def n_stmts(self, parent_node):

        n_stmts = self.add_node_parse_tree("n_stmts", parent_node)

        self.log("In execution -> ","n_stmts")

        while self.stn_delimiters() and self.n_stmt(n_stmts) and self.stn_delimiters():
            continue

        self.check_child_count_and_remove(n_stmts)

        return True

    # n_stmt -> decl_stmt | compound_stmt | if_stmt | for_stmt | loop_stmt | func_call_stmt | assign_stmt | unary_stmt
     
    def n_stmt(self, parent_node):

        n_stmt = self.add_node_parse_tree("n_stmt", parent_node)

        self.log("In execution -> ","n_stmt")
        self.log_tree_indent_c+=1
        
        if self.decl_stmt(n_stmt) or self.compound_stmt(n_stmt) or self.if_stmt(n_stmt) or self.for_stmt(n_stmt)  or \
                self.loop_stmt(n_stmt) or self.ufa_common_stmt(n_stmt)  or self.term("COMMENT-STMT", n_stmt):

            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(n_stmt)
            self.log_tree_indent_c-=1
            return False

    # ufa_common_stmt -> ID ufa_common_stmt_continue
    def ufa_common_stmt(self,parent_node):
        
        ufa_common_stmt = self.add_node_parse_tree("ufa_common_stmt", parent_node)

        self.log("In execution -> ","ufa_common_stmt")
        self.log_tree_indent_c+=1

        if self.term("ID",ufa_common_stmt) and self.ufa_common_stmt_continue(ufa_common_stmt):
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(ufa_common_stmt)
            self.log_tree_indent_c-=1
            return False

    # ufa_common_stmt_continue -> unary_continue | func_call_continue | assign_stmt_wo_id
    def ufa_common_stmt_continue(self, parent_node):
        
        ufa_common_stmt_continue = self.add_node_parse_tree("ufa_common_stmt_continue", parent_node)

        if self.unary_continue(ufa_common_stmt_continue) or self.func_call_continue(ufa_common_stmt_continue) or  self.assign_stmt_wo_id(ufa_common_stmt_continue):
            return True
        else:
            self.remove_node_from_parse_tree(ufa_common_stmt_continue)
            return False

    # decl_stmt -> variable_type st_delimiters decl_stmt_end
    def decl_stmt(self, parent_node):

        decl_stmt = self.add_node_parse_tree("decl_stmt", parent_node)

        self.log("In execution -> ","decl_stmt")
        self.log_tree_indent_c+=1

        if self.variable_type(decl_stmt) and self.st_delimiters() and self.decl_stmt_end(decl_stmt):
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(decl_stmt)
            self.assign_current("Declaration statement")
            self.log_tree_indent_c-=1
            return False

    # variable_type -> INT | DOUBLE | STRING
    def variable_type(self, parent_node):
        
        variable_type = self.add_node_parse_tree("variable_type", parent_node)

        self.log("In execution -> ","variable_type")

        if self.term("INT",variable_type) or self.term("DOUBLE",variable_type) or self.term("STRING",variable_type):
            return True
        else:
            self.remove_node_from_parse_tree(variable_type)
            self.error(tag="Variable type",error_message=f"Unexpected variable type -> {self.get_value(self.c_token_dict)}")
            return False

    # decl_stmt_end -> ID st_delimiters decl_stmt_body st_delimiters SEMICOLON
    def decl_stmt_end(self, parent_node):

        decl_stmt_end = self.add_node_parse_tree("decl_stmt_end", parent_node)

        self.log("In execution -> ","decl_stmt_end")

        if self.term("ID",decl_stmt_end) and self.st_delimiters() and self.decl_stmt_body(decl_stmt_end) and self.st_delimiters() and self.term("SEMICOLON",decl_stmt_end):
            return True
        else:
            self.remove_node_from_parse_tree(decl_stmt_end)
            self.error(tag="Decleration statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # decl_stmt_body -> assignment_operators st_delimiters simple_expr | Empty
    def decl_stmt_body(self, parent_node):

        decl_stmt_body = self.add_node_parse_tree("decl_stmt_body", parent_node)

        self.log("In execution -> ","decl_stmtm_body")

        if self.assignment_operators(decl_stmt_body):
            if self.st_delimiters() and self.simple_expr(decl_stmt_body):
                return True
            else:
                self.remove_node_from_parse_tree(decl_stmt_body)
                self.error(tag="Decleration statement body", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            self.remove_node_from_parse_tree(decl_stmt_body)
            return True

    """# assign_stmt -> assign_stmt_start st_delimiters SEMICOLON
    def assign_stmt(self, parent_node):

        assign_stmt = self.add_node_parse_tree("assign_stmt", parent_node)

        if self.assign_stmt_start(assign_stmt) and self.st_delimiters() and self.term("SEMICOLON",assign_stmt):
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(assign_stmt)
            self.assign_current("Assignment statement")
            self.log_tree_indent_c-=1
            return False"""

    # assign_stmt_start -> ID st_delimiters assignment_operators st_delimiters arithm_expr
    def assign_stmt_start(self, parent_node):

        assign_stmt_start = self.add_node_parse_tree("assign_stmt_start", parent_node)

        self.log("In execution -> ","assign_stmt_start")

        if self.term("ID", assign_stmt_start) and self.st_delimiters() and self.assignment_operators(assign_stmt_start) and self.st_delimiters() and self.arithm_expr(assign_stmt_start):
            return True
        else:
            self.remove_node_from_parse_tree(assign_stmt_start)
            self.error(tag="Assignment statement start", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # assign_stmt_wo_id -> st_delimiters assignment_operators st_delimiters arithm_expr
    def assign_stmt_wo_id(self, parent_node):
        
        assign_stmt_wo_id = self.add_node_parse_tree("assign_stmt_wo_id", parent_node)
       
        self.log("In execution -> ","assign_stmt_wo_id")
        self.log_tree_indent_c+=1

        if self.st_delimiters() and self.assignment_operators(assign_stmt_wo_id) and self.st_delimiters() and self.arithm_expr(assign_stmt_wo_id) and self.st_delimiters() and self.term("SEMICOLON",assign_stmt_wo_id):
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(assign_stmt_wo_id)
            self.assign_current("Assignment statement")
            self.log_tree_indent_c-=1
            return False

    # assignment_operators  → ‘=’ | ‘+=’ | ‘-=’ | ‘*=’ | ‘/=’
    # assignment_operators -> N-ASSIGN-OPT | A-ASSIGN-OPT | S-ASSIGN-OPT | M-ASSIGN-OPT | D-ASSIGN-OPT (with token classes explanation)
    def assignment_operators(self, parent_node):

        assignment_operators = self.add_node_parse_tree("assignment_operators", parent_node)

        self.log("In execution -> ","assignment_operators")

        if self.term("N-ASSIGN-OPT",assignment_operators) or self.term("A-ASSIGN-OPT",assignment_operators) or self.term("S-ASSIGN-OPT",assignment_operators) or self.term("M-ASSIGN-OPT",assignment_operators) or self.term("D-ASSIGN-OPT",assignment_operators):
            return True
        else:
            self.remove_node_from_parse_tree(assignment_operators)
            self.error(tag="Assignment Operators", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # compound_stmt -> OPEN-B stn_delimiters compound_stmt_body  CLOSE-B
    def compound_stmt(self, parent_node):

        compound_stmt = self.add_node_parse_tree("compound_stmt", parent_node)

        self.log("In execution -> ","compound_stmt")
        self.log_tree_indent_c+=1

        if self.term("OPEN-B",compound_stmt) and self.stn_delimiters() and self.n_stmts(compound_stmt) and self.stn_delimiters() and self.term("CLOSE-B",compound_stmt):
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(compound_stmt)
            self.assign_current("Compound statement")
            self.log_tree_indent_c-=1
            return False

    # compound_stmt_body -> stmts | Empty
    def compound_stmt_body(self, parent_node):

        compound_stmt_body = self.add_node_parse_tree("compound_stmt_body", parent_node)

        self.log("In execution -> ","compound_stmt_body")

        while self.n_stmts(compound_stmt_body):
            continue

        self.check_child_count_and_remove(compound_stmt_body)

        return True

    # unary_continue -> unary_operators st_delimiters SEMICOLON
    def unary_continue(self, parent_node):
        
        unary_continue = self.add_node_parse_tree("unary_continue", parent_node)

        self.log("In execution -> ","unary_continue")
        self.log_tree_indent_c+=1
        

        if  self.unary_operators(unary_continue) and self.st_delimiters() and self.term("SEMICOLON",unary_continue):
            self.log_tree_indent_c-=1
            return True
        else:
            #self.error(tag="Unary statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            self.remove_node_from_parse_tree(unary_continue)
            self.assign_current("Unary statement")
            self.log_tree_indent_c-=1
            return False

    # if_stmt -> IF stn_delimiters OPEN-P stn_delimiters bool_expr stn_delimiters CLOSE-P st_delimiters single_new_line n_stmt stn_delimiters if_stmt_end
    def if_stmt(self, parent_node):

        if_stmt = self.add_node_parse_tree("if_stmt", parent_node)

        self.log("In execution -> ","if_stmt")
        self.log_tree_indent_c+=1
        


        if self.term("IF",if_stmt) and self.stn_delimiters() and  self.term("OPEN-P",if_stmt) and self.stn_delimiters() and self.bool_expr(if_stmt) \
            and self.stn_delimiters() and self.term("CLOSE-P",if_stmt) and self.st_delimiters() and self.single_new_line() and self.n_stmt(if_stmt) and self.stn_delimiters() and self.if_stmt_end(if_stmt):
            self.log_tree_indent_c-=1
            
            return True
        else:
            #self.error(tag="If statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            self.remove_node_from_parse_tree(if_stmt)
            self.assign_current("If statement")
            self.log_tree_indent_c-=1
            return False 
     
    # if_stmt_end ->  ELSE if_stmt_end_variations n_stmt
    # if_stmt_end_variations -> st_delimiters | single_new_line

    def if_stmt_end(self, parent_node):

        if_stmt_end = self.add_node_parse_tree("if_stmt_end", parent_node)
        
        self.log("In execution -> ","if_stmt_end")

        if self.term("ELSE",if_stmt_end):
            if  (self.st_delimiters() or self.single_new_line()) and self.n_stmt(if_stmt_end) :
                return True
            else:
                self.remove_node_from_parse_tree(if_stmt_end)
                self.error(tag="Else statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            self.remove_node_from_parse_tree(if_stmt_end)
            return True


    # for_stmt → FOR-LOOP stn_delimiters OPEN-P stn_delimiters for_decl stn_delimiters bool_expr stn_delimiters
    # SEMICOLON stn_delimiters iter_spec stn_delimiters CLOSE-P st_delimiters single_new_line n_stmt
    def for_stmt(self, parent_node):

        for_stmt = self.add_node_parse_tree("for_stmt", parent_node)

        self.log("In execution -> ","for_stmt")
        self.log_tree_indent_c+=1
        

        if self.term("FOR-LOOP",for_stmt) and self.stn_delimiters() and self.term("OPEN-P",for_stmt) and self.stn_delimiters() and  self.for_decl(for_stmt) and self.stn_delimiters() and \
            self.bool_expr(for_stmt) and self.stn_delimiters() and self.term("SEMICOLON",for_stmt) and self.stn_delimiters() and self.iter_spec(for_stmt) and \
            self.stn_delimiters() and self.term("CLOSE-P",for_stmt) and self.st_delimiters() and self.single_new_line() and self.n_stmt(for_stmt):
            self.log_tree_indent_c-=1
            
            return True
        else:
            self.remove_node_from_parse_tree(for_stmt)
            self.assign_current("For statement")
            self.log_tree_indent_c-=1
            return False

    # for_decl -> for_decl_start st_delimiters SEMICOLON | assign_stmt_start st_delimiters SEMICOLON
    def for_decl(self, parent_node):

        for_decl = self.add_node_parse_tree("for_decl", parent_node)

        self.log("In execution -> ","for_decl")

        if ( self.for_decl_start(for_decl) and self.st_delimiters() and self.term("SEMICOLON",for_decl) ) or \
            self.assign_stmt_start(for_decl) and self.st_delimiters() and self.term("SEMICOLON",for_decl):
            return True
        else:
            self.remove_node_from_parse_tree(for_decl)
            self.error(tag="For decl statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False
    
    # for_decl_start -> num_variable_type st_delimiters ID st_delimiters assignment_operators st_delimiters arithm_expr
    def for_decl_start(self, parent_node):

        for_decl_start = self.add_node_parse_tree("for_decl_start", parent_node)

        self.log("In execution -> ","for_decl_start")

        if (self.num_variable_type(for_decl_start) and self.st_delimiters() and self.term("ID", for_decl_start) and \
            self.st_delimiters() and self.assignment_operators(for_decl_start) and self.st_delimiters() and \
            self.arithm_expr(for_decl_start)):
            return True
        else:
            self.remove_node_from_parse_tree(for_decl_start)
            self.error(tag="For decl start statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # num_variable_type -> INT | DOUBLE
    def num_variable_type(self, parent_node):

        num_variable_type = self.add_node_parse_tree("num_variable_type", parent_node)
        
        self.log("In execution -> ", "num_variable_type")

        if self.term("INT",num_variable_type) or self.term("DOUBLE",num_variable_type):
            return True
        else:
            self.remove_node_from_parse_tree(num_variable_type)
            self.error(tag="Num variable type statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # iter_spec -> ID iter_spec_end
    def iter_spec(self, parent_node):

        iter_spec = self.add_node_parse_tree("iter_spec", parent_node)

        self.log("In execution -> ","iter_spec")

        if  self.term("ID",iter_spec) and self.iter_spec_end(iter_spec):
            return True
        else:
            self.remove_node_from_parse_tree(iter_spec)
            self.error(tag="Iter spec statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False
    
    # iter_spec_end -> st_delimiters iter_spec_assign_variations st_delimiters aritm_simple_expr | unary_operators
    def iter_spec_end(self, parent_node):

        iter_spec_end = self.add_node_parse_tree("iter_spec_end", parent_node)

        if (self.st_delimiters() and self.iter_spec_assign_variations(iter_spec_end) and self.st_delimiters() and self.arithm_expr(iter_spec_end)  ) or self.unary_operators(iter_spec_end):
            return True
        else:
            self.remove_node_from_parse_tree(iter_spec_end)
            self.error(tag="Iter spec statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # iter_spec_assign_variations -> A-ASSIGN_OPT | S-ASSIGN_OPT | M-ASSIGN_OPT | D-ASSIGN_OPT
    def iter_spec_assign_variations(self, parent_node):

        iter_spec_assign_variations = self.add_node_parse_tree("iter_spec_assign_variations", parent_node)

        if self.term("A-ASSIGN-OPT",iter_spec_assign_variations) or self.term("S-ASSIGN-OPT",iter_spec_assign_variations) or self.term("M-ASSIGN-OPT",iter_spec_assign_variations) or self.term("D-ASSIGN-OPT",iter_spec_assign_variations):
            return True
        else:
            self.remove_node_from_parse_tree(iter_spec_assign_variations)
            self.error(tag="Iter spec assign variations statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # loop_stmt -> WHILE-LOOP stn_delimiters OPEN-P stn_delimiters bool_expr stn_delimiters CLOSE-P st_delimiters single_new_line n_stmt 
    def loop_stmt(self, parent_node):

        loop_stmt = self.add_node_parse_tree("loop_stmt", parent_node)
        
        self.log("In execution -> ","loop_stmt")
        self.log_tree_indent_c+=1
    

        if self.term("WHILE-LOOP",loop_stmt) and self.stn_delimiters() and self.term("OPEN-P",loop_stmt) and self.stn_delimiters() and self.bool_expr(loop_stmt) and self.stn_delimiters() and \
            self.term("CLOSE-P",loop_stmt) and self.st_delimiters() and self.single_new_line() and self.n_stmt(loop_stmt):
            self.log_tree_indent_c-=1
            
            return True
        else:
            self.remove_node_from_parse_tree(loop_stmt)
            self.assign_current("Loop statement")
            self.log_tree_indent_c-=1
            return False

    # bool_expr -> bool_expr_start_variations stn_delimiters bool_expr_continue
    def bool_expr(self, parent_node):

        bool_expr = self.add_node_parse_tree("bool_expr", parent_node)
    
        self.log("In execution -> ","bool_expr")

        if self.bool_expr_start_variations(bool_expr) and self.stn_delimiters() and self.bool_expr_continue(bool_expr):
            return True
        else:
            self.remove_node_from_parse_tree(bool_expr)
            self.error(tag="Bool expr statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # bool_expr_start_variations -> OPEN-P st_delimiters simple_bool_expr st_delimiters CLOSE-P | simple_bool_expr
    def bool_expr_start_variations(self,parent_node):

        bool_expr_start_variations = self.add_node_parse_tree("bool_expr_start_variations", parent_node)

        self.log("In execution -> ","bool_expr_start_variations")

        if (self.st_delimiters() and self.simple_bool_expr(bool_expr_start_variations) and self.st_delimiters()) or self.simple_bool_expr(bool_expr_start_variations):
            return True
        else:
            self.remove_node_from_parse_tree(bool_expr_start_variations)
            self.error(tag="Bool expr start statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # bool_expr_continue -> logical_operators st_delimiters simple_bool_expr st_delimiters bool_expr_continue | Empty
    def bool_expr_continue(self, parent_node):

        bool_expr_continue = self.add_node_parse_tree("bool_expr_continue", parent_node)

        self.log("In execution -> ", "bool_expr_continue")

        if self.logical_operators(bool_expr_continue):
            if self.st_delimiters() and self.simple_bool_expr(bool_expr_continue) and self.st_delimiters() and self.bool_expr_continue(bool_expr_continue):
                return True
            else:
                self.remove_node_from_parse_tree(bool_expr_continue)
                self.error(tag="Bool expr continue statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            self.check_child_count_and_remove(bool_expr_continue)
            return True
    
    # simple_bool_expr -> simple_expr st_delimiters relational_operators st_delimiters simple_expr
    def simple_bool_expr(self, parent_node):

        simple_bool_expr = self.add_node_parse_tree("simple_bool_expr", parent_node)

        self.log("In execution -> ", "simple_bool_expr")

        if self.simple_expr(simple_bool_expr) and self.st_delimiters() and self.relational_operators(simple_bool_expr) and self.st_delimiters() and self.simple_expr(simple_bool_expr):
            return True
        else:
            self.remove_node_from_parse_tree(simple_bool_expr)
            self.error(tag="Simple bool expr statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # logical_operators -> AND-LOGICAL | OR-LOGICAL | AND-BINARY | OR-BINARY
    def logical_operators(self, parent_node):

        logical_operators = self.add_node_parse_tree("logical_operators", parent_node)

        self.log("In execution -> ", "logical_operators")

        if self.term("AND-LOGICAL",logical_operators) or self.term("OR-LOGICAL",logical_operators) or self.term("AND-BINARY",logical_operators) or self.term("OR-BINARY",logical_operators):
            return True
        else:
            self.remove_node_from_parse_tree(logical_operators)
            self.error(tag="Logical operators statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False
    
    # relational_operators -> EQ | NE | GT | GE | LT | LE
    def relational_operators(self, parent_node):

        relational_operators = self.add_node_parse_tree("relational_operators", parent_node)

        self.log("In execution -> ", "relational_operators")

        if self.term("EQ",relational_operators) or self.term("NE",relational_operators) or self.term("GT",relational_operators) or self.term("GE",relational_operators) or self.term("LT",relational_operators) or self.term("LE",relational_operators):
            return True
        else:
            self.remove_node_from_parse_tree(relational_operators)
            self.error(tag="Relational operators statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False
    
    # unary_operators -> INCREMENT | DECREMENT
    def unary_operators(self, parent_node):

        unary_operators = self.add_node_parse_tree("unary_operators", parent_node)

        self.log("In execution -> ", "unary_operators")

        if self.term("INCREMENT",unary_operators) or self.term("DECREMENT",unary_operators):
            return True
        else:
            self.remove_node_from_parse_tree(unary_operators)
            self.error(tag="Unary operators statement", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # func_init_stmt → func ID ( params_list ) compound_stmt
    # func_init_stmt → stn_delimiters FUNCTION stn_delimiters ID stn_delimiters OPEN-P stn_delimiters params_list stn_delimiters CLOSE-P stn_delimiters compound_stmt stn_delimiters
    def func_init_stmt(self, parent_node):

        func_init_stmt = self.add_node_parse_tree("func_init_stmt", parent_node)

        self.log("In execution -> ", "func_init_stmt")
        self.log_tree_indent_c+=1
        

        if self.stn_delimiters() and self.term("FUNCTION",func_init_stmt) and self.stn_delimiters() and self.term("ID",func_init_stmt) and self.stn_delimiters() \
            and self.term("OPEN-P",func_init_stmt) and self.stn_delimiters() and self.params_list(func_init_stmt) and self.stn_delimiters() \
            and self.term("CLOSE-P",func_init_stmt) and self.stn_delimiters() and self.compound_stmt(func_init_stmt) and self.stn_delimiters():
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(func_init_stmt)
            self.assign_current("Function initialization statement")
            self.log_tree_indent_c-=1
            return False

    # params_list → param_decl st_delimiters params_list_continue | EMPTY
    def params_list(self, parent_node):

        params_list = self.add_node_parse_tree("params_list", parent_node)

        self.log("In execution -> ", "params_list")

        if self.param_decl(params_list):
            if self.st_delimiters() and self.params_list_continue(params_list):
                return True
            else:
                self.remove_node_from_parse_tree(params_list)
                self.error(tag="Parameters list", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            self.check_child_count_and_remove(params_list)
            return True

        

    # params_list_continue → , param_decl params_list_continue | EMPTY
    # params_list_continue → COMMA st_delimiters param_decl st_delimiters params_list_continue | EMPTY
    def params_list_continue(self,parent_node):

        params_list_continue = self.add_node_parse_tree("params_list_continue", parent_node)

        self.log("In execution -> ","params_list_continue")

        while self.term("COMMA",params_list_continue) and self.st_delimiters() and self.param_decl(params_list_continue) and self.st_delimiters():
            continue
        
        self.check_child_count_and_remove(params_list_continue)
        return True

        

    # param_decl → variable_type st_delimiters ID
    def param_decl(self, parent_node):

        param_decl = self.add_node_parse_tree("param_decl", parent_node)

        self.log("In execution ->","param_decl")

        if self.variable_type(param_decl) and self.st_delimiters() and self.term("ID",param_decl):
            return True
        else:
            self.remove_node_from_parse_tree(param_decl)
            self.error(tag="Parameter declaration", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # func_call_continue → ID ( param_values_list ) ;
    # func_call_continue → ID stn_delimiters OPEN-P stn_delimiters params_values_list stn_delimiters CLOSE-P st_delimiters SEMICOLON
    def func_call_continue(self, parent_node):

        func_call_continue = self.add_node_parse_tree("func_call_continue", parent_node)

        self.log("In execution ->","func_call_stmt")
        self.log_tree_indent_c+=1
        

        if  self.stn_delimiters() and self.term("OPEN-P",func_call_continue) and self.stn_delimiters() \
            and self.params_values_list(func_call_continue) and self.stn_delimiters() and self.term("CLOSE-P",func_call_continue) \
            and self.st_delimiters() and self.term("SEMICOLON",func_call_continue):
            
            self.log_tree_indent_c-=1
            return True
        else:
            self.remove_node_from_parse_tree(func_call_continue)
            self.assign_current("Function call statement")
            self.log_tree_indent_c-=1
            return False

    # params_values_list → simple_expr st_delimiters params_value_list_continue | EMPTY
    def params_values_list(self, parent_node):

        params_values_list = self.add_node_parse_tree("params_values_list", parent_node)

        self.log("In execution -> ","params_values_list")

        if self.simple_expr(params_values_list):
            if self.st_delimiters() and self.params_value_list_continue(params_values_list):
                return True
            else:
                self.remove_node_from_parse_tree(params_values_list)
                self.error(tag="Parameters values list", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            self.check_child_count_and_remove(params_values_list)
            return True

        

    # params_value_list_continue  → , simple_expr params_value_list_continue | EMPTY
    # params_value_list_continue  → COMMA st_delimiters simple_expr st_delimiters params_value_list_continue | EMPTY
    def params_value_list_continue(self, parent_node):

        params_value_list_continue = self.add_node_parse_tree("params_value_list_continue", parent_node)

        self.log("In execution -> ","params_value_list_continue")

        while self.term("COMMA",params_value_list_continue) and self.st_delimiters() and self.simple_expr(params_value_list_continue) and self.st_delimiters():
            continue
        
        self.check_child_count_and_remove(params_value_list_continue)
        
        return True

    def check_child_count_and_remove(self, node):
        if len(node.children) == 0:
            self.remove_node_from_parse_tree(node)

    # arithm_simple_expr → ID | INT-VAR | DOUBLE-VAR | OPEN-P stn_delimiters arithm_expr stn_delimiters CLOSE-P
    def arithm_simple_expr(self, parent_node):

        arithm_simple_expr = self.add_node_parse_tree("arithm_simple_expr", parent_node)

        self.log("In execution -> ","arithm_simple_expr")

        if self.term("ID",arithm_simple_expr) or self.term("INT-VAR",arithm_simple_expr) or self.term("DOUBLE-VAR",arithm_simple_expr) or \
            ( self.term("OPEN-P",arithm_simple_expr) and self.stn_delimiters() and self.arithm_expr(arithm_simple_expr) and self.stn_delimiters() and self.term("CLOSE-P",arithm_simple_expr)):
            return True
        else:
            self.remove_node_from_parse_tree(arithm_simple_expr)
            self.error(tag="Arithmetic simple expression", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # arithm_expr → arithm_simple_expr stn_delimiters arithm_expr_end
    def arithm_expr(self, parent_node):

        arithm_expr = self.add_node_parse_tree("arithm_expr", parent_node)

        self.log("In execution -> ","arithm_expr")

        if self.arithm_simple_expr(arithm_expr) and self.stn_delimiters() and self.arithm_expr_end(arithm_expr):
            return True
        else:
            self.remove_node_from_parse_tree(arithm_expr)
            self.error(tag="Arithmetic expression", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # arithm_expr_end → arithm_operators st_delimiters arithm_expr | EMPTY
    def arithm_expr_end(self, parent_node):

        arithm_expr_end = self.add_node_parse_tree("arithm_expr_end", parent_node)

        self.log("In execution -> ","arithm_expr_end")

        if self.arithm_operators(arithm_expr_end):
            if self.st_delimiters() and self.arithm_expr(arithm_expr_end):
                return True
            else:
                self.remove_node_from_parse_tree(arithm_expr_end)
                self.error(tag="Arithmetic expression end", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
                return False
        else:
            # it can be empty so if it i empty then we can remove it from tree
            self.check_child_count_and_remove(arithm_expr_end)
            return True

    # simple_expr → arithm_expr | STRING-VAR 
    def simple_expr(self, parent_node):

        simple_expr = self.add_node_parse_tree("simple_expr", parent_node)

        self.log("In execution -> ","simple_expr")

        if self.arithm_expr(simple_expr) or self.term("STRING-VAR",simple_expr):
            return True
        else:
            self.remove_node_from_parse_tree(simple_expr)
            self.error(tag="Simple expression", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    # arithm_operators → ‘+’ | ’-‘ | ‘*’ | ‘/’ | '%'
    # arithm_operators → PLUS | MINUS | MULT | DIV | REM
    def arithm_operators(self, parent_node):

        arithm_operators = self.add_node_parse_tree("arithm_operators", parent_node)

        self.log("In execution -> ","arithm_operators")

        if self.term("PLUS",arithm_operators) or self.term("MINUS",arithm_operators) or self.term("MULT",arithm_operators) or self.term("DIV",arithm_operators) or self.term("REM",arithm_operators):
            return True
        else:
            self.remove_node_from_parse_tree(arithm_operators)
            self.error(tag="Arithmetic operators", error_message=f"Unexpected token -> {self.get_value(self.c_token_dict)} ")
            return False

    def assign_current(self, stmt):
        self.current_stmt = stmt

    def get_value(self, d):
        for k in d:
            return d[k]
        return None

    def next_token(self):
        self.c_token_dict = self.lexical_analyzer.get_next_token()
    
        if self.c_token_dict is None:

            if not self.lexical_analyzer.error_detected and not self.EOF:
                print("\nLexical analysis process succesfully completed..")
                self.EOF = True
            
            self.c_token_dict =  { "EOF" : "$EOF" }
        

        for key in self.c_token_dict:
            self.c_token = key

    def error(self, tag, error_message):
        if self.error_str == "":
            self.error_str = f">> {tag}: {error_message}\n"

    def log(self, tag, log_message):
        log_tree_tab_indent_str = ""
        for i in range(0,self.log_tree_indent_c):
            log_tree_tab_indent_str +="\t"

        self.info_log_file.write(f"{log_tree_tab_indent_str}{tag}: {log_message} : token {self.c_token}\n ")
        self.info_log_file.flush()

    def get_log_file(self):
        return self.info_log_file