import re

class LexicalAnalyzer():

    def __init__(self, source_code_text):
        self.source_code_text = source_code_text
        self.len_src_code_text = len(self.source_code_text)
        self.pos = 0
        self.symbol_table = open("symbol_table.tb","w")
        self.error_detected = False
        self.table_var_type = None
        self.lexical_rules = {

            "INT" : "^int$",

            "DOUBLE" : "^double$",

            "STRING" : "^string$",

            "IF" : "^if$",

            "ELSE" : "^else$",

            "FUNCTION" : "^func$",

            "WHILE-LOOP" : "^loop$",

            "FOR-LOOP" : "^for$",

            # It should start with # character and it can contain any characters including space characters such as
            # '\n', '\t' and end with # character again. ( '\s' means all space characters )

            "COMMENT-STMT" : "^\#(.|\s)*\#$",

            # An ID can not be exactly same with a "key" word such as int, double, string, for ....
            # An ID can start with a letter and then it can continue with letter, digit an underscore characters.

            "ID" : "^(?!int$|double$|string$|if$|else$|func$|loop$|for$)^([a-zA-Z]+[\w]*$)",

            # Space and tab delimiters
            "ST-DELIMITER" : "^[ \t]+$",

            # New line delimiter, we are counting the new line delimiters one by one,
            # to be able to detect the if 2 new lines comes after an if, loop, for statements or not.
            # That's why we should create new "N-DELIMITER" token token for each '\n' characters.
            "N-DELIMITER" : "^[\n]{1}$",

            # Assignment Operators
            # Normal assignment operator
            "N-ASSIGN-OPT" : "^=$",

            # Assignment operator with addition
            "A-ASSIGN-OPT" : "^\+=$",

            # Assignment operator with subtraction
            "S-ASSIGN-OPT" : "^\-=$",

            # Assignment operator with multplication
            "M-ASSIGN-OPT" : "^\*=$",

            # Assignment operator with division
            "D-ASSIGN-OPT" : "^\/=$",

            # Logical Operators
            "AND-LOGICAL" : "^[&]{1}[&]{1}$",

            "OR-LOGICAL" : "^[\|]{1}[\|]{1}$",

            "AND-BINARY" : "^[&]{1}$",

            "OR-BINARY" : "^[\|]{1}$",

            "NOT-LOGICAL" : "^\!$",

            # Relational Operators

            "EQ" : "^==$",

            "NE" : "^\!=$",

            "GT" : "^>$",

            "GE" : "^>=$",

            "LT" : "^<$",

            "LE" : "^<=$",

            # Unary Operators

            "INCREMENT" : "^\+\+$",

            "DECREMENT" : "^--$",

            # Arithmetic Operators

            "PLUS" : "^\+$",

            "MINUS" : "^-$",

            "MULT" : "^\*$",

            "DIV" : "^/$",

            "REM" : "^%$",

            # Values of variables

            "INT-VAR" : "^[0-9]+$",

            "DOUBLE-VAR" : "^[0-9]+([\.]{0,1}[0-9]*)((e[+-]{0,1}){0,1})([0-9]{0,1}$|([0-9]{0,1}[0-9]{0,1}$)|(1[0-1]{0,1}[0-9]{0,1}$)|(12[0-8]{1}$))",

            "STRING-VAR" : "^\".*\"$",

            # special key characters

            "OPEN-P" : "^\($",

            "CLOSE-P" : "^\)$",

            "OPEN-B" : "^\{$",

            "CLOSE-B" : "^\}$",

            "COMMA" : "^,$",

            "SEMICOLON" : "^;$"

        }

    def get_next_token(self):

        current_pos = self.pos+1

        possible_will_return_tokens = dict()

        count = 0

        while current_pos != self.len_src_code_text+1:

            possible_token_value = self.source_code_text[self.pos:current_pos]

            is_matched = False

            for key in self.lexical_rules:

                rule = self.lexical_rules[key]

                res = re.search(rule, possible_token_value)
                if res:
                    possible_will_return_tokens[key]=possible_token_value
                    is_matched=True
                count+=1

            if possible_token_value[0] == '\"' and is_matched:
                current_pos+=1
                break
            elif possible_token_value[0] == '\"':
                current_pos+=1
                continue
            elif possible_token_value[0] == '#' and is_matched:
                current_pos+=1
                break
            elif possible_token_value[0] == '#':
                current_pos+=1
                continue
            elif not is_matched:
                break

            current_pos+=1

        if len(possible_will_return_tokens) == 0:

            if (current_pos-1) !=self.len_src_code_text:
                self.__print_error_line(current_pos-1)
            return None

        d_l = { k:len(possible_will_return_tokens[k]) for k in possible_will_return_tokens }
        d_s = {k: v for k, v in sorted(d_l.items(), key=lambda item: item[1], reverse=True)}

        will_return_token = None

        for key in d_s:
            will_return_token = {key:possible_will_return_tokens[key]}
            break


        self.pos = current_pos-1

        if key in will_return_token:
            if len(will_return_token[key]) > 1 and (will_return_token[key][-1] == '\n'):
                will_return_token[key]=will_return_token[key][:-1]
                self.pos-=1

        # check current token if it is a variable type then save it on table_var_type variable with current pos
        # if current token is a ID then check table_var_type position, it should have one previous position then save
        # these as VAR_TYPE and VALUE on symbol table file.
        key_of_token = ""
        for key in will_return_token:
            key_of_token = key
            break

        

        if key == "INT" or key == "DOUBLE" or key == "STRING" or key == "FUNCTION" :
            self.table_var_type = key

        if key == "ID":
            #print(f"{self.table_var_type}, {will_return_token[key]}")
            if self.table_var_type is not None:
                #print(f"{self.table_var_type},{will_return_token[key]}\n")
                self.symbol_table.write(f"{self.table_var_type},{will_return_token[key]}\n") 
                self.symbol_table.flush()
                self.table_var_type = None
        
        # end of file (EOF)
        if will_return_token == None:
            self.symbol_table.close()

        return will_return_token

    def __print_error_line(self, error_index):
        self.error_detected = True
        total_character = 0
        line_index = 1
        error_line = ""
        for line in self.source_code_text.split("\n"):
            total_character += len(line)
            if total_character > error_index:
                error_line = line
                break
            line_index+=1

        error_message = f"There is a lexical error on line {str(line_index)} >> \"{error_line}\""

        print(error_message)

        return error_message
