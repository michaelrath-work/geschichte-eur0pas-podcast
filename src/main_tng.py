import argparse
import pathlib
import pprint
import functools
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from dm import Base, Category, Episode, Keyword
from sub_command_parser import SubCommandConfiguration, install_sub_commands, resolve_sub_command

DB_NAME = pathlib.Path(__file__) / '..' / '..' / 'db' / 'geschichte_eur0pas.db' # TODO(micha): strange path with double ..


def add_bootstrap_arguments(parser: argparse.ArgumentParser):
    # parser.add_argument(
    #     '--num-history-days',
    #     help='number of days to process',
    #     type=int,
    #     required=False,
    #     default=14,
    # )
    pass


def bind_bootstrap(args: argparse.ArgumentParser):
    return functools.partial(
        command_bootstrap)


def command_bootstrap(args: argparse.ArgumentParser):
  print (f'hej {args}')
  print(DB_NAME.resolve())
  engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=True)
  Base.metadata.create_all(engine)

  Session = sessionmaker(bind=engine)
  session = Session()

  if False:
    k1 = Keyword(name='k1')
    k2 = Keyword(name='k2')
    category1 = Category(
      marker='A',
      currated_name= 'Epochenübergreifende Themen',
      organic_names = 'a,b,c'
    )

    new_ep = Episode(
        name='EP 1',
        link='http',
        publication_date='2024-12-15',
        duration_seconds=1235,
        keywords=[k1, k2],
        category=category1)
    session.add_all([new_ep, k1, k2, category1])
    session.commit()

  stmt = select(Episode, Keyword, Category).join(Episode.keywords).join(Episode.category).order_by(Episode.id)
  for r in session.execute(stmt):
    pprint.pprint(f'{r.Episode.name} {r.Keyword.name} {r.Category.marker}')



SUB_COMMAND_CONFIG = {
    'bootstrap': SubCommandConfiguration(
        add_bootstrap_arguments, bind_bootstrap),
}



def main():
  parser = argparse.ArgumentParser(description='Geschichte Eur0pas processing')
  install_sub_commands(SUB_COMMAND_CONFIG, parser)
  args = parser.parse_args()
  func = resolve_sub_command(args)
  func(args)


if __name__ == '__main__':
  main()