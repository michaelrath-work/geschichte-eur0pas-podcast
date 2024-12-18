import pathlib
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

DB_NAME = pathlib.Path(__file__) / '..' / '..' / 'db' / 'geschichte_eur0pas.db' # TODO(micha): strange path with double ..


Base = declarative_base()


episode_2_episode = Table(
    'episode_2_episode', Base.metadata,
    Column('from_id', Integer,
           ForeignKey('episode.id'),
           primary_key=True),
    Column('to_id', Integer,
           ForeignKey('episode.id'),
           primary_key=True)
)


class Episode(Base):
  __tablename__ = "episode"

  id: Mapped[int] = mapped_column(primary_key=True)
  title = Column(String)
  link = Column(String)
  number = Column(Integer)
  publication_date = Column(String)
  duration_seconds = Column(Integer)

  category_id: Mapped[int] = mapped_column(ForeignKey('category.id'))
  category: Mapped['Category'] = relationship(back_populates='episodes')

  linked_episodes = relationship(
    'Episode',
    secondary=episode_2_episode,
    primaryjoin=id==episode_2_episode.c.from_id,
    secondaryjoin=id==episode_2_episode.c.to_id)


class Category(Base):
  __tablename__ = 'category'

  id: Mapped[int] = mapped_column(primary_key=True)
  marker = Column(String)
  currated_name = Column(String)
  organic_names = Column(String)

  episodes: Mapped[List['Episode']] = relationship(back_populates='category')


class Keyword(Base):
  __tablename__ = 'keyword'

  id: Mapped[int] = mapped_column(primary_key=True)
  name = Column(String)

  episode_id: Mapped[int] = mapped_column(ForeignKey('episode.id'), nullable=True)
