"""Screening API lib alchemy paginators module"""
from collections import Sequence
from math import ceil


class AlchemyPaginator(object):

    def __init__(self, query, per_page, offset=0, allow_empty_first_page=True):
        self.query = query
        self.per_page = per_page
        self.offset = offset
        self.allow_empty_first_page = allow_empty_first_page

        self.count = self.query.order_by(None).offset(self.offset).count()
        self.num_pages = int(ceil(self.count / float(self.per_page)))
        self.page_range = range(1, self.num_pages + 1)

    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise TypeError('That page number is not an integer')
        if number < 1:
            raise IndexError('That page number is less than 1')
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise IndexError('That page contains no results')
        return number

    def get_page(self, number):
        try:
            number = self.validate_number(number)
        except TypeError:
            number = 1
        except IndexError:
            number = self.num_pages
        return self.page(number)

    def page(self, number):
        number = self.validate_number(number)
        offset = (number - 1) * self.per_page + self.offset
        items = self.query.limit(self.per_page).offset(offset).all()
        return Page(items, number, self)


class Page(Sequence):

    def __init__(self, items, number, paginator):
        self.items = items
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        if not isinstance(self.items, list):
            self.items = list(self.items)
        return self.items[index]

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)
