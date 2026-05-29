const pane = document.querySelector('[data-chat-pane]');
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

function statusMarkup(message) {
    if (!message.mine) return '';
    if (message.deleted) return '<span class="message-status unsent" title="Message unsent">x</span>';
    if (message.seen) return '<span class="message-status read" title="Read">&check;&check;</span>';
    return '<span class="message-status delivered" title="Delivered">&check;&check;</span>';
}

function messageActions(message) {
    return `
        <div class="message-actions">
            <button type="button" data-message-menu aria-label="Message actions">...</button>
            <div class="message-menu">
                <form method="post" action="${message.delete_for_me_url}" data-delete-message>
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <button type="submit">Delete for me</button>
                </form>
                ${message.mine ? `
                    <form method="post" action="${message.delete_for_everyone_url}" data-delete-message>
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                        <button type="submit">Delete for everyone</button>
                    </form>
                ` : ''}
            </div>
        </div>
    `;
}

function renderMessage(message) {
    const row = document.createElement('div');
    row.className = `message-row ${message.mine ? 'mine' : ''}`;
    row.dataset.messageRow = '';

    if (!message.mine) {
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        if (message.sender_avatar) {
            avatar.innerHTML = `<img src="${message.sender_avatar}" alt="${message.sender}">`;
        } else {
            avatar.textContent = (message.sender || '?').charAt(0).toUpperCase();
        }
        row.appendChild(avatar);
    }

    const bubble = document.createElement('article');
    bubble.className = `bubble ${message.mine ? 'mine' : ''}`;
    bubble.dataset.messageId = message.id;
    bubble.innerHTML = messageActions(message);

    if (message.deleted) {
        bubble.insertAdjacentHTML('beforeend', '<p class="unsent-message">Message unsent</p>');
    } else {
        if (message.body) {
            const text = document.createElement('p');
            text.textContent = message.body;
            bubble.appendChild(text);
        }
        if (message.image) {
            const image = document.createElement('img');
            image.src = message.image;
            image.alt = 'Chat image';
            bubble.appendChild(image);
        }
        if (message.voice_note) {
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.src = message.voice_note;
            bubble.appendChild(audio);
        }
        if (message.attachment) {
            const link = document.createElement('a');
            link.className = 'file-link';
            link.href = message.attachment;
            link.textContent = 'Download file';
            bubble.appendChild(link);
        }
    }

    bubble.insertAdjacentHTML('beforeend', `<small>${message.time} ${statusMarkup(message)}</small>`);
    row.appendChild(bubble);
    return row;
}

function syncMessages(messages) {
    const indicator = pane.querySelector('[data-typing-indicator]');
    const known = new Set([...pane.querySelectorAll('[data-message-id]')].map((item) => item.dataset.messageId));

    messages.forEach((message) => {
        const existing = pane.querySelector(`[data-message-id="${message.id}"]`);
        if (existing) {
            existing.querySelector('small').innerHTML = `${message.time} ${statusMarkup(message)}`;
            if (message.deleted && !existing.querySelector('.unsent-message')) {
                existing.innerHTML = `${messageActions(message)}<p class="unsent-message">Message unsent</p><small>${message.time} ${statusMarkup(message)}</small>`;
            }
            return;
        }
        if (known.has(String(message.id))) return;
        pane.insertBefore(renderMessage(message), indicator);
        pane.scrollTop = pane.scrollHeight;
    });
}

async function pollMessages() {
    const response = await fetch(pane.dataset.chatUrl);
    if (!response.ok) return;
    const data = await response.json();
    syncMessages(data.messages || []);

    const status = document.querySelector('[data-typing-status]');
    const indicator = pane.querySelector('[data-typing-indicator]');
    if (status) status.textContent = data.typing ? 'Typing...' : 'Online now';
    if (indicator) indicator.hidden = !data.typing;
}

if (pane) {
    pane.scrollTop = pane.scrollHeight;
    setInterval(pollMessages, 2500);
}

document.addEventListener('click', (event) => {
    const menuButton = event.target.closest('[data-message-menu]');
    document.querySelectorAll('.message-actions.open').forEach((item) => {
        if (!item.contains(event.target)) item.classList.remove('open');
    });
    if (menuButton) {
        menuButton.closest('.message-actions')?.classList.toggle('open');
    }
});

document.addEventListener('submit', async (event) => {
    const form = event.target.closest('[data-delete-message]');
    if (!form) return;
    event.preventDefault();
    const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!response.ok) {
        form.submit();
        return;
    }
    const data = await response.json();
    if (!data.deleted) {
        form.closest('[data-message-row]')?.remove();
        return;
    }
    await pollMessages();
});

const messageInput = document.querySelector('.message-box textarea[name="body"], .message-box input[name="body"]');
let typingTimer;
async function sendTyping(isTyping) {
    if (!pane?.dataset.typingUrl) return;
    const formData = new FormData();
    formData.append('typing', isTyping ? '1' : '0');
    await fetch(pane.dataset.typingUrl, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken },
    });
}

if (messageInput) {
    messageInput.addEventListener('input', () => {
        sendTyping(Boolean(messageInput.value.trim())).catch(() => {});
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => sendTyping(false).catch(() => {}), 1800);
    });
    messageInput.closest('form')?.addEventListener('submit', () => {
        sendTyping(false).catch(() => {});
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
