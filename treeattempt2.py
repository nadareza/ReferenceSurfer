#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: 	main.py
# Author: 	Alessandro Gerada, Nada Reza
# Date: 	2023-03-24
# Copyright: 	Alessandro Gerada, Nada Reza 2023
# Email: 	alessandro.gerada@liverpool.ac.uk

"""Documentation"""

from habanero import Crossref
import csv
from datetime import datetime
from random import random, choice
from anytree import Node, RenderTree, NodeMixin

tree_nodes = set()

class Paper:
    def __init__(self, DOI, title, author, year, references = None):
        self._DOI = DOI
        self._title = title[0] if title else None
        self._author = author
        self._year = year
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
    
def make_paper_from_query(query):
    message = query['message']
    doi = message['DOI']
    title = message['title']
    author = message['author']
    date_time = message['created']['date-time']
    year = datetime.fromisoformat(date_time).year
    references = message['reference'] if message['references-count'] > 0 else None
    return Paper(DOI=doi,
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
    
    if not current_paper.get_references(): 
        print(f"Current paper does not have references on system: {current_paper.get_title()}")
        return choice(list(starting_papers))
     
    if random() < back_to_start_weight: 
        return choice(list(starting_papers))
    
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
                return choice(list(starting_papers))
            try:
                random_paper = make_paper_from_query(query)
            except: 
                print(f"Unable to get useful query for: {random_reference.get_title()}")
                continue
            try:
                if Node(current_paper.make_name()) in tree_nodes:
                    current_paper.add_child(random_paper.make_name())
                else: 
                    new_node =  Node(current_paper.make_name(), children=random_paper.make_name())
                    tree_nodes.add(new_node)
            except: 
                print(f"Unable to make node from P:{current_paper.make_name()} & C:{random_reference.make_name()}")
                continue


        else: 
            print(f"Paper already seen: {random_reference.get_title()}")
            try: 
                query =  query_from_DOI(doi)
                paper = make_paper_from_query(query)
                if Node(paper.make_name()) in tree_nodes:
                    current_paper.add_child(paper.make_name())
                else: 
                    new_node =  Node(current_paper.make_name(), children=paper.make_name())
                    tree_nodes.add(new_node)
            except:
                print(f"Seen but unable to make node for parent {current_paper.get_title} and child {random_reference.get_title}")
            random_paper = next(x for x in seen_papers if x.get_DOI() == doi)
        
        return random_paper
        
        """
        title = random_reference.get_title()
        if title: 
            title = title.lower()
            for i in keywords: 
                if i in title:
                    return random_paper
            
        """
    return choice(list(starting_papers))

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

    for doi in starting_DOIs:
        result = query_from_DOI(doi)
        paper = make_paper_from_query(result)
        starting_papers.add(paper)

    for paper in starting_papers:
        paper_node = Node(paper.make_name(), parent=None)
        tree_nodes.add(paper_node)

    paper_pointer = choice(list(starting_papers))
    for _ in range(20): 
        print(f"iteration {_}")
        new_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                         keywords=['pharmacokinetics', 'pharmacodynamics'])
         
        if new_paper not in starting_papers: 
            if new_paper not in seen_papers: 
                paper_counter[new_paper] = 1
                seen_DOIs.add(new_paper.get_DOI())
                seen_papers.add(new_paper)
            else: 
                paper_counter[new_paper] += 1
                    
        if new_paper.get_references(): 
            if paper_pointer not in starting_papers:
                if paper_pointer not in seen_papers:
                    new_node = Node(paper_pointer.make_name(), children=new_paper.make_name())
                    tree_nodes.add(new_node)
                else:
                    for node in tree_nodes:
                        if node.name == paper_pointer.make_name():
                            node.add_child(new_paper.make_name())
                        else: 
                            continue
            paper_pointer = new_paper
        elif seen_papers: 
            paper_pointer = choice(list(seen_papers))
        else: 
            paper_pointer = choice(list(starting_papers))
    
    sorted_paper_counter = sorted(paper_counter.items(), key=lambda item: item[1], reverse=True)
        
    for i,j in sorted_paper_counter: 
        print(f"Paper {i.make_name()} {i.get_title()} DOI {i.get_DOI()} seen {j} times")
    
    tree_roots = []

    for n in tree_nodes: 
        if n.parent == None:
            tree_roots.append(n)
        else:
            continue

    for root in tree_roots:
        for pre, fill, node in RenderTree(root): 
            treestr = u"%s%s" % (pre, node.name)
            print(treestr.ljust(8))

    with open('trial.csv', 'w', newline='') as csvfile:

        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(['DOI', 'title', 'author', 'year', 'times_seen'])
        for paper,times_seen in paper_counter.items(): 
            writer.writerow([paper.get_DOI(), 
                             paper.get_title(), 
                             paper.get_first_author(),
                             paper.get_year(),
                             times_seen])

main()