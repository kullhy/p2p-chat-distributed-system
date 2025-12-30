class SocketClient {
    constructor(url, peerId, onMessage) {
        this.url = `${url}/${peerId}`;
        this.onMessage = onMessage;
        this.socket = null;
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.socket = new WebSocket(this.url);
            this.socket.onopen = () => resolve();
            this.socket.onerror = (err) => reject(err);
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            };
        });
    }

    send(type, payload, to = null, fromId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type, from: fromId, to, payload }));
        }
    }
}