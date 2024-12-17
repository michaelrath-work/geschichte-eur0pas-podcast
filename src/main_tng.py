import argparse
import functools
import logging

from command import (
  step_bootstrap,
  step_export
)
from sub_command_parser import (
  SubCommandConfiguration,
  install_sub_commands,
  no_arguments,
  resolve_sub_command
)


def bind_bootstrap(args: argparse.ArgumentParser):
  return functools.partial(command_bootstrap)


def command_bootstrap(args: argparse.ArgumentParser):
  step_bootstrap()


def bind_export(args: argparse.ArgumentParser):
  return functools.partial(command_export)


def command_export(args: argparse.ArgumentParser):
   step_export()


SUB_COMMAND_CONFIG = {
    'bootstrap': SubCommandConfiguration(no_arguments, bind_bootstrap),
    'export': SubCommandConfiguration(no_arguments, bind_export),
}


def main():
  logging.basicConfig(format='%(asctime)-15s %(name)s %(levelname)s %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S',
                      level=logging.INFO)

  parser = argparse.ArgumentParser(description='Geschichte Eur0pas processing')
  install_sub_commands(SUB_COMMAND_CONFIG, parser)
  args = parser.parse_args()
  func = resolve_sub_command(args)
  func(args)


if __name__ == '__main__':
  main()
