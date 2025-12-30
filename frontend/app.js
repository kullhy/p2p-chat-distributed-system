const peerId = Math.random().toString(36).substr(2, 9);
let username = "";
let currentChatPeer = null;
let activeP2PConnections = {};

const messageStore = {
    global: [],
    private: {}
};

const globalSocket = new SocketClient('ws://localhost:8000/ws/global', peerId, handleGlobalMessage);
const signalingSocket = new SocketClient('ws://localhost:8000/ws/signaling', peerId, handleSignalingMessage);

// UI Cache
const messagesCont = document.getElementById('messages-container');
const chatTitle = document.getElementById('chat-title');
const p2pStatus = document.getElementById('p2p-status');

document.getElementById('join-btn').onclick = async () => {
    username = document.getElementById('username-input').value || "Guest";
    await globalSocket.connect();
    await signalingSocket.connect();
    globalSocket.send('register', { username }, null, peerId);
    document.getElementById('setup-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    document.getElementById('display-id').innerText = peerId;
};

function handleGlobalMessage(data) {
    if (data.type === 'peer_list') {
        renderPeerList(data.payload.peers);
    } else if (data.type === 'global_msg') {
        messageStore.global.push(data);
        if (!currentChatPeer) renderMessage(data);
    }
}

async function handleSignalingMessage(data) {
    const fromId = data.from;
    if (!activeP2PConnections[fromId]) {
        initiateP2P(fromId, false);
    }
    await activeP2PConnections[fromId].handleSignal(data.payload);
}

function renderPeerList(peers) {
    const peerListEl = document.getElementById('peer-list');
    peerListEl.innerHTML = `<li class="peer-item ${!currentChatPeer ? 'active' : ''}" onclick="switchChat(null)">Global Hub</li>`;
    peers.forEach(p => {
        if (p.peerId === peerId) return;
        const li = document.createElement('li');
        li.className = `peer-item ${currentChatPeer === p.peerId ? 'active' : ''}`;
        li.innerHTML = `<span>${p.username}</span><br><small>${p.peerId.substr(0,5)}</small>`;
        li.onclick = () => switchChat(p);
        peerListEl.appendChild(li);
    });
}

function switchChat(peer) {
    currentChatPeer = peer ? peer.peerId : null;
    chatTitle.innerText = peer ? `Private: ${peer.username}` : "Global Chat";

    messagesCont.innerHTML = "";
    if (!currentChatPeer) {
        messageStore.global.forEach(msg => renderMessage(msg));
    } else {
        const history = messageStore.private[currentChatPeer] || [];
        history.forEach(msg => renderMessage(msg));
        if (!activeP2PConnections[currentChatPeer]) initiateP2P(currentChatPeer, true);
    }
    updateP2PStatus();
}

function initiateP2P(remoteId, isCaller) {
    if (activeP2PConnections[remoteId]) return;

    const conn = new P2PConnection(peerId, remoteId, signalingSocket,
        (msg) => {
            const msgObj = { ...msg, from: remoteId };
            if (!messageStore.private[remoteId]) messageStore.private[remoteId] = [];
            messageStore.private[remoteId].push(msgObj);
            if (currentChatPeer === remoteId) renderMessage(msgObj);
        },
        () => { updateP2PStatus() }
    );
    activeP2PConnections[remoteId] = conn;
    if (isCaller) conn.createOffer();
}

function updateP2PStatus() {
    if (!currentChatPeer) { p2pStatus.innerText = ""; return; }
    const conn = activeP2PConnections[currentChatPeer];
    const isReady = conn?.dc?.readyState === 'open';
    p2pStatus.innerText = isReady ? "● P2P Connected" : "○ Negotiating...";
    p2pStatus.className = isReady ? "status-online" : "status-offline";
}

function renderMessage(data) {
    // Check ownership
    const isSelf = data.from === peerId;
    const div = document.createElement('div');
    div.className = `msg ${isSelf ? 'self' : 'other'}`;

    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const senderName = isSelf ? "You" : (data.payload.sender || "Peer");

    div.innerHTML = `
        <div class="msg-info">${senderName} • ${time}</div>
        <div class="msg-text">${data.payload.text}</div>
    `;

    messagesCont.appendChild(div);
    messagesCont.scrollTop = messagesCont.scrollHeight;
}

document.getElementById('message-form').onsubmit = (e) => {
    e.preventDefault();
    const input = document.getElementById('msg-input');
    const text = input.value.trim();
    if (!text) return;

    const msgObj = {
        type: currentChatPeer ? 'p2p_msg' : 'global_msg',
        from: peerId,
        payload: { text, sender: username }
    };

    if (currentChatPeer) {
        activeP2PConnections[currentChatPeer].send(msgObj);
        if (!messageStore.private[currentChatPeer]) messageStore.private[currentChatPeer] = [];
        messageStore.private[currentChatPeer].push(msgObj);
        renderMessage(msgObj);
    } else {
        globalSocket.send('global_msg', msgObj.payload, null, peerId);
    }
    input.value = "";
};