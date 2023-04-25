#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: 	Paper.py
# Author: 	Alessandro Gerada, Nada Reza
# Date: 	2023-04-25
# Copyright: 	Alessandro Gerada 2023
# Email: 	alessandro.gerada@liverpool.ac.uk

"""Paper and PaperNode classes"""

from anytree import NodeMixin
import networkx as nx 
from unidecode import unidecode

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
    
    def get_last_author(self):
        try:
            author = self._author[-1]['family']
        except:
            author = None
        return author
    
    def get_all_authors(self):
        try: 
            authors_list = []
            for author in self._author:
                if author != self._author[0] & author != self._author[-1]:
                    family_name = author['family']
                    authors_list.append[family_name]
        except:
            author = None
        return authors_list
    
    def get_references(self):
        return self._references
    
    def get_title(self): 
        return self._title
    
    def get_DOI(self):
        return self._DOI
    
    def get_year(self):
        return self._year   
    
    def make_name(self):
        name = f"{self.get_first_author()} et al, {self.get_year()} ({self.get_DOI()})" 
        return name
    
    def title_score(self, keywords):
        title = self.get_title()
        title = unidecode.unidecode(title)
        title = title.lower()
        title_score = 0
        if title:  
            for keyword in keywords: 
                if keyword[1] in title:
                    title_score + keyword[2]
            return title_score
    
    def author_score(self, important_authors):
        first_author = self.get_first_author()
        all_authors = self.get_all_authors()
        last_author = self.get_last_author()
        first_author = unidecode.unidecode(first_author)
        all_authors = unidecode.unidecode(all_authors)
        last_authors = unidecode.unidecode(last_authors)
        first_author = first_author.lower()
        all_authors = all_authors.lower()
        last_authors = last_authors.lower()

        author_score = 0

        if first_author:
            for author in important_authors:
                if author in first_author:
                    author_score = author_score + (25 * 0.375)
                if author in last_author:
                    author_score = author_score + (25 * 0.375)
                if author in all_authors:
                    author_score = author_score + (1 * 0.25)
                    if author_score > 25:
                        author_score = 25
            return(author_score)
    
    def paper_score(self):
        paper_score = sum(self.title_score() + self.author_score()) * 2
        return(paper_score)
        
class PaperNode(Paper, NodeMixin):
    def __init__(self, DOI, title, author, year, references = None, parent = None, children = None):
        super().__init__(DOI, title, author, year, references)
        self.name = self.make_name()
        self.parent = parent
        if children:
            self.children = children
    
    def add_children(self, children):
        if not children: 
            return
        self.children = children

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
    
    def get_children(self): 
        return self.children
    
    def clear_children(self): 
        self.children = tuple()
    
    def count_ancestors(self):
        ancestors = list(self.ancestors)
        num_ancestors = len(ancestors)
        return num_ancestors
    
class DAGNode(Paper):
    def __init__(self, DOI, title, author, year, references = None, parent= None, score = None):
        super().__init__(DOI, title, author, year, references)
        self._name = self.make_name()
        self._parent=parent
        self._score = self.node_score()
    
    def set_parent(self, parent): 
        self._parent = parent
    
    def get_parent(self): 
        return self._parent

    def frequency_score(self, edge_list):
        counter = 0
        for dagedge in edge_list:
            if self.make_name() in dagedge:
                counter = counter + 1
        if counter > 25:
            frequency_score = 25 * 2
        else:
            frequency_score = counter * 2
        return(frequency_score)

    def depth_score(self, starting_papers, node_list, edge_list):
        root_nodes = []
        for paper in starting_papers:
            root_node = DAGNode(paper) 
            root_nodes.append(root_node) 
        self_node = DAGNode(self) 
        DAG = nx.DiGraph
        DAG.add_nodes_from(node_list)
        DAG.add_edges_from(edge_list)
        root_distance = [] 
        for root in root_nodes:
            shortest_root_node = nx.shortest_path(DAG, source=root, target=self_node)
            root_distance.append[shortest_root_node]
        max_depth = max(root_distance)
        if max_depth > 25:
            depth_score =  25 * 2
        else:
            depth_score = max_depth * 2
        return(depth_score)
    
    def node_score(self):
        self._score = sum(self.frequency_score() + self.depth_score()) 
        return(self._score)       





        
        
    