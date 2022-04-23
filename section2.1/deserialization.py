from marshmallow import Schema, fields, INCLUDE, EXCLUDE


class BookSchema(Schema):
    title = fields.Str(required=True)
    author = fields.Str(required=True)
    description = fields.Str()


class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author


incoming_book_data = {
    "title": "Clean Code",
    "author": "Bob Martin"
}

book_schema = BookSchema(unknown=INCLUDE)
book = book_schema.load(incoming_book_data)
book_obj = Book(**book)

print(book_obj.title)