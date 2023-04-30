#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: 	filename.py
# Author: 	Alessandro Gerada, Nada Reza
# Date: 	2023-04-25
# Copyright: 	Alessandro Gerada 2023
# Email: 	alessandro.gerada@liverpool.ac.uk

"""Surfing classes"""

from Paper import Paper

class SurfAction():
    def __init__(self, is_back_to_start: bool): 
        self._is_back_to_start = is_back_to_start

    def is_back_to_start(self): 
        return self._is_back_to_start
    
class BackToStart(SurfAction): 
    def __init__(self): 
        super().__init__(is_back_to_start=True)

class InvalidReferences(SurfAction): 
    def __init__(self): 
        super().__init__(is_back_to_start=True)

class NewPaper(SurfAction): 
    def __init__(self): 
        super().__init__(is_back_to_start=False)

class PreviouslySeenPaper(SurfAction): 
    def __init__(self): 
        super().__init__(is_back_to_start=False)

class LowScorePaper(SurfAction):
    def __init__(self): 
        super().__init__(is_back_to_start=True)

class SurfWrapper(): 
    def __init__(self, paper: Paper, action: SurfAction): 
        self._paper = paper
        self._action = action
    
    def is_back_to_start(self): 
        return self._action.is_back_to_start()
    
    def get_paper(self): 
        return self._paper