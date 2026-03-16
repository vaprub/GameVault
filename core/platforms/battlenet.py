from .base import PlatformBase

class BattleNetPlatform(PlatformBase):
    def __init__(self, database, crypto):
        super().__init__(database, crypto)
        self.name = "BattleNet"
    
    def authenticate(self, credentials):
        # Заглушка
        return False
    
    def fetch_games(self, account_id=None):
        return []