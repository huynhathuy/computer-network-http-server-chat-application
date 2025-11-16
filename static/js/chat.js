// Chat application JavaScript
(function() {
    let currentUser = null;
    let currentChannel = 'general';
    let lastMessageCount = 0;
    let channels = [];
    let refreshInterval = null;
    
    // Helper function
    function $(id) {
        return document.getElementById(id);
    }
    
    // Initialize
    function init() {
        // Check authentication
        currentUser = sessionStorage.getItem('username');
        if (!currentUser) {
            window.location.href = '/login.html';
            return;
        }
        
        // Display username
        $('currentUsername').textContent = currentUser;
        
        // Set up event listeners
        $('sendBtn').addEventListener('click', sendMessage);
        $('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        $('logoutBtn').addEventListener('click', logout);
        $('createChannelBtn').addEventListener('click', createChannel);
        
        // Load initial data
        loadChannels();
        loadMessages();
        
        // Start polling for updates
        refreshInterval = setInterval(function() {
            loadChannels();
            loadMessages();
        }, 5000);
    }
    
    // Load channels and users
    function loadChannels() {
        Promise.all([
            fetch('/channels', { credentials: 'same-origin' }).then(r => r.json()),
            fetch('/get-list', { credentials: 'same-origin' }).then(r => r.json())
        ])
        .then(([channelsData, usersData]) => {
            channels = channelsData.channels || [];
            renderChannels(channels);
            renderUsers(usersData.peers || []);
        })
        .catch(error => {
            console.error('Error loading channels:', error);
        });
    }
    
    // Render channels list
    function renderChannels(chatChannels) {
        const channelsList = $('channelsList');
        channelsList.innerHTML = '';
        
        chatChannels.forEach(function(channel) {
            const div = document.createElement('div');
            div.className = 'channel-item' + (channel === currentChannel ? ' active' : '');
            div.textContent = '# ' + channel;
            div.onclick = function() {
                selectChannel(channel);
            };
            channelsList.appendChild(div);
        });
    }
    
    // Render users list
    function renderUsers(users) {
        const usersList = $('usersList');
        usersList.innerHTML = '';
        
        // Filter out current user
        const otherUsers = users.filter(function(user) {
            return user.username !== currentUser;
        });
        
        otherUsers.forEach(function(user) {
            const div = document.createElement('div');
            div.className = 'user-item';
            div.textContent = '• ' + user.username;
            usersList.appendChild(div);
        });
        
        if (otherUsers.length === 0) {
            const div = document.createElement('div');
            div.style.color = '#95a5a6';
            div.style.fontSize = '12px';
            div.style.padding = '10px';
            div.textContent = 'No other users online';
            usersList.appendChild(div);
        }
    }
    
    // Select channel
    function selectChannel(channel) {
        currentChannel = channel;
        lastMessageCount = 0;
        $('messagesHeader').textContent = '#' + channel;
        
        // Clear messages immediately when switching channels
        const container = $('messagesContainer');
        container.innerHTML = '<div style="text-align:center;color:#95a5a6;padding:20px;">Loading...</div>';
        
        // Update active state
        const items = document.querySelectorAll('.channel-item');
        items.forEach(function(item) {
            item.classList.remove('active');
            if (item.textContent === '# ' + channel) {
                item.classList.add('active');
            }
        });
        
        loadMessages();
    }
    
    // Load messages for current channel
    function loadMessages() {
        fetch('/messages?channel=' + encodeURIComponent(currentChannel), {
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            const messages = data.messages || [];
            
            // Always render messages to ensure correct channel content is shown
            // (fixes issue where switching channels might show cached messages)
            lastMessageCount = messages.length;
            renderMessages(messages);
        })
        .catch(error => {
            console.error('Error loading messages:', error);
        });
    }
    
    // Render messages
    function renderMessages(messages) {
        const container = $('messagesContainer');
        container.innerHTML = '';
        
        if (messages.length === 0) {
            const div = document.createElement('div');
            div.style.textAlign = 'center';
            div.style.color = '#95a5a6';
            div.style.padding = '20px';
            div.textContent = 'No messages yet. Start the conversation!';
            container.appendChild(div);
            return;
        }
        
        messages.forEach(function(msg) {
            const div = document.createElement('div');
            div.className = 'message';
            
            const sender = document.createElement('div');
            sender.className = 'message-sender';
            sender.textContent = msg.sender;
            
            const text = document.createElement('div');
            text.className = 'message-text';
            text.textContent = msg.text;
            
            const time = document.createElement('div');
            time.className = 'message-time';
            const date = new Date(msg.timestamp * 1000);
            time.textContent = date.toLocaleTimeString();
            
            div.appendChild(sender);
            div.appendChild(text);
            div.appendChild(time);
            container.appendChild(div);
        });
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }
    
    // Send message
    function sendMessage() {
        const input = $('messageInput');
        const text = input.value.trim();
        
        if (!text) return;
        
        const message = {
            channel: currentChannel,
            sender: currentUser,
            text: text,
            timestamp: Date.now() / 1000
        };
        
        fetch('/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(message)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'sent') {
                input.value = '';
                loadMessages();
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
        });
    }
    
    // Create new channel
    function createChannel() {
        const channelName = prompt('Enter new channel name:');
        if (!channelName) return;
        
        fetch('/create-channel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({ channel: channelName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'created') {
                loadChannels();
                selectChannel(channelName);
            } else {
                alert('Error: ' + (data.error || 'Could not create channel'));
            }
        })
        .catch(error => {
            console.error('Error creating channel:', error);
        });
    }
    
    // Logout
    function logout() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        sessionStorage.clear();
        document.cookie = 'auth=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        window.location.href = '/login.html';
    }
    
    // Start the app
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
