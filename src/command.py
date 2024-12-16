import datetime
import os
import pprint
import pathlib
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_datamodel import Base, Category, DB_NAME, Episode
import rss_datamodel
from rss_datamodel import analyse_channel_data, download_current_feed, poor_mans_csv_parser, read_feed

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

def _delete_db():
  try:
    pathlib.Path.unlink(DB_NAME.resolve())
  except:
    print('Nothing to delete')


def step_bootstrap():
  _delete_db()

  engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
  Base.metadata.create_all(engine)

  Session = sessionmaker(bind=engine)
  session = Session()

  currated_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / 'meta' / 'categories.csv')

  for c in currated_categories:
    # pprint.pprint(c)
    db_cat = Category(
      marker=c.id,
      currated_name=c.name,
      organic_names='',
    )
    session.add(db_cat)
  session.commit()

  local_feed_file_path = download_current_feed()
  channel_xml = read_feed(local_feed_file_path)
  analysis_result = analyse_channel_data(channel_xml, currated_categories)

  def date_to_str(d: datetime.date) -> str:
    return d.strftime('%Y-%m-%d')

  for i, e in enumerate(analysis_result.episodes):

    db_e = Episode(
      title=e.title,
      number=e.number,
      link=e.link,
      publication_date=date_to_str(e.publication_date),
      duration_seconds=e.duration_seconds
    )
    rss_cat = rss_datamodel.Category.adjust(currated_categories, e.category.organic)

    db_cat = session.query(Category).filter(Category.marker == rss_cat.currated_id)[0]
    db_cat.episodes.append(db_e)
    session.add_all([db_e, db_cat])

  session.commit()

  stmt = select(Episode, Category).join(Episode.category).order_by(Episode.title)
  for r in session.execute(stmt):
    pprint.pprint(f'{r.Episode.title} -> {r.Category.marker}: {r.Category.currated_name}')
