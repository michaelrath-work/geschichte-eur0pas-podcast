import os
import pprint
import pathlib
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from dm import Base, DB_NAME, Episode, Keyword, Category

def _delete_db():
  try:
    pathlib.Path.unlink(DB_NAME.resolve())
  except:
    print('Nothing to delete')


def step_bootstrap():
  _delete_db()

  engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=True)
  Base.metadata.create_all(engine)

  Session = sessionmaker(bind=engine)
  session = Session()

  if True:
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

  engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=True)
  Base.metadata.create_all(engine)

  Session = sessionmaker(bind=engine)
  session = Session()

  stmt = select(Episode, Keyword, Category).join(Episode.keywords).join(Episode.category).order_by(Episode.id)
  for r in session.execute(stmt):
    pprint.pprint(f'{r.Episode.name} {r.Keyword.name} {r.Category.marker}')
