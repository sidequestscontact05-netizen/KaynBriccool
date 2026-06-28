document.addEventListener('DOMContentLoaded', function() {
    var chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    var conversationId = chatMessages.dataset.conversationId;
    var pollUrl = chatMessages.dataset.pollUrl || ('/' + conversationId + '/poll/');
    var lastId = '';

    function messageExists(id) {
        return chatMessages.querySelector('[data-message-id="' + id + '"]') !== null;
    }

    function pollMessages() {
        if (window._chatLastId && window._chatLastId !== lastId) {
            lastId = window._chatLastId;
        }
        var url = pollUrl + (lastId ? '?last_id=' + lastId : '');
        fetch(url)
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.is_closed) {
                    var form = document.querySelector('.chat-input');
                    if (form) {
                        form.remove();
                        var banner = document.createElement('div');
                        banner.className = 'chat-closed-banner';
                        banner.innerHTML = '<p><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> Cette conversation est clôturée car la mission est terminée.</p>';
                        form.parentNode.appendChild(banner);
                    }
                    var badge = document.createElement('span');
                    badge.className = 'closed-badge';
                    badge.textContent = 'Conversation clôturée';
                    document.querySelector('.chat-header').appendChild(badge);
                    return;
                }
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(function(msg) {
                        if (messageExists(msg.id)) return;
                        var wrapper = document.createElement('div');
                        wrapper.innerHTML = msg.rendered_html;
                        var bubble = wrapper.firstElementChild;
                        if (bubble) {
                            chatMessages.appendChild(bubble);
                            lastId = msg.id;
                        }
                    });
                    if (typeof initAudioPlayers === 'function') {
                        initAudioPlayers(chatMessages);
                    }
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            })
            .catch(function(err) { console.error('Poll error:', err); });
    }

    setInterval(pollMessages, 2000);

    chatMessages.scrollTop = chatMessages.scrollHeight;
});