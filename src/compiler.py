from enum import IntFlag
from intermediate_code_generator import IntermediateCodeGenerator
from lexical_analyzer import LexicalAnalyzer
from parser_ import Parser
from semantic_analyzer import SemanticAnalyzer, TYPES
from sys import argv
from anytree import RenderTree
from anytree.exporter import DotExporter


def main():
    test_parser(argv[1])

def test_parser(src_file_path):
    source_file = src_file_path
    source_file = open(source_file, "r", encoding="UTF-8")
    source_code_text = source_file.read()
    analyzer = LexicalAnalyzer(source_code_text)
    parser = Parser(analyzer)
    parser.run()
    parse_tree, trees_out_file = parser.save_parse_tree_as_file()

    semantic_analyzer = SemanticAnalyzer(parse_tree, info_log_file=parser.get_log_file(), trees_out_file=trees_out_file)
    semantic_analyzer.visit(parse_tree)
    semantic_analyzer.debug_render_tree(parse_tree)

    three_address_code_generator = IntermediateCodeGenerator(parse_tree, analyzer)
    three_address_code_generator.generate_three_address_codes()


def test_lexical_analyzer(src_file_path, target_file_path):

    source_file = src_file_path
    target_file = target_file_path
    source_file = open(source_file, "r", encoding="UTF-8")
    target_file = open(target_file, "w", encoding="UTF-8")
    source_code_text = source_file.read()

    analyzer = LexicalAnalyzer(source_code_text)
    token = ""

    while token != None:
        token = analyzer.get_next_token()
        if token != None:
            target_file.write(str(token)+str("\n"))
            target_file.flush()

    target_file.close()

    print(f"\nLexical analysis completed,\nGenerated tokens saved to specified target file -> {target_file_path}\n")

if __name__ == "__main__":
    main()
