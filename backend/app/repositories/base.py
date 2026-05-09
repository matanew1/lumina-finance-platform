from sqlalchemy.orm import Session


class BaseRepository:
    '''
    Base class for all repositories.
    '''
    def __init__(self, db: Session) -> None:
        '''
        Initializes the repository with a database session.
        - Parameters:
            - db: Session - The database session.
        '''
        self.db = db
