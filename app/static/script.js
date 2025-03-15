// Function to add a message to the chat container
function addMessage(message, isUser) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to the bottom of the chat container
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to show loading indicator
function showLoading() {
    const chatContainer = document.getElementById('chat-container');
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('loading');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.textContent = 'Bot is typing...';
    chatContainer.appendChild(loadingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to hide loading indicator
function hideLoading() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Function to send a message to the server
async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    
    if (message === '') return;
    
    // Add user message to the chat
    addMessage(message, true);
    
    // Clear input field
    userInput.value = '';
    
    // Show loading indicator
    showLoading();
    
    try {
        // Send the message to the server
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message }),
        });
        
        const data = await response.json();
        
        // Hide loading indicator
        hideLoading();
        
        // Add bot response to the chat
        addMessage(data.answer, false);
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        addMessage('Sorry, there was an error processing your request.', false);
    }
}

// Listen for Enter key press
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});