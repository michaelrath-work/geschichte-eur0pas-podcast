from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, Mapped, mapped_column


Base = declarative_base()


class Episode(Base):
  __tablename__ = "episode"

  id: Mapped[int] = mapped_column(primary_key=True)
  name = Column(String)
  link = Column(String)
  publication_date = Column(String)
  duration_seconds = Column(Integer)

  keywords: Mapped[List['Keyword']] = relationship()


  def __repr__(self) -> str:
    return f"Episode(id={self.id!r}, name={self.name!r})"


class Category(Base):
  __tablename__ = 'category'

  id: Mapped[int] = mapped_column(primary_key=True)
  marker = Column(String)
  currated_name = Column(String)
  organic_names = Column(String)


class Keyword(Base):
  __tablename__ = 'keyword'

  id: Mapped[int] = mapped_column(primary_key=True)
  name = Column(String)
  episode_id: Mapped[int] = mapped_column(ForeignKey("episode.id"))