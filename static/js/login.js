// Login form handler
(function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('error-message');
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // Clear previous error
        errorMessage.textContent = '';
        
        // Prepare form data
        const formData = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
        
        // Send login request
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            credentials: 'same-origin',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Login failed');
            }
        })
        .then(data => {
            if (data.status === 'ok') {
                // Store user info
                sessionStorage.setItem('username', username);
                sessionStorage.setItem('auth', 'true');
                
                // Register as peer
                registerPeer(username).then(() => {
                    // Redirect to chat
                    window.location.href = '/index.html';
                });
            } else {
                errorMessage.textContent = 'Login failed. Please try again.';
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            errorMessage.textContent = 'Login failed. Please check your credentials.';
        });
    });
    
    function registerPeer(username) {
        const peerData = {
            id: 'web_' + Date.now(),
            ip: '127.0.0.1',
            port: 0,  // Web client doesn't have a listening port
            username: username
        };
        
        sessionStorage.setItem('peerId', peerData.id);
        
        return fetch('/submit-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(peerData)
        }).catch(error => {
            console.error('Error registering peer:', error);
        });
    }
})();
