import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv

DATABASE_URL = 'postgres://rwkradveffikre:28272880b7cc5fe661e5b7c0d1b846e118e129c6f76ee57470920202b03362f9@ec2-107-20-239-47.compute-1.amazonaws.com:5432/dcqj6ar089mkj2'

# Set up connection to the database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))


# Open file using with
with open('books.csv', "r") as file:

    # Create a dict reader and loop over file contents
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        isbn = row['isbn']
        title = row['title']
        author = row['author']
        year = row['year']

        author_id = db.execute("SELECT id FROM authors WHERE name = :name",
                        {'name': author}).fetchall()
        if not author_id:
            db.execute("INSERT INTO authors (name) VALUES (:name)", {'name': author})
            db.commit()
            print(f"Inserted author {author} into database")
        else:
            print(f"Already in database with id: {author_id}")
        author_id = db.execute("SELECT id FROM authors WHERE name = "
                               ":name", {'name': author}).fetchall()[0][0]
        print(f"Inserted author: {author} into database with id: {author_id}")
        db.execute("INSERT INTO books (title, pub_date, author_id, isbn) "
                   "VALUES (:title, :pub_date, :author_id, :isbn)",
                   {
                       'title': title,
                       'pub_date': year,
                       'author_id': author_id,
                       'isbn': isbn})
        db.commit()
        print(f"Inserted book title {title} into database")
print("Done with the database insertions")
