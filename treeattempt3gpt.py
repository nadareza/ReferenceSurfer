from habanero import Crossref
import csv
from datetime import datetime
from random import random, choice
from anytree import Node, RenderTree, NodeMixin

class Paper:
    def __init__(self, DOI, title, author, year, references = None):
        self._DOI = DOI
        self._title = title[0] if title else None
        self._author = author
        self._year = year
        self._name = self.make_name()
        self._references = []
        if references:
            self.add_references(references)
    
    def add_references(self, references):
        for i in references:
            doi = i['DOI'] if 'DOI' in i else None
            title = i['article-title'] if 'article-title' in i else None
            author = i['author'] if 'author' in i else None
            year = i['year'] if 'year' in i else None
            ref = Paper(doi, title, author, year)
            self._references.append(ref)                     
    
    def __repr__(self) -> str:
        return f"""
        Paper {self._DOI}, author: {self.get_first_author()}, year: {self._year},
        title: {self._title}
        {len(self._references)} references
        """
    
    def __hash__(self): 
        return hash(self._DOI)
    
    def __eq__(self, other):
        if isinstance(other, Paper): 
            return self._DOI == other._DOI
        return NotImplemented
    
    def get_first_author(self): 
        try: 
            author = self._author[0]['family']
        except: 
            author = None
        return author
    
    def get_references(self):
        return self._references
    
    def get_title(self): 
        return self._title
    
    def get_DOI(self):
        return self._DOI
    
    def get_year(self):
        return self._year   
    
    def make_name(self):
        name = f"{self.get_first_author()} et al, {self.get_year()}"
        return name
        
class PaperNode(Paper, NodeMixin):
    def __init__(self, DOI, title, author, year, references = None, parent = None, children = None):
        super().__init__(DOI, title, author, year, references)
        self.name = self.make_name()
        self.parent = parent
        if children:
            self.children = children
    
    # let's not use add_children for now
    def add_children(self, children):
        if not children: 
            return
        self.children = children
        """if not self.children: 
            if len(children) == 1: 
                self.children = []
                self.children.append(children)
            else: 
                self.children = children
        else: 
            if len(children) == 1: 
                self.children.append(children)
            else: 
                for i in children: 
                    self.children.append(i)"""

    def add_child_node(self, child_node): 
        if not child_node: 
            return
        if type(child_node) != PaperNode: 
            raise ValueError("Function .add_child_node() can only take PaperNode for parameter child_node") 
        if child_node in self.get_children(): 
            return
        previous_children = self.get_children()
        new_children = list(previous_children)
        new_children.append(child_node)
        self.children = new_children

        """
        if not self.children: 
            self.children = []
            self.children.append(child_node)
        elif child_node not in self.children:
            self.children.append(child_node)
        else: 
            return
        """
    
    def get_children(self): 
        return self.children
    
    def clear_children(self): 
        self.children = tuple()

    def set_parent(self, parent): 
        self.parent = parent

    def get_parent(self): 
        return self.parent
       
def make_paper_from_query(query):
    message = query['message']
    doi = message['DOI']
    title = message['title']
    author = message['author']
    date_time = message['created']['date-time']
    year = datetime.fromisoformat(date_time).year
    references = message['reference'] if message['references-count'] > 0 else None
    return PaperNode(DOI=doi,
                 title=title,
                 author=author,
                 year=year,
                 references=references)

def query_from_DOI(doi): 
    cr = Crossref()
    try: 
        query = cr.works(doi)
    except: 
        print(f"Failed to pull DOI {doi}")
        return None
    
    if query['message-type'] == 'work': 
        print(f"Found paper: {doi}")
        return query
    
    print(f"Unable to pull {doi}")
    return None

def surf(current_paper, starting_papers, seen_DOIs, seen_papers, cr, back_to_start_weight=0.15, 
         keyword_discard=0.8, keywords=[]):
    
    class SurfWrapper(): 
        def __init__(self, paper: PaperNode, is_back_to_start: bool): 
            self._paper = paper
            self._is_back_to_start = is_back_to_start
        
        def is_back_to_start(self): 
            return self._is_back_to_start
        
        def get_paper_node(self): 
            return self._paper
        
    if not current_paper.get_references(): 
        print(f"Current paper does not have references on system: {current_paper.get_title()}")
        return SurfWrapper(choice(list(starting_papers)),True)
     
    if random() < back_to_start_weight: 
        return SurfWrapper(choice(list(starting_papers)),True)
    
    for _ in range(10): 
        random_reference = choice(current_paper.get_references())
        # if we have already seen paper, don't download again

        doi = random_reference.get_DOI()
        if not doi: 
            if not random_reference.get_title(): 
                print("Empty paper title and empty DOI")
            else:
                print(f"No DOI for {random_reference.get_title()} found")
            continue
        
        if doi not in seen_DOIs:
            try: 
                query = query_from_DOI(doi)
            except: 
                return SurfWrapper(choice(list(starting_papers)),True)
            try:
                random_paper = make_paper_from_query(query)
            except: 
                print(f"Unable to get useful query for: {random_reference.get_title()}")
                continue

        else: 
            print(f"Paper already seen: {random_reference.get_title()}")
            random_paper = next(x for x in seen_papers if x.get_DOI() == doi)
        
        return SurfWrapper(random_paper,False)
        
        """
        title = random_reference.get_title()
        if title: 
            title = title.lower()
            for i in keywords: 
                if i in title:
                    return random_paper
            
        """
    return SurfWrapper(choice(list(starting_papers)), False)

def copy_node(node): 
    """
    Return deep copy of node
    """
    new_node = PaperNode(node.get_DOI(), node.get_title(), node._author, 
                         node.get_year(), parent = node.get_parent())
    return new_node

def walk_tree(node): 
    if not node.get_parent(): 
        return node
    else: 
        new_node = copy_node(node.get_parent())
        new_node.clear_children()
        new_node.add_children(node.get_children())
        return walk_tree(new_node)

def main(): 
    cr = Crossref()
    STARTING_CORPUS_PATH = 'corpus.csv'

    starting_DOIs = set()
    seen_DOIs = set()

    with open(STARTING_CORPUS_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            doi = row['DOI']
            if doi: 
                starting_DOIs.add(doi)

    starting_papers = set()
    seen_papers = set()
    paper_counter = dict()
    tree = []

    for i in starting_DOIs:
        result = query_from_DOI(i)
        paper = make_paper_from_query(result)
        #paper.children = [PaperNode('123', 'test', 'Me', '1920'), PaperNode('456', 'testing', 'you', '1924')]
        starting_papers.add(paper)


    paper_pointer = choice(list(starting_papers))
    for _ in range(10): 
        print(f"iteration {_}")
        new_wrapped_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                         keywords=['pharmacokinetics', 'pharmacodynamics'])
        new_paper = new_wrapped_paper.get_paper_node()
        if not new_wrapped_paper.is_back_to_start(): 
            paper_pointer.add_child_node(new_paper)

        if new_paper not in starting_papers: 
            if new_paper in tree:
                # if we already have a node for this paper in tree, add another node only
                # if parent different to previously recorded nodes
                previous_nodes = [i for i in tree if i == new_paper]
                if not any([True for i in previous_nodes if i.get_parent() == paper_pointer]): 
                    new_paper.set_parent(paper_pointer)
                    tree.append(new_paper)
            else: 
                new_paper.set_parent(paper_pointer)
                tree.append(new_paper)
            if new_paper not in seen_papers: 
                paper_counter[new_paper] = 1
                seen_DOIs.add(new_paper.get_DOI())
                seen_papers.add(new_paper)
            else: 
                paper_counter[new_paper] += 1
        
        if new_paper.get_references(): 
            paper_pointer = new_paper
        elif seen_papers: 
            paper_pointer = choice(list(seen_papers))
        else: 
            paper_pointer = choice(list(starting_papers))
        
    sorted_paper_counter = sorted(paper_counter.items(), key=lambda item: item[1], reverse=True)

    for i,j in sorted_paper_counter: 
        print(f"Paper {i.make_name()} {i.get_title()} DOI {i.get_DOI()} seen {j} times")

    for top_paper,_ in sorted_paper_counter: 
        clean_root = walk_tree(top_paper)
        for pre, fill, node in RenderTree(clean_root): 
                    treestr = u"%s%s" % (pre, node.name)
                    print(treestr.ljust(8))

    with open('rs_output_10.csv', 'w', newline='') as csvfile:

        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(['DOI', 'author', 'title', 'times_seen'])
        for paper,times_seen in paper_counter.items(): 
            writer.writerow([paper.get_DOI(), 
                             paper.get_title(), 
                             paper.get_first_author(),
                             times_seen])

main()
