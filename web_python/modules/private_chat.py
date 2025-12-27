from datetime import datetime

class PrivateChat:
    def __init__(self, base_ptr):
        self.base = base_ptr
        self.on_message_received = None

    def send_message(self, target_id, content):
        timestamp = int(datetime.now().timestamp() * 1000)
        payload = {
            'type': 'PRIVATE_CHAT',
            'sender': self.base.my_id,
            'content': content,
            'timestamp': timestamp
        }
        
        # Check connection. If not there, try connect (async issue in sync send?)
        # BaseP2P.connect returns conn object but it might be not 'open' immediately.
        # But if we rely on UI list, we are likely connected (if Host propagated).
        # Wait, if we are Client A and want to chat Client B, we might not have direct conn yet.
        # `base.connect` handles initializing it.
        # But `base.send` checks `conn.open`.
        # If new connection, `send` will fail.
        # Robust way: Queue message?
        # For this refactor: Attempt connect. 
        
        if target_id not in self.base.connections or not self.base.connections[target_id].open:
            self.base.connect(target_id)
            # Cannot send immediately. 
            # In a real app we queue. 
            # Here let's assume if user clicks on list, we might have connected or connect on click.
            # But just in case, we return a "pending" or just send and hope.
            # Actually, we can return success=False if not sent.
        
        sent = self.base.send(target_id, payload)
        
        return {
            'sender': self.base.my_id,
            'content': content,
            'direction': 'sent', 
            'scope': 'private',
            'timestamp': timestamp,
            'sent_status': sent
        }

    def on_private_data(self, sender_id, data):
        if data['type'] == 'PRIVATE_CHAT':
            if self.on_message_received:
                self.on_message_received({
                    'sender': sender_id,
                    'content': data['content'],
                    'direction': 'received',
                    'scope': 'private',
                    'timestamp': data.get('timestamp')
                })
