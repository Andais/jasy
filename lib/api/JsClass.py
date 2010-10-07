#
# JavaScript Tools
# Copyright 2010 Sebastian Werner
#

import os
import logging

from js.Dependencies import collect
from js.Parser import parse
from js.Compressor import compress

uniqueId = 0

class JsClass():
    def __init__(self, path, rel, project):
        global uniqueId
        
        self.path = path
        self.rel = rel
        self.project = project
        self.name = os.path.splitext(self.rel)[0].replace("/", ".")
        self.id = uniqueId
        
        uniqueId += 1

        self.__cache = self.project.cache
        self.__mtime = os.stat(path).st_mtime

        self.__treeKey = "tree[%s]-" % self.rel
        self.__depKey = "deps[%s]-" % self.rel
        self.__breakKey = "breaks[%s]-" % self.rel
        self.__compressedKey = "compressed[%s]" % self.rel


    def getName(self):
        return self.name
        
    def getModificationTime(self):
        return self.__mtime

    def getText(self):
        return open(self.path, mode="r", encoding="utf-8").read()

    def getTree(self, permutation=None):
        field = "tree[%s]-%s" % (self.rel, permutation)
        tree = self.__cache.read(field, self.__mtime)
        if tree == None:
            logging.debug("%s: Generating tree..." % self.name)
            tree = parse(self.getText(), self.path)
            self.__cache.store(field, tree, self.__mtime)
            
        return tree

    def getDependencies(self, permutation=None):
        field = "deps[%s]-%s" % (self.rel, permutation)
        deps = self.__cache.read(field, self.__mtime)
        if deps == None:
            logging.debug("%s: Collecting dependencies..." % self.name)
            deps, breaks = collect(self.getTree(permutation), self.getName())
            self.__cache.store(field, deps, self.__mtime)
            
            field = "breaks[%s]-%s" % (self.rel, permutation)
            self.__cache.store(field, breaks, self.__mtime)
        
        return deps
            
    def getBreakDependencies(self, permutation=None):
        field = "breaks[%s]-%s" % (self.rel, permutation)
        breaks = self.__cache.read(field, self.__mtime)
        if breaks == None:
            self.getDependencies()
            breaks = self.__cache.read(field, self.__mtime)
            
        return breaks
        
    def getCompressed(self, permutation=None):
        compressed = self.__cache.read(self.__compressedKey, self.__mtime)
        if compressed == None:
            logging.debug("%s: Compressing tree..." % self.name)
            tree = self.getTree(permutation)
            compressed = compress(tree)
            self.__cache.store(self.__compressedKey, compressed, self.__mtime)
            
        return compressed
            
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
        
        