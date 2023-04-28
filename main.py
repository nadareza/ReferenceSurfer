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
from Paper import Paper, DAGNode
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

def make_dagnode_from_paper(paper_name, score : float = None, depth : float = None):
    dagnode = DAGNode(paper_name, score, depth)
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
    depth_list = dict()
    paired_node_list = dict()

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
    
    #Colour nodes by antibiotic class
    ABX_COLOURS = 'antibiotic_colours.csv'

    abx_list = []
    abx_colours = dict()
    abx_classes = dict()
    node_colours = dict()

    with open(ABX_COLOURS, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            abx = row['abx']
            colour = row['colour']
            abxclass = row['class']
            abx_colours[abx] = colour
            abx_classes[abx] = abxclass
            abx_list.append(abx)

    #Add starting corpus as papers, DAG nodes (of depth 0) and calculate scores
    for i in starting_DOIs:
        result = query_from_DOI(i)
        paper = make_paper_from_query(result)
        starting_papers.add(paper)
        paper_name = paper.make_name()
        dag_node = make_dagnode_from_paper(paper_name)
        dag_node.set_depth(0)
        node_list.add(dag_node)
        depth_list[paper_name] = dag_node.get_depth()
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
        try: 
            title = paper.get_title()
            title = unidecode(title)
            title = title.lower()
            for ab in abx_list:
                if ab in title:
                    if paper_name in node_colours:
                        node_colours[paper_name] += abx_colours[ab]
                    else:
                        node_colours[paper_name] = abx_colours[ab]
        except:
            pass
    
    #Start surfing
    paper_pointer = choice(list(starting_papers))
    for _ in range(20): 
        print(f"iteration {_}")
        new_wrapped_paper = surf(paper_pointer, starting_papers, seen_DOIs, seen_papers, cr=cr,
                                 back_to_start_weight=0.15)
        new_paper = new_wrapped_paper.get_paper()
        new_paper_score = new_paper.score_paper(keywords, important_authors)
        new_paper_name = new_paper.make_name()
        new_node = make_dagnode_from_paper(new_paper_name)
        

        #If the paper scores very low based on title and authors, skip over it, likely irrelevant 
        if new_paper_score < 10:
             print(f"""
             Low paper score: {new_paper.get_title()} by {new_paper.get_first_author()}, 
             Total ={new_paper_score}, 
             Title = {new_paper.title_score(keywords)}, 
             Author = {new_paper.author_score(important_authors)} 
             - excluded (likely irrelevant)
             """)
             continue
            # ???choice list starting_papers vs surf vs choice list seen_papers?? vs go back 'Dal segno al coda'
        else:
            print(f"""
            Great paper score! {new_paper.get_title()} by {new_paper.get_first_author()}, 
            Total ={new_paper_score}, 
            Title = {new_paper.title_score(keywords)}, 
            Author = {new_paper.author_score(important_authors)} 
            - included""")

        if new_node not in node_list:
            node_list.add(new_node)

        #If current paper has been arrived at from another paper without jumping - set parent and increase depth
        if not new_wrapped_paper.is_back_to_start(): 
            parent_name = paper_pointer.make_name()
            new_node.set_parent(parent_name)
            parent_depth = depth_list[parent_name]
            new_depth = parent_depth + 1
            new_node.set_depth(new_depth)
            new_node_depth = new_node.get_depth()
            depth_list[new_paper_name] = new_node_depth
            new_edge = new_node.make_scoreless_edge()
            if new_paper_name not in paired_node_list:
                paired_node_list[new_paper_name] = []
                paired_node_list[new_paper_name].append(new_edge)
            else:
                if new_edge not in paired_node_list[new_paper_name]:
                    paired_node_list[new_paper_name].append(new_edge)
                else:
                    pass
        
        #Assign a colour
        new_paper_title = new_paper.get_title()
        for ab in abx_list:
            if ab in new_paper_title:
                    if new_paper_name in node_colours:
                        node_colours[new_paper_name] += abx_colours[ab]
                    else:
                        node_colours[new_paper_name] = abx_colours[ab]
        
        #Keep track of how many times we have seen this paper
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

    #Print our list of papers and how many times we have seen them, in order of frequency   
    sorted_paper_counter = sorted(paper_counter.items(), key=lambda item: item[1], reverse=True)

    for i,j in sorted_paper_counter: 
        print(f"Paper {i.make_name()} {i.get_title()} DOI {i.get_DOI()} seen {j} times")

    #Make pairs for DAG edges
    concat_paired_nodes = []
    for paper_name in paired_node_list:
        for pair in paired_node_list[paper_name]:
            concat_paired_nodes.append(pair)
    
    #Make labels for DAG nodes
    labels = {}
    node_name_list = []
    for node in node_list:
        name = node.get_name()
        labels[name] = f"{name}"  
        node_name_list.append(name)
    
    #Calculate scores for DAG node size
    freq_list = {}
    score_list = {}
    for paper, frequency in paper_counter.items():
        id = paper.make_name()
        freq_list[id] = frequency
    for pap_name in node_name_list:
        if pap_name in freq_list:
            freq_score = freq_list[pap_name]
        else:
            freq_score = 0
        if pap_name in depth_list and depth_list[pap_name] != None: 
            depth_score = depth_list[pap_name]
        else:
            depth_score = 0
        score = freq_score + depth_score + 1
        score_list[pap_name] =  score

    #Colour DAG nodes according to antibiotic
    colour_list = dict()
    for paper_name in node_colours:
        print(f"{node_colours[paper_name]}")
        collist = [node_colours[paper_name]]
        print(f"{colour_list}")
        if len(collist) == 1:
            colour_list[paper_name] = node_colours[paper_name]
        if len(collist) > 1:
            print(f"{collist}")
            colset = set([node_colours[paper_name]])
            print(f"{colset}")
            if len(collist) != len(colset):
               node_colours[paper_name] = list(colset)
               if len(node_colours[paper_name]) > 1: 
                    colour_list[paper_name] = 'gray'
    for paper_name in node_name_list:
        if paper_name not in node_colours:
            colour_list[paper_name] = 'black'

    print(f"""
    COLOUR LIST:
    {colour_list}""")

    DAG = nx.MultiDiGraph()
    DAG.add_nodes_from(node_name_list)
    DAG.add_edges_from(concat_paired_nodes)
    edge_attr = {'alpha' : 0.5}
    nx.draw(DAG, with_labels = True, font_weight= 'bold', font_size=6, node_size=0, edge_color='blue', **edge_attr)
    plt.show()

    with open('rs_output_10.csv', 'w', newline='') as csvfile:

        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(['DOI', 'author', 'title', 'times_seen'])
        for paper,times_seen in paper_counter.items(): 
            writer.writerow([paper.get_DOI(), 
                             paper.get_title(), 
                             paper.get_first_author(),
                             times_seen])

main()
