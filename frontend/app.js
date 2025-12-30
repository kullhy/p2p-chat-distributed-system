const peerId = Math.random().toString(36).substr(2, 9);
let username = "";
let currentChatPeer = null;

// NETWORK LAYER STATE (Lives forever)
const activeP2PConnections = {};
const messageStore = { global: [], private: {} };
let lastPeers = [];

console.log("[UI-INIT] PeerID:", peerId);

const globalSocket = new SocketClient('ws://localhost:8000/ws/global', peerId,
    handleGlobalMessage,
    (isOnline) => {
        const statusEl = document.getElementById('connection-status');
        statusEl.innerText = isOnline ? "Global: Online" : "Global: Offline";
        statusEl.className = isOnline ? "status-online" : "status-offline";
    }
);

const signalingSocket = new SocketClient('ws://localhost:8000/ws/signaling', peerId, handleSignalingMessage);

document.getElementById('join-btn').onclick = async () => {
    username = document.getElementById('username-input').value.trim() || "User_" + peerId.substr(0,3);
    try {
        await globalSocket.connect();
        await signalingSocket.connect();
        globalSocket.send('register', { username }, null, peerId);
        document.getElementById('setup-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        document.getElementById('display-id').innerText = peerId;
    } catch (e) {
        console.error("Connection failed", e);
        alert("Could not connect to backend.");
    }
};

function handleGlobalMessage(data) {
    if (data.type === 'peer_list') {
        lastPeers = data.payload.peers;
        updatePeerListUI();
    } else if (data.type === 'global_msg') {
        console.log("[DATA-GLOBAL] Received message. UI context:", currentChatPeer ? "Private" : "Global");
        messageStore.global.push(data);
        if (!currentChatPeer) renderMessage(data);
    }
}

async function handleSignalingMessage(data) {
    const fromId = data.from;
    if (data.type === 'signal') {
        // FIX: If we have a dead connection for this peer, kill it first
        if (activeP2PConnections[fromId]) {
            const state = activeP2PConnections[fromId].pc.connectionState;
            if (state === 'failed' || state === 'closed') {
                console.log(`[RTC-SYNC] Found dead connection for ${fromId}. Cleaning up before accepting new signal.`);
                activeP2PConnections[fromId].close();
                delete activeP2PConnections[fromId];
            }
        }

        if (!activeP2PConnections[fromId]) {
            console.log(`[RTC-SYNC] REUSE: Creating new instance on signal receipt for ${fromId}`);
            initiateP2P(fromId, false);
        }
        await activeP2PConnections[fromId].handleSignal(data.payload);
    }
}

function updatePeerListUI() {
    const list = document.getElementById('peer-list');
    list.innerHTML = `<li class="peer-item ${!currentChatPeer ? 'active' : ''}" id="btn-global">Global Chat</li>`;
    document.getElementById('btn-global').onclick = () => switchChat(null);

    lastPeers.forEach(p => {
        if (p.peerId === peerId) return;
        const li = document.createElement('li');
        li.className = `peer-item ${currentChatPeer === p.peerId ? 'active' : ''}`;
        li.innerText = `${p.username} (${p.peerId.substr(0,4)})`;
        li.onclick = () => switchChat(p);
        list.appendChild(li);
    });
}

function switchChat(peer) {
    const targetId = peer ? peer.peerId : null;
    if (currentChatPeer === targetId) return;

    console.log(`[UI-SWITCH] ${currentChatPeer || 'Global'} -> ${targetId || 'Global'}`);
    currentChatPeer = targetId;

    updatePeerListUI();
    document.getElementById('chat-title').innerText = peer ? `Private Chat: ${peer.username}` : "Global Chat";

    const messagesCont = document.getElementById('messages-container');
    messagesCont.innerHTML = "";

    if (!currentChatPeer) {
        messageStore.global.forEach(msg => renderMessage(msg));
    } else {
        const history = messageStore.private[currentChatPeer] || [];
        history.forEach(msg => renderMessage(msg));

        // Ensure valid connection exists
        initiateP2P(currentChatPeer, true);
    }
    updateP2PStatusUI();
}

function initiateP2P(remoteId, isCaller) {
    // FIX: Zombie Killer Logic
    if (activeP2PConnections[remoteId]) {
        const conn = activeP2PConnections[remoteId];
        const state = conn.pc.connectionState;

        if (['failed', 'closed', 'disconnected'].includes(state)) {
            console.warn(`[RTC-LIFE] Connection to ${remoteId} is ${state}. Destroying and recreating.`);
            conn.close();
            delete activeP2PConnections[remoteId];
        } else {
            console.log(`[RTC-LIFE] REUSE: Existing healthy connection found for ${remoteId} (${state})`);
            return;
        }
    }

    const conn = new P2PConnection(peerId, remoteId, signalingSocket,
        (msg) => {
            const msgWithSender = { ...msg, from: remoteId };
            if (!messageStore.private[remoteId]) messageStore.private[remoteId] = [];
            messageStore.private[remoteId].push(msgWithSender);
            if (currentChatPeer === remoteId) renderMessage(msgWithSender);
        },
        () => updateP2PStatusUI()
    );

    activeP2PConnections[remoteId] = conn;
    if (isCaller) {
        // Small delay to ensure signaling readiness
        setTimeout(() => conn.createOffer(), 150);
    }
}

function updateP2PStatusUI() {
    const p2pStatus = document.getElementById('p2p-status');
    if (!currentChatPeer) { p2pStatus.innerText = ""; return; }

    const conn = activeP2PConnections[currentChatPeer];
    if (!conn) { p2pStatus.innerText = "○ Waiting..."; return; }

    const state = conn.pc.connectionState; // Use connectionState for better accuracy
    const isReady = conn.dc && conn.dc.readyState === 'open';

    if (isReady) {
        p2pStatus.innerText = "● P2P Connected";
        p2pStatus.style.color = "#43b581";
    } else if (state === 'failed' || state === 'closed') {
        p2pStatus.innerText = "× Connection Failed";
        p2pStatus.style.color = "#f04747";
    } else {
        p2pStatus.innerText = "○ Establishing P2P...";
        p2pStatus.style.color = "#faa61a";
    }
}

function renderMessage(data) {
    const messagesCont = document.getElementById('messages-container');
    const isSelf = data.from === peerId;
    const div = document.createElement('div');
    div.className = `msg ${isSelf ? 'self' : 'other'}`;

    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const sender = isSelf ? "You" : (data.payload.sender || "Peer");

    div.innerHTML = `<div class="msg-info">${sender} • ${time}</div><div>${data.payload.text}</div>`;
    messagesCont.appendChild(div);
    messagesCont.scrollTop = messagesCont.scrollHeight;
}

document.getElementById('message-form').onsubmit = (e) => {
    e.preventDefault();
    const input = document.getElementById('msg-input');
    const text = input.value.trim();
    if (!text) return;

    const msgObj = { from: peerId, payload: { text, sender: username } };

    if (currentChatPeer) {
        const conn = activeP2PConnections[currentChatPeer];
        // Ensure we don't try to send on a dead connection
        if (conn && conn.send(msgObj)) {
            if (!messageStore.private[currentChatPeer]) messageStore.private[currentChatPeer] = [];
            messageStore.private[currentChatPeer].push(msgObj);
            renderMessage(msgObj);
        } else {
            console.warn("[UI-SEND] P2P not open yet or failed.");
            alert("P2P connection is not ready. Try switching chats to retry.");
        }
    } else {
        globalSocket.send('global_msg', msgObj.payload, null, peerId);
    }
    input.value = "";
};