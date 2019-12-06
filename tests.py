import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

DATABASE_URL = 'postgres://rwkradveffikre:28272880b7cc5fe661e5b7c0d1b846e118e129c6f76ee57470920202b03362f9@ec2-107-20-239-47.compute-1.amazonaws.com:5432/dcqj6ar089mkj2'

# Set up connection to the database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

title = 'the'
year = '1998'
author_id = 1
isbn = '1632168146'
user_id = 11
book = db.execute("SELECT books.title, books.isbn, authors.name, "
                       "books.pub_date, books.id "
                       "FROM books "
                       "INNER JOIN authors ON books.author_id=authors.id "
                       "WHERE books.isbn = :isbn",
                       {'isbn': f"{isbn}"}).fetchall()

print(book)




