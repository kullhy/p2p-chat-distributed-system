// --- Configuration ---
const PEER_CONFIG = {
    host: '0.peerjs.com',
    port: 443,
    path: '/',
    secure: true,
    debug: 2
};

// --- State ---
let myPeerId = null;
let peer = null;
let connections = {}; // { peerId: DataConnection }
let activeChatId = null;
let chatHistory = {}; // { peerId: [{type, content, time}] }

// --- DOM Elements ---
const myIdEl = document.getElementById('my-peer-id');
const statusDot = document.querySelector('.status-dot');
const statusText = document.getElementById('status-text');
const targetIdInput = document.getElementById('target-id-input');
const connectBtn = document.getElementById('connect-btn');
const peerListEl = document.getElementById('peer-list');
const msgInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const messagesBox = document.getElementById('messages-container');
const chatStatus = document.getElementById('chat-status');
const currentPeerName = document.getElementById('current-peer-name');

// --- Initialization ---
function init() {
    // Generate a random ID for user
    const randomId = "User-" + Math.floor(Math.random() * 100000);
    peer = new Peer(randomId, PEER_CONFIG);

    peer.on('open', (id) => {
        myPeerId = id;
        myIdEl.textContent = id;
        statusDot.classList.add('online');
        statusText.textContent = "Online";
        console.log('My Peer ID is: ' + id);
    });

    peer.on('connection', (conn) => {
        setupConnection(conn);
        alert(`Incoming connection from ${conn.peer}`);
    });

    peer.on('error', (err) => {
        console.error(err);
        alert("P2P Error: " + err.type);
    });
}

// --- Connections ---
connectBtn.addEventListener('click', () => {
    const targetId = targetIdInput.value.trim();
    if (!targetId || targetId === myPeerId) return;
    
    // Connect to peer
    const conn = peer.connect(targetId);
    setupConnection(conn);
});

function setupConnection(conn) {
    conn.on('open', () => {
        connections[conn.peer] = conn;
        addPeerToList(conn.peer);
        // If we initiated, switch to chat
        if (targetIdInput.value === conn.peer) {
            switchChat(conn.peer);
            targetIdInput.value = "";
        }
    });

    conn.on('data', (data) => {
        handleIncomingMessage(conn.peer, data);
    });

    conn.on('close', () => {
        alert(`${conn.peer} disconnected`);
        delete connections[conn.peer];
        removePeerFromList(conn.peer);
        if (activeChatId === conn.peer) {
            disableChat();
        }
    });
}

// --- UI Logic ---
function addPeerToList(id) {
    const existing = document.querySelector(`[data-id="${id}"]`);
    if (existing) return;

    const li = document.createElement('li');
    li.className = 'peer-item';
    li.dataset.id = id;
    li.innerHTML = `
        <div class="peer-avatar">${id.substring(0, 2)}</div>
        <div class="peer-info">
            <h4>${id}</h4>
            <p>Connected</p>
        </div>
    `;
    li.onclick = () => switchChat(id);
    peerListEl.appendChild(li);
}

function removePeerFromList(id) {
    const el = document.querySelector(`[data-id="${id}"]`);
    if (el) el.remove();
}

function switchChat(id) {
    activeChatId = id;
    
    // Update active UI
    document.querySelectorAll('.peer-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-id="${id}"]`)?.classList.add('active');
    
    currentPeerName.textContent = id;
    chatStatus.textContent = "Secure P2P Connection via WebRTC";
    
    // Enable inputs
    msgInput.disabled = false;
    sendBtn.disabled = false;
    msgInput.focus();

    renderMessages(id);
}

function disableChat() {
    activeChatId = null;
    currentPeerName.textContent = "No active chat";
    chatStatus.textContent = "Wait for connection...";
    messagesBox.innerHTML = '<div class="welcome-screen"><h1>Decentralized Chat</h1><p>Peer Disconnected.</p></div>';
    msgInput.disabled = true;
    sendBtn.disabled = true;
}

// --- Messaging ---
function handleIncomingMessage(senderId, data) {
    // data = { content: string, timestamp: number }
    if (!chatHistory[senderId]) chatHistory[senderId] = [];
    
    chatHistory[senderId].push({
        type: 'received',
        content: data.content,
        timestamp: data.timestamp
    });

    if (activeChatId === senderId) {
        appendMessageToUI('received', data.content, data.timestamp);
    } else {
        // Notification logic could go here
        const el = document.querySelector(`[data-id="${senderId}"] p`);
        if (el) el.textContent = "New message!";
    }
}

function sendMessage() {
    const content = msgInput.value.trim();
    if (!content || !activeChatId) return;

    const conn = connections[activeChatId];
    if (conn && conn.open) {
        const payload = {
            content: content,
            timestamp: Date.now()
        };
        conn.send(payload);

        // Store internally
        if (!chatHistory[activeChatId]) chatHistory[activeChatId] = [];
        chatHistory[activeChatId].push({
            type: 'sent',
            content: content,
            timestamp: Date.now()
        });
        
        appendMessageToUI('sent', content, Date.now());
        msgInput.value = "";
    } else {
        alert("Connection lost!");
    }
}

sendBtn.addEventListener('click', sendMessage);
msgInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function renderMessages(peerId) {
    messagesBox.innerHTML = '';
    const msgs = chatHistory[peerId] || [];
    msgs.forEach(msg => {
        appendMessageToUI(msg.type, msg.content, msg.timestamp);
    });
    scrollToBottom();
}

function appendMessageToUI(type, content, timestamp) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    const timeStr = new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    div.innerHTML = `
        ${content}
        <span class="meta">${timeStr}</span>
    `;
    messagesBox.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

// --- Utils ---
function copyId() {
    navigator.clipboard.writeText(myPeerId).then(() => {
        alert("Copied ID to clipboard!");
    });
}

// Start
init();
