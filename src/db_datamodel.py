import pathlib
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

DB_NAME = pathlib.Path(__file__) / '..' / '..' / 'db' / 'geschichte_eur0pas.db' # TODO(micha): strange path with double ..


Base = declarative_base()


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
