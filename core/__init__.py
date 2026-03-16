# core/__init__.py
from .crypto import CryptoManager
from .database import Database
from .email_sender import EmailSender
from .cloud_storage import CloudStorage
from .logger import setup_logger
from .platforms.steam import SteamPlatform
from .platforms.psn import PSNPlatform
from .platforms.xbox import XboxPlatform
from .platforms.epic import EpicPlatform
from .platforms.battlenet import BattleNetPlatform
from .platforms.ubisoft import UbisoftPlatform