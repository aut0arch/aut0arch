import sys
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_java as tsjava

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

filepath = sys.argv[1]

with open(filepath, "rb") as f:
    source_code = f.read()

tree = parser.parse(source_code)
root_node = tree.root_node

query_scm = """
    (method_invocation 
        object: (identifier)? @call.object
        name: (identifier) @call.name
    ) @call.node
"""
query = Query(JAVA_LANGUAGE, query_scm)
cursor = QueryCursor(query)
matches = cursor.matches(root_node)

print(f"File: {filepath}")
print(f"Total matches: {len(matches)}")
for pattern_index, captures_dict in matches:
    print(f"Match pattern {pattern_index}:")
    for tag, nodes in captures_dict.items():
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            content = source_code[node.start_byte:node.end_byte].decode("utf8")
            print(f"  {tag}: {content}")
