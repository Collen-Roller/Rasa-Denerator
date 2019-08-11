from rasa_denerator import RasaDenerator

def main():

    arg_parser = RasaDenerator.create_argument_parser()
    args = arg_parser.parse_args()
    denerator = RasaDenerator(nlu_file = args.nlu_file, 
                            actions_dir = args.actions_dir,
                            tag_files = args.tag_files, 
                            output = args.output)
    denerator.generate_domain()
        
if __name__== "__main__":
    main()