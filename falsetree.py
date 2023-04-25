import csv
from anytree import Node, RenderTree, NodeMixin

class Tree(NodeMixin):
    def __init__(self):
        self._doi = DOI
        self._authors = author
        self._year = year
        self.child = child
        self._children = []

    def get_author(self):
        return(self._author)
    
    def get_year(self):
        return(self._year)
    
    def get_doi(self):
        return(self._doi)
    
    def make_name(self):
        name = f"{self.get_author()} et al, {self.get_year()} @ {self.get_doi}"
    
    def make_node(self):
        Node(self.make_name(), children=self._children)
    

def main():
    PAPERCHAIN = 'morales_doifix.csv'
    
    tree_nodes = []

    with open(PAPERCHAIN, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            doi = row['parent.doi']
            authors = row[0]['parent.authors']
            year= row['parent.year']
            child = ['child.doi']
            self.children = self.children.append(child)
            node = make_node.self()
            tree_nodes.append(node)
    
    main()
