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
            bubble.innerHTML = `<p></p><small>${message.time}${message.seen && message.mine ? ' - Seen' : ''}</small>`;
            bubble.querySelector('p').textContent = message.body || 'Attachment';

            if (message.image) {
                const image = document.createElement('img');
                image.src = message.image;
                image.alt = 'Chat image';
                bubble.insertBefore(image, bubble.querySelector('small'));
            }
            if (message.voice_note) {
                const audio = document.createElement('audio');
                audio.controls = true;
                audio.src = message.voice_note;
                bubble.insertBefore(audio, bubble.querySelector('small'));
            }
            if (message.attachment) {
                const link = document.createElement('a');
                link.href = message.attachment;
                link.textContent = 'Download file';
                bubble.insertBefore(link, bubble.querySelector('small'));
            }

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

const attachmentPicker = document.querySelector('[data-attachment-picker]');
const attachmentToggle = document.querySelector('[data-attachment-toggle]');
const attachmentName = document.querySelector('[data-attachment-name]');
if (attachmentPicker && attachmentToggle) {
    attachmentToggle.addEventListener('click', () => {
        attachmentPicker.classList.toggle('open');
    });
    document.addEventListener('click', (event) => {
        if (!attachmentPicker.contains(event.target)) {
            attachmentPicker.classList.remove('open');
        }
    });
    attachmentPicker.querySelectorAll('input[type="file"]').forEach((input) => {
        input.addEventListener('change', () => {
            const names = [...attachmentPicker.querySelectorAll('input[type="file"]')]
                .filter((fileInput) => fileInput.files.length)
                .map((fileInput) => fileInput.files[0].name);
            if (attachmentName) attachmentName.textContent = names.join(', ');
            attachmentPicker.classList.remove('open');
        });
    });
}
