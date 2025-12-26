// --- Configuration ---
// Generate a unique namespace to avoid collisions with others using this demo code on the internet
const APP_NAMESPACE = 'nexus-p2p-v3-';
const LOBBY_ID = 'nexus-p2p-lobby-master-node-v3';
const PEER_CONFIG = {
    host: '0.peerjs.com',
    port: 443,
    path: '/',
    secure: true,
    debug: 1
};

// --- State ---
let myPeerId = null;
let peer = null;
let isLobbyHost = false;

// Connections
let lobbyConnection = null; // Client -> Host
let connections = {}; // Host -> Clients OR Client -> Client (Private)
let knownUsers = []; // [{id, status}]

let activeChatId = 'GLOBAL_CHAT';
let chatHistory = { 'GLOBAL_CHAT': [] };
let heartbeatInterval = null;

// --- DOM Elements ---
const myIdEl = document.getElementById('my-peer-id');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const peerListEl = document.getElementById('peer-list');
const msgInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const messagesBox = document.getElementById('messages-container');
const currentPeerName = document.getElementById('current-peer-name');
const chatStatus = document.getElementById('chat-status');
const toast = document.getElementById('toast');

// --- Initialization ---
async function init() {
    // 1. Attempt to grab the HOST ID
    try {
        console.log("Attempting to become Host...");
        peer = new Peer(LOBBY_ID, PEER_CONFIG);

        peer.on('open', (id) => {
            console.log("SUCCESS: I am the HOST");
            isLobbyHost = true;
            setupMyIdentity(id, "HOST NODE (Server)");
            updateKnownUsers([{ id: id, status: 'online' }]);
            startHostHeartbeat();
        });

        peer.on('error', (err) => {
            // If ID is taken, we are a Client
            if (err.type === 'unavailable-id') {
                console.log("Host occupied. Joining as Client...");
                initAsClient();
            } else {
                console.error("Peer Error:", err);
                if (err.type === 'peer-unavailable') {
                    // Could happen if trying to connect to disconnected Host
                    showToast("Host unreachable. Retrying...");
                }
            }
        });

        setupPeerEvents(peer);

    } catch (e) {
        initAsClient();
    }
}

function initAsClient() {
    const randomId = APP_NAMESPACE + Math.floor(Math.random() * 100000);
    peer = new Peer(randomId, PEER_CONFIG);

    peer.on('open', (id) => {
        setupMyIdentity(id, "Client Node");
        connectToLobby();
    });

    setupPeerEvents(peer);
}

function setupMyIdentity(id, type) {
    myPeerId = id;
    myIdEl.textContent = id;
    statusDot.className = 'status-indicator online';
    statusText.textContent = type;
    msgInput.disabled = false;
    sendBtn.disabled = false;

    // Explicit window close handling
    window.addEventListener('beforeunload', () => {
        if (lobbyConnection && lobbyConnection.open) {
            lobbyConnection.send({ type: 'LEAVE', sender: myPeerId });
        }
        peer.destroy();
    });
}

function setupPeerEvents(p) {
    p.on('connection', (conn) => {
        handleIncomingConnection(conn);
    });
}

function startHostHeartbeat() {
    if (heartbeatInterval) clearInterval(heartbeatInterval);
    heartbeatInterval = setInterval(() => {
        if (!isLobbyHost) return;

        // Broadcast User List regularly ensures eventual consistency
        broadcastToAll({ type: 'USER_LIST_UPDATE', users: knownUsers });

        // Clean dead connections
        Object.keys(connections).forEach(peerId => {
            const conn = connections[peerId];
            if (!conn.open) {
                console.log("Found dead connection:", peerId);
                removeUser(peerId);
            }
        });
    }, 3000); // Every 3 seconds
}

// --- CLIENT LOGIC ---
function connectToLobby() {
    if (lobbyConnection) lobbyConnection.close();

    statusText.textContent = "Connecting to Host...";
    lobbyConnection = peer.connect(LOBBY_ID, {
        reliable: true
    });

    lobbyConnection.on('open', () => {
        console.log("Connected to Host");
        statusText.textContent = "Online • Global Linked";
        statusDot.className = 'status-indicator online';

        lobbyConnection.send({ type: 'LOGIN', sender: myPeerId });
    });

    lobbyConnection.on('data', (data) => handleData(lobbyConnection, data));

    lobbyConnection.on('close', () => {
        statusText.textContent = "Disconnected from Host";
        statusDot.className = 'status-indicator';
        showToast("Host Disconnected. Please refresh.");
        updateKnownUsers([]); // Clear list as we are isolated
    });

    lobbyConnection.on('error', (err) => {
        console.error("Lobby Conn Error:", err);
    });
}

// --- HOST LOGIC ---
function handleIncomingConnection(conn) {
    conn.on('open', () => {
        if (isLobbyHost) {
            console.log("Host: Client connected", conn.peer);
            connections[conn.peer] = conn;

            // Add user (avoid duplicates)
            if (!knownUsers.find(u => u.id === conn.peer)) {
                const newList = [...knownUsers, { id: conn.peer, status: 'online' }];
                updateKnownUsers(newList);
                // Broadcast IMMEDIATELY
                broadcastToAll({ type: 'USER_LIST_UPDATE', users: newList });
            } else {
                // Just send him the current list
                conn.send({ type: 'USER_LIST_UPDATE', users: knownUsers });
            }
        } else {
            console.log("Private connection established with", conn.peer);
            connections[conn.peer] = conn;
        }
    });

    conn.on('data', (data) => handleData(conn, data));

    conn.on('close', () => {
        handleDisconnect(conn.peer);
    });

    conn.on('error', () => {
        handleDisconnect(conn.peer);
    });
}

function handleDisconnect(peerId) {
    console.log("Disconnect detected:", peerId);
    if (connections[peerId]) delete connections[peerId];

    if (isLobbyHost) {
        removeUser(peerId);
    }
}

function removeUser(peerId) {
    const exists = knownUsers.find(u => u.id === peerId);
    if (exists) {
        const newList = knownUsers.filter(u => u.id !== peerId);
        updateKnownUsers(newList);
        broadcastToAll({ type: 'USER_LIST_UPDATE', users: newList });

        // Notify System
        storeAndRenderMessage('GLOBAL_CHAT', 'System', `${peerId.slice(-5)} left the chat.`, 'system', 'global');
    }
}

// --- SHARED DATA HANDLER ---
function handleData(conn, data) {
    // console.log("Data in:", data);

    switch (data.type) {
        case 'LOGIN':
            // Logic handled in open, but good for heartbeat
            break;

        case 'LEAVE':
            handleDisconnect(data.sender);
            break;

        case 'USER_LIST_UPDATE':
            updateKnownUsers(data.users);
            break;

        case 'GLOBAL_CHAT':
            if (isLobbyHost) {
                // Broadcast to everyone else
                broadcastToAll(data, data.sender);
            }
            storeAndRenderMessage('GLOBAL_CHAT', data.sender, data.content, 'received', 'global');
            break;

        case 'PRIVATE_CHAT':
            storeAndRenderMessage(data.sender, data.sender, data.content, 'received', 'private');
            break;
    }
}

// --- UTILS ---
function updateKnownUsers(newList) {
    knownUsers = newList;
    // Debounce render?
    renderPeerList();
}

function broadcastToAll(payload, excludeId = null) {
    Object.values(connections).forEach(conn => {
        if (conn.open && conn.peer !== excludeId) {
            try {
                conn.send(payload);
            } catch (e) {
                console.error("Broadcast failed to", conn.peer);
            }
        }
    });
}

function sendPrivate(targetId, payload) {
    // Check existing
    if (connections[targetId] && connections[targetId].open) {
        connections[targetId].send(payload);
        return;
    }

    // Create new
    const newConn = peer.connect(targetId);
    newConn.on('open', () => {
        connections[targetId] = newConn;
        newConn.send(payload);
        newConn.on('data', d => handleData(newConn, d));
    });
}

// --- UI ---
function renderPeerList() {
    peerListEl.innerHTML = '';

    // Global Item
    const globalLi = document.createElement('li');
    globalLi.className = `peer-item ${activeChatId === 'GLOBAL_CHAT' ? 'active' : ''}`;
    globalLi.innerHTML = `
        <div class="peer-avatar globe"><ion-icon name="earth-outline"></ion-icon></div>
        <div class="peer-info">
            <h4>Global Network</h4>
            <span>${knownUsers.length} Online</span>
        </div>`;
    globalLi.onclick = () => switchChat('GLOBAL_CHAT');
    peerListEl.appendChild(globalLi);

    // Divider
    const div = document.createElement('div');
    div.className = 'list-divider';
    div.innerText = 'Online Users';
    peerListEl.appendChild(div);

    // Users
    knownUsers.forEach(user => {
        if (user.id === myPeerId) return;
        if (user.id === LOBBY_ID && isLobbyHost) return;

        const li = document.createElement('li');
        li.className = `peer-item ${activeChatId === user.id ? 'active' : ''}`;

        let displayName = user.id === LOBBY_ID ? "HOST SERVER" : user.id.replace(APP_NAMESPACE, 'User-');

        li.innerHTML = `
            <div class="peer-avatar">${displayName.substring(0, 2)}</div>
            <div class="peer-info">
                <h4>${displayName}</h4>
                <div class="status-badge online"></div>
            </div>`;
        li.onclick = () => switchChat(user.id);
        peerListEl.appendChild(li);
    });
}

function switchChat(id) {
    activeChatId = id;
    renderPeerList();
    renderMessages(id);

    if (id === 'GLOBAL_CHAT') {
        currentPeerName.innerText = "Global Network";
        chatStatus.innerText = "Broadcast Channel";
        msgInput.placeholder = "Message everyone...";
    } else {
        let displayName = id === LOBBY_ID ? "HOST SERVER" : id.replace(APP_NAMESPACE, 'User-');
        currentPeerName.innerText = displayName;
        chatStatus.innerText = "Private Channel";
        msgInput.placeholder = `Message ${displayName}...`;
    }
}

function storeAndRenderMessage(chatContext, senderId, content, direction, scope) {
    if (!chatHistory[chatContext]) chatHistory[chatContext] = [];

    let displayName = senderId === myPeerId ? "Me" : senderId.replace(APP_NAMESPACE, 'User-');
    if (senderId === LOBBY_ID) displayName = "HOST";

    const msg = {
        sender: displayName,
        content: content,
        timestamp: Date.now(),
        direction: direction, // 'sent', 'received', 'system'
        scope: scope
    };

    chatHistory[chatContext].push(msg);
    if (activeChatId === chatContext) {
        appendMessage(msg);
    }
}

function renderMessages(chatId) {
    messagesBox.innerHTML = '';
    const output = chatHistory[chatId] || [];

    if (output.length === 0) {
        messagesBox.innerHTML = `<div class="welcome-hero"><h2>Start the conversation</h2></div>`;
        return;
    }

    output.forEach(appendMessage);
}

function appendMessage(msg) {
    const div = document.createElement('div');

    if (msg.direction === 'system') {
        div.className = 'message system';
        div.innerHTML = `<small style="color:var(--text-dim); text-align:center; display:block; margin: 10px 0;">${msg.content}</small>`;
    } else {
        div.className = `message ${msg.direction}`;
        let nameHtml = '';
        if (msg.scope === 'global' && msg.direction === 'received') {
            nameHtml = `<div class="msg-sender">${msg.sender}</div>`;
        }
        div.innerHTML = `
            ${nameHtml}
            ${msg.content}
            <span class="meta">${new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        `;
    }
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

// --- Send ---
function sendMessage() {
    const text = msgInput.value.trim();
    if (!text) return;

    if (activeChatId === 'GLOBAL_CHAT') {
        const payload = { type: 'GLOBAL_CHAT', sender: myPeerId, content: text };

        // If Host: Broadcast to all
        if (isLobbyHost) {
            broadcastToAll(payload);
        } else if (lobbyConnection && lobbyConnection.open) {
            // If Client: Send to Host
            lobbyConnection.send(payload);
        } else {
            showToast("Network Unavailable");
            return;
        }

        storeAndRenderMessage('GLOBAL_CHAT', myPeerId, text, 'sent', 'global');
    } else {
        // Private
        sendPrivate(activeChatId, { type: 'PRIVATE_CHAT', sender: myPeerId, content: text });
        storeAndRenderMessage(activeChatId, myPeerId, text, 'sent', 'private');
    }
    msgInput.value = '';
}

// Handlers
sendBtn.onclick = sendMessage;
msgInput.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); }

function showToast(m) {
    toast.innerText = m;
    toast.className = 'toast';
    setTimeout(() => toast.className = 'toast hidden', 3000);
}

function copyId() {
    navigator.clipboard.writeText(myPeerId);
    showToast("ID Copied!");
}

// Start
init();
