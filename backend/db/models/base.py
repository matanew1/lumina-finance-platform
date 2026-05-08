from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

'''Base class for SQLAlchemy models with a custom naming convention for constraints and indexes.'''
convention = {
    "ix": "ix_%(column_0_label)s", # Indexes will be named as "ix_<column_name>"
    "uq": "uq_%(table_name)s_%(column_0_name)s", # Unique constraints will be named as "uq_<table_name>_<column_name>"
    "ck": "ck_%(table_name)s_%(constraint_name)s", # Check constraints will be named as "ck_<table_name>_<constraint_name>"
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", # Foreign keys will be named as "fk_<table_name>_<column_name>_<referred_table_name>"
    "pk": "pk_%(table_name)s", # Primary keys will be named as "pk_<table_name>"
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
