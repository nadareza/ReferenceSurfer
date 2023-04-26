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
from anytree import Node, RenderTree
from unidecode import unidecode
from Surf import SurfWrapper, BackToStart, InvalidReferences, NewPaper, PreviouslySeenPaper
from Paper import Paper, PaperNode, DAGNode
import networkx as nx 
import matplotlib.pyplot as plt

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

def make_dagnode_from_paper(paper : Paper):
    dagnode = DAGNode(paper)
    return(dagnode)

def surf(current_paper, starting_papers, seen_DOIs, seen_papers, cr, back_to_start_weight=0.15, 
         keyword_discard=0.8, keywords=[]):
        
    if not current_paper.get_references(): 
        print(f"Current paper does not have references on system: {current_paper.get_title()}")
        return SurfWrapper(choice(list(starting_papers)), 
                           action=InvalidReferences())
    
    if random() < back_to_start_weight: 
        return SurfWrapper(choice(list(starting_papers)),
                           action=BackToStart())
    
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
                print(f"Unable to get query for: {random_reference.get_title()}")
                continue
            try:
                random_paper = make_paper_from_query(query)
                return SurfWrapper(random_paper, 
                                   action=NewPaper())
            except: 
                print(f"Unable to make paper from query for: {random_reference.get_title()}")
                continue

        else: 
            print(f"Paper already seen: {random_reference.get_title()}")
            random_paper = next(x for x in seen_papers if x.get_DOI() == doi)
            return SurfWrapper(random_paper, 
                               action=PreviouslySeenPaper())
      
    return SurfWrapper(choice(list(starting_papers)), 
                       action=BackToStart())
"""""
def copy_node(node): 
    
    Return deep copy of node

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
"""

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
    node_list = dict()
    paired_node_list = []
    edge_list = dict()

    KEYWORDS = 'keywords.csv'
    #IMPORTANT_AUTHORS = 'important_authors.csv'

    keywords = [] 
    important_authors = [] 

    with open(KEYWORDS, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            keyterm = row['keyterms']
            value = row['value']
            keyword = [keyterm, value]
            keywords.append(keyword)
    
    """""
    with open(IMPORTANT_AUTHORS, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            first_author = row['author'][0]
            last_author = row['author'][-1]
            important_authors.append(first_author)
            important_authors.append(last_author)
    """

    for i in starting_DOIs:
        result = query_from_DOI(i)
        paper = make_paper_from_query(result)
        starting_papers.add(paper)
        dag_node = make_dagnode_from_paper(paper)
        node_list[paper] = dag_node

    paper_pointer = choice(list(starting_papers))
    for _ in range(10): 
        print(f"iteration {_}")
        new_wrapped_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                                 back_to_start_weight=0.15)
        new_paper = new_wrapped_paper.get_paper()
        new_paper_score = new_paper.score_paper(keywords, important_authors)
        new_node = make_dagnode_from_paper(new_paper)
           #if the paper scores very low from title and authors, skip over it, likely irrelevant 
        if new_paper_score < 1:
             print(f"Low paper score, likely irrelevant")
             continue
            # choice list starting_papers vs surf vs choice list seen_papers?? vs go back 'Dal segno al coda'

        if new_paper not in node_list:
                node_list[new_paper] = new_node

        if not new_wrapped_paper.is_back_to_start(): 
            new_node.set_parent(paper_pointer)
            new_edge = new_node.make_scoreless_edge()
            paired_node_list.append(new_edge)
            
        if new_paper not in starting_papers: 
            new_node.set_parent(paper_pointer)
            new_edge = new_node.make_scoreless_edge()
            if new_edge in paired_node_list:
                # if we already have a node for this paper in edge list, add another node only
                # if parent different to previously recorded nodes
                previous_nodes = [i for i in edge_list if i == new_edge]
                if not any([True for i in previous_nodes if i.get_parent() == paper_pointer]): 
                    paired_node_list.append(new_edge)
            else: 
                paired_node_list.append(new_edge)
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
    
    for node in paired_node_list:
        freq_score = node.frequency_score(paper_counter)
        depth_score = node.depth_score(starting_papers, node_list, paired_node_list)
        weight_score = sum(freq_score + depth_score)
        scored_node= node.set_score(weight_score)
        scored_edge = scored_node.make_scored_edge()
        edge_list[node](scored_edge)    
    
    DAG = nx.DiGraph
    DAG.add_nodes_from(node_list)
    DAG.add_edges_from(edge_list)
    nx.draw_networkx(DAG, pos)

    with open('rs_output_10.csv', 'w', newline='') as csvfile:

        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(['DOI', 'author', 'title', 'times_seen'])
        for paper,times_seen in paper_counter.items(): 
            writer.writerow([paper.get_DOI(), 
                             paper.get_title(), 
                             paper.get_first_author(),
                             times_seen])

main()

"""""
    for leaf in tree:
     try: 
         print(f" ID:{leaf.name}, parent:{leaf.parent.name}, children{leaf.children.name}")
     except: 
         continue

    tree_roots = set()
    for leaf in tree:
        if leaf.parent == None:
            tree_roots.add(leaf)
        else: 
            continue
    
    for root in tree_roots:
        print(f"Root: {root}")
        for pre, fill, node in RenderTree(root): 
                    treestr = u"%s%s" % (pre, node.name)
                    print(treestr.ljust(8))
"""
