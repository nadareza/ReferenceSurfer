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
        return None
    
    if query['message-type'] == 'work': 
        return query
    else: 
        return None

def surf(current_paper, starting_papers, seen_DOIs, seen_papers, cr, back_to_start_weight=0.01, 
         keyword_discard=0.8, keywords=[]):
    
    if not current_paper.get_references(): 
        return choice(list(starting_papers))
     
    if random() < back_to_start_weight: 
        return choice(list(starting_papers))
    
    random_reference = choice(current_paper.get_references())
    # if we have already seen paper, don't download again

    doi = random_reference.get_DOI()
    if doi not in seen_DOIs:
        query = cr.works(ids=doi)
        try:
            random_paper = make_paper_from_query(query)
        except: 
            return choice(list(starting_papers))
    else: 
        random_paper = next(x for x in seen_papers if x.get_DOI() == doi)
    
    if random() > 0.8: 
        return random_paper
    
    title = random_reference.get_title()
    if title: 
        title = title.lower()
        for i in keywords: 
            if i in title:
                return random_paper
        
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
    seen_papers = dict()

    for i in starting_DOIs:
        result = cr.works(ids = i)
        paper = make_paper_from_query(result)
        starting_papers.add(paper)

    
    for i in starting_papers: 
        refs = i.get_references()
        dois = [i.get_DOI() for i in refs]
        for d in dois: 
            if d: 
                q = query_from_DOI(d)
            else: 
                q = None
            if q: 
                new_paper = make_paper_from_query(q)
                print(new_paper)
            else: 
                print(q)


    paper_pointer = choice(list(starting_papers))
    for _ in range(100): 
        new_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                         keywords=['pharmacokinetics', 'pharmacodynamics'])
        
        if new_paper not in starting_papers: 
            if new_paper not in seen_papers: 
                seen_papers[new_paper] = 1
            else: 
                seen_papers[new_paper] += 1
        
    for i,j in seen_papers.items(): 
        print(f"Paper {i.get_title()} seen {j} times")

main()
