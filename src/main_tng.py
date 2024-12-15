import argparse
import functools

from command import step_bootstrap
from sub_command_parser import SubCommandConfiguration, install_sub_commands, no_arguments, resolve_sub_command


def bind_bootstrap(args: argparse.ArgumentParser):
    return functools.partial(command_bootstrap)


def command_bootstrap(args: argparse.ArgumentParser):
  step_bootstrap()


SUB_COMMAND_CONFIG = {
    'bootstrap': SubCommandConfiguration(no_arguments, bind_bootstrap),
}


def main():
  parser = argparse.ArgumentParser(description='Geschichte Eur0pas processing')
  install_sub_commands(SUB_COMMAND_CONFIG, parser)
  args = parser.parse_args()
  func = resolve_sub_command(args)
  func(args)


if __name__ == '__main__':
  main()
