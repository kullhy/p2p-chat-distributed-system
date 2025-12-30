import os


class Config:
    PROJECT_NAME = "Hybrid P2P Chat"
    VERSION = "1.0.0"
    HOST = "0.0.0.0"
    PORT = 8000
    # In a production environment, you would add TURN server credentials here
    STUN_SERVERS = ["stun:stun.l.google.com:19302"]


settings = Config()
