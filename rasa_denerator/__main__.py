from rasa_denerator import RasaDenerator
import sys

def main():

    arg_parser = RasaDenerator.create_argument_parser()
    args = arg_parser.parse_args()
    
    tag_dict = {}
    if args.tag_files:
        tag_dict = RasaDenerator.convert_tags(args.tag_files)

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