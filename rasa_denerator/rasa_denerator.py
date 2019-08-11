"""
rasa_denerator.py
August 10, 2019
collen.roller@gmail.com

Domain aggergator to merge disparate files to create a aggregated domain.yml file for Rasa 

See README.md for details

"""

from argparse import ArgumentParser
import ruamel.yaml as yaml
from ruamel.yaml import YAML
import os
import os.path
import sys
import logging
from os import listdir, remove, removedirs, makedirs
from os.path import isfile, join, exists
from typing import Any, Optional, Text, Dict, Set, List
from rasa.nlu.training_data import loading
from rasa.nlu.training_data import Message, TrainingData
from rasa_sdk.executor import ActionExecutor
from pathlib import Path 

VALID_SEARCH_TAGS = ["forms", "actions", "templates", "slots", "entities", "intents"]

logger = logging.getLogger(__name__)

class RasaDenerator:
    
    def __init__(self,
                 nlu_file: Optional[Text] = None,
                 actions_dir: Optional[Text] = None,
                 tag_files: Optional[List] = None,
                 output: Optional[Text] = None
                ) -> None:
        
        self.nlu_file = nlu_file
        self.actions_dir = actions_dir
        self.tag_dict = {} # Convert List to dict for later use
        self.output = output
           
        if tag_files:    
            for pair in tag_files: 
                if pair[0] not in VALID_SEARCH_TAGS:
                    logger.warning("%s is not a valid tag [%s] ignoring" % (pair[0],VALID_SEARCH_TAGS))
                else:
                    self.tag_dict[pair[0]] = pair[1] 
    
        if self.verify_arguments():
            logger.debug("Initialized Denerator with | NLU File: %s, Action Dir: %s, Output_File:%s, Tag Dict: %s" % (self.nlu_file, self.actions_dir, self.tag_dict, self.output))
        else:
            logger.error("At least one argument must be specified\n")
            self.create_argument_parser().print_help()
            sys.exit()
    
    def verify_arguments(self) -> bool:
        if (self.nlu_file or self.tag_dict or self.actions_dir):
            return True
        return False
    
    def generate_domain(self) -> Text:
    
        logger.debug("Generating domain file")
        results = self.get_tagged_entries(self.tag_dict) # Get tagged entities
        
        # if nlu_file is specified, look for intents and entities within the nlu file. 
        # Keep only the intents / entities that were found within the nlu file
        if self.nlu_file:
            logger.debug("Extracting entities and intents from nlu training data (%s)" % self.nlu_file)
            nlu_data = loading.load_data(self.nlu_file)
            if nlu_data:
                # Clear intents / entities since NLU data takes precidence
                results["entities"] = list(nlu_data.entities)
                results["intents"] = list(nlu_data.intents)
                
        # if actions_file is specified, look for registed actions within actions file.
        # Keep only the actions / forms that were found within the NLU file
        if self.actions_dir:
            logger.debug("Extracting actions from action directory (%s)" % self.actions_dir)
            actions = self.get_actions(self.actions_dir)
            if "actions" in actions.keys(): results["actions"] = actions["actions"]
            if "forms" in actions.keys(): results["forms"] = actions["forms"]
         
        logger.debug("Merging identified utterances")
        # If templates exist, append them to the actions
        if "templates" in results.keys() and len(results["templates"]) > 0 and len(results["templates"][0]) > 0:
            results["actions"] = results["actions"] + list(results["templates"][0].keys())       
        
        logger.debug("Formatting output")
        # Iterate through output, identify existing tags, and remove keys that dont exist
        for tag in VALID_SEARCH_TAGS:
            if tag in results.keys() and len(results[tag]) > 0:
                if tag is "templates":
                    print("Found %s %s" % (len(results[tag][0]), tag))
                else: 
                    print("Found %s %s" % (len(results[tag]), tag))
            else:
                # remove the keys from the list
                del results[tag]
                logger.warning("No %s found" % tag)  
    
        # output the results to std out, if an output file was specified, send it there
        yaml = YAML()
        yaml.compact(seq_seq=False, seq_map=False)
        if self.output:
            #output to file
            if os.path.isdir(self.output): 
                logger.error("Output location (%s) is a directory.. can not overwrite" % self.output)
                return "Output location (%s) is a directory.. can not overwrite" % self.output
            elif os.path.isfile(self.output):
                logger.warning("Output file %s already exists, overwritting..." % self.output)
                
            output_path = self.output if os.path.isabs(self.output) else os.path.join(os.path.abspath(os.curdir), self.output)
            
            try:
                stream = open(output_path)
            except IOError:
                stream = open(Path(output_path), "w") #Create the file!
                
            yaml.dump(results, stream)
            print("Results saved to %s" % self.output)
        else:    
            yaml.dump(results, sys.stdout)
            
            
    # Iterates through use specified files and returns tagged information within yml files
    def get_tagged_entries(self, tag_dict):
        
        results = {}
        # Set results for key to an empty list
        for tag in VALID_SEARCH_TAGS:  results[tag] = []

        # iterate through tag_dict and recursivly look through directories for .yml files with tags.
        for key,path in tag_dict.items():
            
            if os.path.isdir(path):  
                # Recursivly find all .yml files within sub directories
                canidates = [os.path.join(subdir, file) 
                             for subdir, dirs, files in os.walk(path) 
                             for file in files if file.endswith(".yml")]
                
                # Read YML Files for key
                for candidate in canidates:
                    # Go through each file and look for elements to add to the results for the key
                    yml = self.get_yml(key, candidate)
                
                    if yml and key in yml: 
                        # if templates, dive down another level
                        if len(results[key]) > 0 and "templates" in key:
                            #from IPython.core.debugger import Tracer; Tracer()()
                            results[key][0].update(yml[key])
                        else:
                            results[key].append(yml[key])
            
            elif os.path.isfile(path) and path.endswith(".yml"):  
                yml = self.get_yml(key, path)
                if yml and key in yml:
                    results[key].append(yml[key])
                    
        return results
    
    # Provide the actions directory that will be mounted for production
    # i.e. actions/actions.py
    #      actions/__init__.py
    # Pass <PATH_TO_ACTIONS_DIRECTORY> 
    def get_actions(self, location):
        if os.path.isdir(location):  
            sys.path.insert(0, location)
            a_exec = ActionExecutor()
            
            # os.path.basename did not work here for some reason unknown.
            a_exec.register_package(Path(location).name)
            actions = list(a_exec.actions.keys())
            # Return a dictionary of actions and forms
            # NOTE: FORM NEEDS TO HAVE FORM IN NAME, ACTIONS NEED ACTION IN NAME
            return {"actions": [item for item in actions if item.startswith("action")], 
                    "forms": [item for item in actions if item.startswith("form")]}
        elif os.path.isfile(location): 
            logger.error("%s must be a model directory, not a file" % location)

        return None
    
    
    # Create class structure 
    def get_yml(self, key, file) -> Optional[Dict]:
        try:
            loaded_yml = yaml.safe_load(open(file, "r"))
            if loaded_yml and key in loaded_yml:
                return {key: loaded_yml[key]}
        except yaml.YAMLError as exc:
            logger.error("Error loading yml file %s" % file)
            logger.error(exc)
        return None 
    
    @staticmethod
    def create_argument_parser() -> ArgumentParser:
        parser = ArgumentParser(
            description='merge disparate Rasa domain files to create or update a aggregated domain.yml')
        parser.add_argument('-o', '--output',
                           required=False,
                           help='-o <PATH_TO_OUTPUT_FILE>')

        parser.add_argument('-nlu', '--nlu_file',
                            required=False,
                            help='-nlu <PATH_TO_NLU_TRAINING_DATA>')

        parser.add_argument('-actions', '--actions_dir',
                            required=False,
                            help='-actions <PATH_TO_ACTIONS_DIRECTORY>')
        
        parser.add_argument('-f', '--find',
                            nargs=2,
                            action='append',
                            dest="tag_files",
                            required=False,
                            help='-f <TAG> <PATH_TO_DIRECTORY_OR_FILE>')  
        return parser