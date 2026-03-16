from .base import PlatformBase

class XboxPlatform(PlatformBase):
    def __init__(self, database, crypto):
        super().__init__(database, crypto)
        self.name = "Xbox"
    
    def authenticate(self, credentials):
        # Заглушка
        return False
    
    def fetch_games(self, account_id=None):
        return []