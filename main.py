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
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx 

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

def make_dagnode_from_paper(paper_name):
    dagnode = DAGNode(paper_name)
    return(dagnode)

def get_dagnode(paper: Paper):
    id = paper.make_name()
    return(tuple(id, ))

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
    node_list = set()
    paired_node_list = dict()
    edge_list = dict()

    KEYWORDS = 'keywords.csv'
    IMPORTANT_AUTHORS = 'important_authors.csv'

    keywords = [] 
    important_authors = [] 

    with open(KEYWORDS, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            keyterm = row['keyterms']
            value = row['value']
            keyword = [unidecode(keyterm).lower(), value]
            keywords.append(keyword)
    
    with open(IMPORTANT_AUTHORS, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            author = row['Last']
            author = unidecode(author)
            author = author.lower()
            important_authors.append(author)

    for i in starting_DOIs:
        result = query_from_DOI(i)
        paper = make_paper_from_query(result)
        starting_papers.add(paper)
        paper_name = paper.make_name()
        dag_node = make_dagnode_from_paper(paper_name)
        node_list.add(dag_node)
        try:
            first_author = paper.get_first_author()
            first_author = unidecode(first_author)
            first_author = first_author.lower()
            if first_author not in important_authors:
                important_authors.append(first_author)
        except:
            pass
        try:
            last_author = paper.get_last_author()
            last_author = unidecode(last_author)
            last_author = last_author.lower()
            if last_author not in important_authors:
                important_authors.append(last_author)
        except:
            pass 

    paper_pointer = choice(list(starting_papers))
    for _ in range(50): 
        print(f"iteration {_}")
        new_wrapped_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                                 back_to_start_weight=0.15)
        new_paper = new_wrapped_paper.get_paper()
        new_paper_score = new_paper.score_paper(keywords, important_authors)
        new_paper_name = new_paper.make_name()
        new_node = make_dagnode_from_paper(new_paper_name)
        

           #if the paper scores very low from title and authors, skip over it, likely irrelevant 
        if new_paper_score < 10:
             print(f"""
             Low paper score: {new_paper.get_title} by {new_paper.get_first_author()}, 
             Total ={new_paper_score}, 
             Title = {new_paper.title_score(keywords)}, 
             Author = {new_paper.author_score(important_authors)} 
             - therefore likely irrelevant
             """)
             continue
            # choice list starting_papers vs surf vs choice list seen_papers?? vs go back 'Dal segno al coda'
        else:
            print(f"""
            Great paper score! {new_paper.get_title} by {new_paper.get_first_author()}, 
            Total ={new_paper_score}, 
            Title = {new_paper.title_score(keywords)}, 
            Author = {new_paper.author_score(important_authors)} 
            - paper included""")

        if new_node not in node_list:
            node_list.add(new_node)

        if not new_wrapped_paper.is_back_to_start(): 
            parent_name = paper_pointer.make_name()
            new_node.set_parent(parent_name)
            new_edge = new_node.make_scoreless_edge()
            if new_paper_name not in paired_node_list:
                paired_node_list[new_paper_name] = []
                paired_node_list[new_paper_name].append(new_edge)
            else:
                if new_edge not in paired_node_list[new_paper_name]:
                    paired_node_list[new_paper_name].append(new_edge)
                else:
                    pass
        
        if new_paper not in starting_papers: 
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

    concat_paired_nodes = []
    root_nodes = []
    for paper_name in paired_node_list:
        for pair in paired_node_list[paper_name]:
            concat_paired_nodes.append(pair)
    for paper in starting_papers:
        paper_name = paper.make_name()
        if paper_name in node_list:
            root_nodes.append(paper_name)
    labels = {}
    node_name_list = []
    for node in node_list:
        name = node.get_name()
        labels[name] = f"{name}"  
        node_name_list.append(name)
    print(f"""
    Labels: {labels}""")
    print(f"""Node Name List: 
    {node_name_list}""")
    print(f"""Paired Node List:
           {paired_node_list}""")
    print(f"""Edge List:
           {edge_list}""")
    print(f"""Concatenated Paired List:
           {concat_paired_nodes}""")
    print(f"""Paper Counter:
           {paper_counter}""")
    
    seed = 16454
    scoring_DAG = nx.DiGraph()
    pos = nx.spring_layout(scoring_DAG, seed=seed)
    scoring_DAG.add_nodes_from(node_name_list)
    scoring_DAG.add_edges_from(concat_paired_nodes)
    nx.draw(scoring_DAG, with_labels = True, font_weight= 'bold', font_size=6)
    #nx.draw_networkx_labels(scoring_DAG, pos=nx.spring_layout(scoring_DAG), labels=labels, font_size=8, font_color='green')
    plt.show()
    
    """""
    for paper_name in node_name_list:
        root_distances = [] 
        for root in root_nodes:
            shortest_root_node = nx.shortest_path_length(scoring_DAG, source=root, target=paper_name)
            print(f"shortest path:{shortest_root_node}")
            root_distances.append[shortest_root_node]
    print("hello!")
    print(root_distances)
    """
        #depth_score = max(root_distances)
        #freq_score = len(paired_node_list[paper_name])
        #weight_score = freq_score + depth_score
        #paper_name.set_score(weight_score)
        #scored_edge = paper_name.make_scored_edge()
        #edge_list[paper](scored_edge) 
    """""
    DAG = nx.DiGraph()
    DAG.add_nodes_from(edge_list)
    DAG.add_edges_from(edge_list)
    nx.draw_networkx(DAG, pos)
    """
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
