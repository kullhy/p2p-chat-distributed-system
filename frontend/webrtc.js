class P2PConnection {
    constructor(peerId, remotePeerId, signalingClient, onMessage, onStatusChange) {
        this.peerId = peerId;
        this.remotePeerId = remotePeerId;
        this.signaling = signalingClient;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange;
        this.iceQueue = [];

        this.pc = new RTCPeerConnection({
            iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });

        // Handle candidates found by this browser
        this.pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.signaling.send('signal', { candidate: event.candidate }, this.remotePeerId, this.peerId);
            }
        };

        // Handle incoming DataChannel (for the 'Answerer')
        this.pc.ondatachannel = (event) => {
            console.log("DataChannel received from remote");
            this.setupDataChannel(event.channel);
        };
    }

    setupDataChannel(channel) {
        this.dc = channel;
        this.dc.onopen = () => {
            console.log("P2P DataChannel Open");
            this.onStatusChange('connected');
        };
        this.dc.onclose = () => this.onStatusChange('disconnected');
        this.dc.onmessage = (e) => this.onMessage(JSON.parse(e.data));
    }

    async createOffer() {
        // Create DataChannel (for the 'Offerer')
        const channel = this.pc.createDataChannel("chat", { negotiated: false });
        this.setupDataChannel(channel);

        const offer = await this.pc.createOffer();
        await this.pc.setLocalDescription(offer);
        this.signaling.send('signal', { sdp: offer }, this.remotePeerId, this.peerId);
    }

    async handleSignal(data) {
        if (data.sdp) {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
            if (data.sdp.type === 'offer') {
                const answer = await this.pc.createAnswer();
                await this.pc.setLocalDescription(answer);
                this.signaling.send('signal', { sdp: answer }, this.remotePeerId, this.peerId);
            }
            // Add any candidates that arrived before the SDP was set
            while (this.iceQueue.length > 0) {
                const candidate = this.iceQueue.shift();
                await this.pc.addIceCandidate(candidate).catch(e => console.error(e));
            }
        } else if (data.candidate) {
            const candidate = new RTCIceCandidate(data.candidate);
            if (this.pc.remoteDescription) {
                await this.pc.addIceCandidate(candidate).catch(e => console.error(e));
            } else {
                this.iceQueue.push(candidate);
            }
        }
    }

    send(msg) {
        if (this.dc && this.dc.readyState === 'open') {
            this.dc.send(JSON.stringify(msg));
        }
    }
}