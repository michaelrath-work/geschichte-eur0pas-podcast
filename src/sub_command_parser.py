import argparse
import typing
from dataclasses import dataclass


@dataclass
class SubCommandConfiguration:
    add_arguments_func: typing.Callable[[argparse.ArgumentParser], None]
    bind_arguments_to_command_func: typing.Callable[
        [argparse.Namespace],
        typing.Callable[[], typing.Any]]


SubCommandConfigT = typing.Mapping[str, SubCommandConfiguration]


def no_arguments(args: argparse.Namespace):
    pass


def install_sub_commands(cmds: SubCommandConfigT, main_parser: argparse.ArgumentParser):
    subparsers = main_parser.add_subparsers(
        help='sub command to run')

    for command_name, config in cmds.items():
        parser = subparsers.add_parser(command_name)
        parser.set_defaults(dart_sub_command_name=command_name,
                            dart_bind_arguments_to_command_func=config.bind_arguments_to_command_func)
        config.add_arguments_func(parser)


def resolve_sub_command(args: argparse.Namespace):
    return args.dart_bind_arguments_to_command_func(args)
