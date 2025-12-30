class P2PConnection {
    constructor(peerId, remotePeerId, signalingClient, onMessage, onStatusChange) {
        this.peerId = peerId;
        this.remotePeerId = remotePeerId;
        this.signaling = signalingClient;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange;
        this.iceQueue = [];
        this.isStarted = false;

        console.log(`[RTC-LIFE] CREATE: New instance for peer ${remotePeerId}`);

        this.pc = new RTCPeerConnection({
            iceServers: [
                {urls: "stun:stun.l.google.com:19302"},
                {urls: "stun:stun1.l.google.com:19302"}
            ]
        });

        // 1. Log chi tiết Candidate nội bộ sinh ra
        this.pc.onicecandidate = (event) => {
            if (event.candidate) {
                const cand = event.candidate.candidate;
                const type = event.candidate.type; // host, srflx, relay
                // Kiểm tra xem có phải mDNS (.local) hay IP thật
                console.log(`[RTC-DETAIL] GATHERED LOCAL | Type: ${type} | Val: ${cand}`);

                this.signaling.send('signal', {candidate: event.candidate}, this.remotePeerId, this.peerId);
            }
        };

        // 2. Bắt lỗi ICE Error cụ thể (thường bị bỏ qua)
        this.pc.onicecandidateerror = (event) => {
            console.error(`[RTC-ERR] ICE Error code: ${event.errorCode} | Text: ${event.errorText} | URL: ${event.url}`);
        };

        this.pc.oniceconnectionstatechange = () => {
            const state = this.pc.iceConnectionState;
            console.log(`[RTC-ICE-STATE] ${this.remotePeerId}: ${state}`);

            // 3. Khi connection failed, Dump Stats để xem nó chết ở cặp IP nào
            if (state === 'failed' || state === 'disconnected') {
                this.dumpStats();
            }

            this.onStatusChange(state);
        };

        this.pc.onconnectionstatechange = () => {
            console.log(`[RTC-CONN-STATE] ${this.remotePeerId}: ${this.pc.connectionState}`);
            this.onStatusChange(this.pc.connectionState);
        };

        this.pc.ondatachannel = (event) => {
            console.log(`[RTC-DATA] INBOUND: DataChannel from ${this.remotePeerId}`);
            this.setupDataChannel(event.channel);
        };
    }

    // Hàm Phân tích tử thi (Post-mortem analysis)
    async dumpStats() {
        console.log("--- START ICE STATS DUMP ---");
        try {
            const stats = await this.pc.getStats();
            stats.forEach(report => {
                if (report.type === 'candidate-pair' && report.state === 'failed') {
                    console.log(`[RTC-FAIL-PAIR] Local: ${report.localCandidateId} <-> Remote: ${report.remoteCandidateId}`);
                    console.log(`[RTC-FAIL-REASON] BytesSent: ${report.bytesSent}, BytesReceived: ${report.bytesReceived}`);
                }
            });
        } catch (e) {
            console.error("Could not dump stats", e);
        }
        console.log("--- END ICE STATS DUMP ---");
    }

    setupDataChannel(channel) {
        this.dc = channel;
        this.dc.onopen = () => {
            console.log(`[RTC-DATA] OPEN: P2P Tunnel ready.`);
            this.onStatusChange('connected');
        };
        this.dc.onclose = () => {
            console.log(`[RTC-DATA] CLOSE.`);
            this.onStatusChange('disconnected');
        };
        this.dc.onmessage = (e) => {
            this.onMessage(JSON.parse(e.data));
        };
    }

    async createOffer() {
        if (this.isStarted) return;
        this.isStarted = true;

        console.log(`[RTC-ROLE] CALLER: Creating Offer for ${this.remotePeerId}`);
        const channel = this.pc.createDataChannel("chat");
        this.setupDataChannel(channel);

        try {
            const offer = await this.pc.createOffer();
            await this.pc.setLocalDescription(offer);
            this.signaling.send('signal', {sdp: offer}, this.remotePeerId, this.peerId);
        } catch (e) {
            console.error("[RTC-ERR] Create Offer Failed:", e);
        }
    }

    async handleSignal(data) {
        try {
            if (data.sdp) {
                console.log(`[RTC-SDP] REMOTE: Received ${data.sdp.type}`);
                await this.pc.setRemoteDescription(new RTCSessionDescription(data.sdp));

                if (data.sdp.type === 'offer') {
                    console.log(`[RTC-ROLE] CALLEE: Creating Answer`);
                    const answer = await this.pc.createAnswer();
                    await this.pc.setLocalDescription(answer);
                    this.signaling.send('signal', {sdp: answer}, this.remotePeerId, this.peerId);
                }

                while (this.iceQueue.length > 0) {
                    const candidate = this.iceQueue.shift();
                    console.log(`[RTC-ICE] FLUSH: Adding queued candidate`);
                    await this.pc.addIceCandidate(candidate);
                }
            } else if (data.candidate) {
                const candidate = new RTCIceCandidate(data.candidate);

                // 4. Log chi tiết Candidate nhận được từ Peer kia
                console.log(`[RTC-DETAIL] RECEIVED REMOTE | Val: ${candidate.candidate}`);

                if (this.pc.remoteDescription) {
                    await this.pc.addIceCandidate(candidate);
                } else {
                    console.log(`[RTC-ICE] QUEUE: Buffering candidate`);
                    this.iceQueue.push(candidate);
                }
            }
        } catch (e) {
            console.error(`[RTC-ERR] Signal Error:`, e);
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
        console.log(`[RTC-LIFE] DESTROY: Closing connection`);
        if (this.dc) this.dc.close();
        if (this.pc) this.pc.close();
    }
}