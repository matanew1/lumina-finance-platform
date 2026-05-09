from sqlalchemy import select

from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    '''
    Repository for client-related database operations.
    '''
    def list_client_ids(self) -> list[str]:
        '''
        Lists all unique client IDs.
        - Returns:
            - list[str]: A list of unique client IDs.
        '''

        # Query the database for distinct client IDs from the Transaction table, ordered alphabetically.
        statement = select(Transaction.client_id).distinct().order_by(Transaction.client_id)

        # Execute the query and return the results as a list of strings.
        return list(self.db.scalars(statement).all())
