class Paper():
    def __init__(self, id, submitter=None, authors=None, title=None, comments=None,journalref=None,doi=None,abstract=None,categories=None,versions=None) -> None:
        self.id=id
        self.submitter=submitter
        self.authors=authors
        self.title=title
        self.comments=comments
        self.journalref=journalref
        self.doi=doi
        self.abstract=abstract
        self.categories=categories
        self.versions=versions
        
    def to_JSON(self):
        return{
            'id': self.id,
            'submitter': self.submitter,
            'authors': self.authors,
            'title': self.title,
            'comments': self.comments,
            'journalref': self.journalref,
            'doi': self.doi,
            'abstract': self.abstract,
            'categories': self.categories,
            'versions': self.versions
        }
        