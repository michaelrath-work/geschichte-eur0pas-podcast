import pathlib
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

DB_NAME = pathlib.Path(__file__).parent / '..' / 'db' / 'geschichte_eur0pas.db'

Base = declarative_base()

Episode_2_episode = Table(
    'episode_2_episode',
    Base.metadata,
    Column('from_id', Integer,
           ForeignKey('episode.id'),
           primary_key=True),
    Column('to_id', Integer,
           ForeignKey('episode.id'),
           primary_key=True)
)


Episode_2_keyword = Table(
    'episode_2_keyword',
    Base.metadata,
    Column('episode_id', Integer,
           ForeignKey('episode.id'),
           primary_key=True),
    Column('keyword_id', Integer,
            ForeignKey('keyword.id'),
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
        secondary=Episode_2_episode,
        primaryjoin=id==Episode_2_episode.c.from_id,
        secondaryjoin=id==Episode_2_episode.c.to_id)

    keywords = relationship('Keyword', secondary=Episode_2_keyword, back_populates='episodes')


class Category(Base):
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(primary_key=True)
    marker = Column(String)
    curated_name = Column(String)
    # separated by '|'
    organic_names = Column(String)

    episodes: Mapped[List['Episode']] = relationship(back_populates='category')


class Keyword(Base):
    __tablename__ = 'keyword'

    id: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)

    episodes = relationship('Episode', secondary=Episode_2_keyword, back_populates='keywords')
