class SocketClient {
    constructor(url, peerId, onMessage, onStatusChange) {
        this.url = `${url}/${peerId}`;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange; // Callback for UI updates
        this.socket = null;
    }

    connect() {
        return new Promise((resolve, reject) => {
            console.log(`[WS] Connecting to ${this.url}`);
            this.socket = new WebSocket(this.url);

            this.socket.onopen = () => {
                console.log(`[WS] Connected: ${this.url}`);
                if (this.onStatusChange) this.onStatusChange(true);
                resolve();
            };

            this.socket.onerror = (err) => {
                console.error(`[WS] Error: ${this.url}`, err);
                if (this.onStatusChange) this.onStatusChange(false);
                reject(err);
            };

            this.socket.onclose = () => {
                console.warn(`[WS] Closed: ${this.url}`);
                if (this.onStatusChange) this.onStatusChange(false);
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            };
        });
    }

    send(type, payload, to = null, fromId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const msg = JSON.stringify({type, from: fromId, to, payload});
            this.socket.send(msg);
        } else {
            console.error(`[WS] Cannot send: Socket not open (${type})`);
        }
    }
}