"""
Protocol Definitions

Message Types:
- register: Initial handshake to set username
- peer_list: Broadcast of all online users
- global_msg: Standard chat message for everyone
- signal: WebRTC signaling data (offer, answer, ice)
- user_joined/user_left: Presence updates
"""

class MessageTypes:
    REGISTER = "register"
    PEER_LIST = "peer_list"
    GLOBAL_MSG = "global_msg"
    SIGNAL = "signal"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"