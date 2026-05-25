const pane = document.querySelector('[data-chat-pane]');
if (pane) {
    pane.scrollTop = pane.scrollHeight;
    setInterval(async () => {
        const response = await fetch(pane.dataset.chatUrl);
        const data = await response.json();
        const known = new Set([...pane.querySelectorAll('[data-message-id]')].map((item) => item.dataset.messageId));
        data.messages.forEach((message) => {
            if (known.has(String(message.id))) return;
            const bubble = document.createElement('article');
            bubble.className = `bubble ${message.mine ? 'mine' : ''}`;
            bubble.dataset.messageId = message.id;
            bubble.innerHTML = `<p></p><small>${message.time}${message.seen && message.mine ? ' · Seen' : ''}</small>`;
            bubble.querySelector('p').textContent = message.body || 'Attachment';
            pane.appendChild(bubble);
            pane.scrollTop = pane.scrollHeight;
        });
    }, 3500);
}

const messageInput = document.querySelector('.message-box input[name="body"]');
if (messageInput) {
    messageInput.addEventListener('input', () => {
        document.querySelector('.online-dot')?.classList.add('typing');
    });
}
