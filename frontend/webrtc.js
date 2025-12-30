class P2PConnection {
    constructor(peerId, remotePeerId, signalingClient, onMessage, onStatusChange) {
        this.peerId = peerId;
        this.remotePeerId = remotePeerId;
        this.signaling = signalingClient;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange;
        this.iceQueue = [];
        this.isStarted = false;

        this.pc = new RTCPeerConnection({
            iceServers: [
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" }
            ]
        });

        this.pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.signaling.send('signal', { candidate: event.candidate }, this.remotePeerId, this.peerId);
            }
        };

        this.pc.oniceconnectionstatechange = () => {
            const state = this.pc.iceConnectionState;
            console.log(`[RTC] ICE State (${this.remotePeerId}): ${state}`);
            this.onStatusChange(state);
        };

        this.pc.onconnectionstatechange = () => {
            console.log(`[RTC] Connection State (${this.remotePeerId}): ${this.pc.connectionState}`);
            this.onStatusChange(this.pc.connectionState);
        };

        this.pc.ondatachannel = (event) => {
            this.setupDataChannel(event.channel);
        };
    }

    setupDataChannel(channel) {
        this.dc = channel;
        this.dc.onopen = () => {
            console.log(`[RTC] DataChannel Open with ${this.remotePeerId}`);
            this.onStatusChange('connected');
        };
        this.dc.onclose = () => {
            console.log(`[RTC] DataChannel Closed with ${this.remotePeerId}`);
            this.onStatusChange('disconnected');
        };
        this.dc.onmessage = (e) => this.onMessage(JSON.parse(e.data));
    }

    async createOffer() {
        if (this.isStarted) return;
        this.isStarted = true;

        const channel = this.pc.createDataChannel("chat");
        this.setupDataChannel(channel);

        try {
            const offer = await this.pc.createOffer();
            await this.pc.setLocalDescription(offer);
            this.signaling.send('signal', { sdp: offer }, this.remotePeerId, this.peerId);
        } catch (e) {
            console.error("[RTC] Offer Error:", e);
        }
    }

    async handleSignal(data) {
        try {
            if (data.sdp) {
                await this.pc.setRemoteDescription(new RTCSessionDescription(data.sdp));

                if (data.sdp.type === 'offer') {
                    const answer = await this.pc.createAnswer();
                    await this.pc.setLocalDescription(answer);
                    this.signaling.send('signal', { sdp: answer }, this.remotePeerId, this.peerId);
                }

                while (this.iceQueue.length > 0) {
                    await this.pc.addIceCandidate(this.iceQueue.shift());
                }
            } else if (data.candidate) {
                const candidate = new RTCIceCandidate(data.candidate);
                if (this.pc.remoteDescription) {
                    await this.pc.addIceCandidate(candidate);
                } else {
                    this.iceQueue.push(candidate);
                }
            }
        } catch (e) {
            console.error(`[RTC] Signal Handling Error:`, e);
        }
    }

    send(msg) {
        if (this.dc && this.dc.readyState === 'open') {
            this.dc.send(JSON.stringify(msg));
            return true;
        }
        return false;
    }

    close() {
        if (this.dc) {
            this.dc.onclose = null;
            this.dc.close();
        }
        if (this.pc) {
            this.pc.onicecandidate = null;
            this.pc.onconnectionstatechange = null;
            this.pc.close();
        }
    }
}