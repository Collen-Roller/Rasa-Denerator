# Rasa Denerator

A simple way of generating a domain.yml file for Rasa

**Works with legacy versions of rasa || rasa 1.x!**

Developed with Python 3.7.x

## Installation

```bash
$ pip install rasa_denerator
```

After installation, the component can be used via command line or within a python script, we provide scenarios for both.

## Usage

### CLI

The example below will create a domain file from an actions module, nlu training data and templates

```bash
$ rasa_denerator -actions Rasa-Denerator/notebooks/denerator_tests/actions -f templates Rasa-Denerator/notebooks/denerator_tests/data -nlu Rasa-Denerator/notebooks/denerator_tests/data/nlu/nlu.md 
 ```
 
 ```bash
usage: rasa_denerator [-h] [-o OUTPUT] [-nlu NLU_FILE]
                         [-actions ACTIONS_DIR] [-f TAG_FILES TAG_FILES]

merge disparate Rasa domain files to create or update a aggregated domain.yml

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        -o <PATH_TO_OUTPUT_FILE>
  -nlu NLU_FILE, --nlu_file NLU_FILE
                        -nlu <PATH_TO_NLU_TRAINING_DATA>
  -actions ACTIONS_DIR, --actions_dir ACTIONS_DIR
                        -actions <PATH_TO_ACTIONS_DIRECTORY>
  -f TAG_FILES TAG_FILES, --find TAG_FILES TAG_FILES
                        -f <TAG> <PATH_TO_DIRECTORY_OR_FILE>
 ```

The script will output to the std.out unless an output file is specific. 

Queries can get quite complex. For example, you could specify the following:
```bash
rasa_denerator -actions Rasa-Denerator/notebooks/denerator_tests/actions \ 
         -f templates Rasa-Denerator/notebooks/denerator_tests/data \
         -f slots Rasa-Denerator/notebooks/denerator_tests/data/ \
         -nlu Rasa-Denerator/notebooks/denerator_tests/data/nlu/nlu.md \
         -o domain.yml
 ```

### Python

If you'd like to use the denerator within a python script, you can do that too!
```python
from rasa_denerator import RasaDenerator

nlu_file = "denerator_tests/data/nlu/nlu.md"
actions_dir = "denerator_tests/actions/"
tag_dict = {"templates":"denerator_tests/data/domain", "slots": "denerator_tests/data/domain", "entities":"denerator_tests/data/domain"}
output_file = "domain.yml"

denerator = RasaDenerator(nlu_file = nlu_file, 
                        actions_dir = actions_dir,
                        tag_dict = tag_dict,
                        output = output_file)
denerator.generate_domain()

```

## Explanation

Creating a domain.yml file currently is a tedious process within Rasa.  Take this example below

Here is a sample structure that your rasa project might look like right now.

```
your_rasa_project
│   README.md
│   other stuff...   
│
└───data (This is where you store all your data)
│   nlu.md
|   domain.yml
|       
└───actions (This is where your action.py lives for rasa_sdk)
    │   __init__.py
    │   actions.py
    |   other_code.py
```

Currently the developer must hand create the domain file using multiple assets from other files that already exists within other parts of the application. Here are some points below
 
1. Entities and intents that are placed within training data files must be copied manually to a domain.yml file prior to training. 
2. Custom action names must be listed within the domain.yml file. Developers currently need to manually extract these names from their custom action classes everytime they add a new actions prior to retraining
3. Templates are defined within the domain.yml file. These templates are utterances that can be returned to the user at certain trained points within the dialogue. Once these template utterances are defined, their identifies must be manually copied to the actions section of the domain.yml file.

You might have felt these pain points before...

To alleviate some pain, I created this tool to automatically generate a domain.yml file

### Dev considerations: 
- Automatically generate intents based on intents listed within NLU training data
- Automatically generate actions based on a valid actions module  
- Automatically aggergate forms, actions, slots, utterances listed within a specific directory recursivly
- If NLU training data exists or Actions module exists, tags read in for entities, intents, actions, or forms are ignored
- Make it command line version accessable
- Make it easy to include within another script

### A Better Layout

Instead of hand creating these domain files and updating them constantly as you create new entities, intents, utterances, and actions consider the layout below. 

```
your_rasa_project
│   README.md
│   other stuff...   
│
└───data (This is where you store all your data)
│   │
│   └───nlu
│       │   nlu.md
|       |
│   └───domain
│       │   templates_1.yml (file containing templates)
|       |   templates_2.yml (file containing more templates...)
│       │   slots_1.yml (file containing slots)
|       |   slots_2.yml (file containing more slots...)
│       │   entities.yml (file containing entities, these entities will take precedence over entities found in the nlu.md)
│       │   intents.yml (file containing intents, these intent will take precedence over entities found in the nlu.md)
|       
└───actions (This is where your action.py lives for rasa_sdk)
    │   __init__.py
    │   actions.py
    |   other_code.py
```

#### Utterances

All utterance templates can be defined within a set of yml files. The script will automatically extract these templates and add them to a domain file as templates and registed actions. Additionally, the script will append these to registered utterances to the registered actions within the generated domain file. 

#### Entities and Intents

Entities and intents will be extracted from the nlu.md training data file. This script uses Rasa's training_data functions to load and extract entities and intents. This allows us to accept markdown, json, etc. Entities and intents within the training data are extracted and placed into the output file.

If you want to hand-define entities and intents, thats fine too. Just create a folder or file that contains them and pass it to the script. 

Note: If a entities or intents are specified, they will take precidence over entities and intents identified within the nlu training data file.

#### Actions

Most Rasa users define custom actions. Copying these names from their respective classes and copying them into the domain file is currently tedious. The denerator fixes this my using rasa_sdk to  load the repsective action module created by the user, extract the class names, and automatically add them to the domain file.

## Tests

All unit tests are within the notebook file and can be run here. I prototyped all code within the notebook, all unit tests can be found there.

## License 

MIT 2019

## Questions

Contact me at collen.roller@gmail.com
