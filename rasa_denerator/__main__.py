from rasa_denerator import RasaDenerator
import sys

def main():

    arg_parser = RasaDenerator.create_argument_parser()
    args = arg_parser.parse_args()
    
    tag_dict = {}
    if args.tag_files:    
        for pair in args.tag_files: 
            if pair[0] not in ["forms", "actions", "templates", "slots", "entities", "intents"]:
                print("%s is not a valid tag [%s] ignoring" % pair[0])
            else:
                tag_dict[pair[0]] = pair[1] 

    if not (args.nlu_file or tag_dict or args.actions_dir):
        arg_parser.error('At least one argument must be present to run')

    denerator = RasaDenerator(nlu_file = args.nlu_file, 
                            actions_dir = args.actions_dir,
                            tag_dict = tag_dict, 
                            output = args.output)
    denerator.generate_domain()
    
def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

if __name__== "__main__":
    main()