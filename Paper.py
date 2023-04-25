#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: 	Paper.py
# Author: 	Alessandro Gerada, Nada Reza
# Date: 	2023-04-25
# Copyright: 	Alessandro Gerada 2023
# Email: 	alessandro.gerada@liverpool.ac.uk

"""Paper and PaperNode classes"""

from anytree import NodeMixin

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
        name = f"{self.get_first_author()} et al, {self.get_year()} ({self.get_DOI()})" 
        return name
        
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

    def set_parent(self, parent): 
        self.parent = parent

    def get_parent(self): 
        return self.parent
    
    def count_ancestors(self):
        ancestors = list(self.ancestors)
        num_ancestors = len(ancestors)
        return num_ancestors