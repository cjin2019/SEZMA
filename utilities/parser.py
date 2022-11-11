def check_process_inputs(args: dict, args_type: dict) -> None:
    """
    Checks the inputs per process. Raises an exception is missing argument or argument is not correct type
    """
    for arg_name in args_type:
        expected_type = args_type[arg_name]
        if arg_name not in args:
            raise Exception(f"Missing {arg_name} in config.json")
        curr_type = type(args[arg_name])
        if curr_type != args_type[arg_name]:
            raise TypeError(f"Wrong type for {arg_name}. {arg_name} is of type {curr_type} but should be {expected_type}")

def parse_swift_output(input: bytes) -> str:
    """
    Parses the swift output from the subprocess output
    """
    line: str = input.decode('utf8', 'strict')
    return line[line.index(" ")+1:]