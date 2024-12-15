import datetime
import os
import pprint
import pathlib
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_datamodel import Base, DB_NAME, Episode, Keyword, Category
from rss_datamodel import analyse_channel_data, download_current_feed, poor_mans_csv_parser, read_feed

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

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

  currated_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / 'meta' / 'categories.csv')

  for c in currated_categories:
    pprint.pprint(c)
    cat = Category(
      marker=c.id,
      currated_name=c.name,
      organic_names='',
    )
    session.add(cat)
  session.commit()

  local_feed_file_path = download_current_feed()
  channel_xml = read_feed(local_feed_file_path)
  analysis_result = analyse_channel_data(channel_xml, currated_categories)

  def date_to_str(d: datetime.date) -> str:
    return d.strftime('%Y-%m-%d')

  for i, e in enumerate(analysis_result.episodes):
    print(f'{i:03d}')
    db_e = Episode(
      title=e.title,
      number=e.number,
      link=e.link,
      publication_date=date_to_str(e.publication_date),
      duration_seconds=e.duration_seconds
    )
    session.add(db_e)

  session.commit()

  # stmt = select(Episode, Keyword, Category).join(Episode.keywords).join(Episode.category).order_by(Episode.id)
  # for r in session.execute(stmt):
  #   pprint.pprint(f'{r.Episode.name} {r.Keyword.name} {r.Category.marker}')
