import csv
from anytree import Node, RenderTree

root_node = None

# Create dictionary to hold parent nodes
parent_dict = {}
child_dict = {}

# Open CSV file and iterate over rows
with open('morales_doifix.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over rows
    for i, row in enumerate(reader):
        parent_doi = row['parent.doi']
        parent_author = row['parent.authors'].split(',' or '.')[0]
        parent_year = row['parent.year']
        child_doi = row['child.doi']
        child_author = row['child.author']
        child_year = row['child.year']

        # Generate node name
        parent_name = f"{parent_author} et al, {parent_year} "
        child_name = f"{child_author} et al, {child_year}"
        
        # Check if parent node already exists
        if parent_name in parent_dict:
            # If it does, create new child node and add to list of children
            parent_dict[parent_name].children = list(parent_dict[parent_name].children) + [Node(child_name)]
            node = Node(name=parent_name, children=parent_dict[parent_name].children)
            print(node), print(node.children)
                   
        else:
            # If it doesn't, create new parent node and add child node to list of children
            node = Node(name=parent_name, children=[Node(child_name)])
            parent_dict[parent_name] = node 
            print(node), print(node.children)

    # Find the node with no parent and set it as the root (will there be more than one??)
    root_nodes = []
    for parent_name in parent_dict:
        if parent_dict[parent_name].children is None:
            root_node = parent_dict[parent_name]
            root_nodes.append(root_node)

    # Print tree if root node is not None
    for parent_name in parent_dict:
        for pre, fill, node in RenderTree(parent_name):
            treestr = u"%s%s" % (pre, node.name)
            print(treestr.ljust(8), node.name)
    else:
        print("No root nodes found.")  



