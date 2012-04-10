#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import types, logging
from jasy.env.State import setPrefix, startSection

__all__ = ["task"]

class Task:
    __doc__ = ""
    __slots__ = ["__func", "name", "desc", "args", "__doc__"]

    
    def __init__(self, func, desc="", **kwargs):
        name = func.__name__
        self.__func = func
        
        self.name = name
        self.desc = desc
        self.args = kwargs
        
        addTask(self)
        

    def __call__(self, **kwargs):
        
        merged = {}
        merged.update(self.args)
        merged.update(kwargs)
        
        # Use prefix from arguments if available
        # Use no prefix for cleanup tasks
        # Fallback to task name (e.g. "build" task => "build" folder)
        if "prefix" in merged:
            setPrefix(merged["prefix"])
            del merged["prefix"]
        elif "clean" in self.name:
            setPrefix(None)
        else:
            setPrefix(self.name)
        
        # Execute internal function
        return self.__func(**merged)


    def __repr__(self):
        return "Task: " + self.__name__



def task(func, **kwargs):
    """ Specifies that this function is a task. """
    
    if isinstance(func, Task):
        return func

    elif isinstance(func, types.FunctionType):
        return Task(func)
    
    else:
        # Used for called task() (to pass in prefixes, descriptions, etc.)
        def wrapper(finalfunc):
            return Task(finalfunc, func, **kwargs)
            
        return wrapper



# Local task managment
__tasks__ = {}

def addTask(task):
    logging.debug("Registering task: %s" % task.name)
    __tasks__[task.name] = task

def executeTask(name, **kwargs):
    if name in __tasks__:
        startSection("Executing task %s..." % name)
        try:
            __tasks__[name](**kwargs)
        except:
            logging.error("Could not finish task %s successfully!" % name)
            raise
    else:
        raise JasyError("No such task: %s" % name)

def printTasks():
    for name in __tasks__:
        obj = __tasks__[name]
        if obj.desc:
            logging.info("- %s: %s" % (name, obj.desc))
        else:
            logging.info("- %s" % name)


# Jasy reference for executing remote tasks
__jasyCommand = None

def setJasyCommand(cmd):
    global __jasyCommand
    __jasyCommand = cmd


# Remote run support
def runTask(project, task, **kwargs):

    startSection("Running %s of project %s..." % (task, project))

    import subprocess
    from jasy.core.Project import getProjectByName

    # Pauses this session to allow sub process fully accessing the same projects
    session.pause()

    # Build parameter list from optional arguments
    params = ["--%s=%s" % (key, kwargs[key]) for key in kwargs]
    if not "prefix" in kwargs:
        params.append("--prefix=%s" % __prefix)

    # Full list of args to pass to subprocess
    args = [__jasyCommand, task] + params

    # Change into sub folder and execute jasy task
    oldPath = os.getcwd()
    remote = getProjectByName(project)
    if remote is None:
        raise JasyError("Unknown project %s" % project)

    os.chdir(remote.getPath())
    returnValue = subprocess.call(args)
    os.chdir(oldPath)

    # Resumes this session after sub process was finished
    session.resume()

    # Error handling
    if returnValue != 0:
        raise JasyError("Executing of sub task %s from project %s failed" % (task, project))