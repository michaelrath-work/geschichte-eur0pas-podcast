import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dm import Base, Episode, Keyword


def main():
  db_name = pathlib.Path(__file__) / '..' / '..' / 'db' / 'geschichte_eur0pas.db' # TODO(micha): strange path with double ..
  print(db_name.resolve())
  engine = create_engine(f'sqlite:///{db_name.resolve()}', echo=True)
  Base.metadata.create_all(engine)

  Session = sessionmaker(bind=engine)
  session = Session()

  k1 = Keyword(name='k1')
  k2 = Keyword(name='k2')

  new_ep = Episode(
      name='EP 1',
      link='http',
      publication_date='2024-12-15',
      duration_seconds=1235,
      keywords=[k1, k2])
  session.add_all([new_ep, k1, k2])
  session.commit()


if __name__ == '__main__':
  main()