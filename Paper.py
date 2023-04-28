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
        name = f"""
        {self.get_first_author()} 
        {self.get_year()}""" 
        {self.get_DOI()} 
        return name
    
    def title_score(self, keywords):
        title = self.get_title()
        title_score = float(0)
        if title:  
            title = unidecode(title)
            title = title.lower()
            for keyword in keywords: 
                if keyword[0] in title:
                    value = float(keyword[1])
                    title_score = title_score + value
            return title_score
        else:
            title_score = float(0)
    
    def author_score(self, important_authors):
        first_author = self.get_first_author()
        last_author = self.get_last_author()
        all_authors = self.get_all_authors()
        author_score = float(0)

        if first_author:
            first_author = unidecode(first_author)
            first_author = first_author.lower()
            for author in important_authors:
                if author in first_author:
                    author_score = author_score + (25 * 0.375)
        else:
            author_score = float(0)
        if last_author:
            last_author = unidecode(last_author)
            last_author = last_author.lower()
            for author in important_authors:
                if author in last_author:
                    author_score = author_score + (25 * 0.375)
        else:
            author_score = float(0)
        if all_authors:
            for author in all_authors[:25]:
                author = unidecode(author)
                author = author.lower()
            if author in all_authors:
                author_score = author_score + (1 * 0.25)
        else:
            author_score = float(0)
        if author_score > 25:
            author_score = float(25)
        return(author_score)
    
    def score_paper(self, keywords, important_authors):
        if self.title_score(keywords):
            wt_title_score = float(3 * self.title_score(keywords))
        else:
            wt_title_score = float(0)
        author_score = self.author_score(important_authors)
        paper_score = (wt_title_score + author_score)
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
    
class DAGNode():
    def __init__(self, name, parent : Paper = None, score = None):
        self._name = name
        if parent:
            self._parent = parent.make_name()
        if score:
            self._score = score     
    
    def set_parent(self, parent_name): 
        self._parent = parent_name
    
    def get_parent(self): 
        return self._parent
    
    def get_name(self):
        return self._name

    def make_scoreless_edge(self):
        parent = f"{self._parent}"
        name = f"{self._name}"
        dag_edge = (parent, name)
        return(tuple(dag_edge))
    
    def make_scored_edge(self):
        parent = f"{self._parent}"
        name = f"{self._name}"
        score = self._score
        dag_edge = (parent, name, score)
        return(tuple(dag_edge))
    
    def set_freq_score(self, freq_score):
        self._freq_score = freq_score
        return self._freq_score
    
    def set_depth_score(self, depth_score):
        self._depth_score = depth_score
        return self._depth_score
    """""
    def depth_score(self, starting_papers, node_list, paired_node_list):
        root_nodes = []
        for paper in starting_papers:
            root_node = DAGNode(paper) 
            root_nodes.append(root_node) 
        self_node = DAGNode(self) 
        DAG = nx.DiGraph
        DAG.add_nodes_from(node_list)
        DAG.add_edges_from(paired_node_list)
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
    """ 
    def set_score(self, score):
        self._score = score
        return(self._score)       





        
        
    