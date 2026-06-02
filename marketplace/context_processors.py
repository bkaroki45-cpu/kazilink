from .views import matching_alert_jobs, unread_chat_message_count


def alert_badge(request):
    if not request.user.is_authenticated:
        return {'alert_match_count': 0, 'unread_chat_count': 0}

    return {
        'alert_match_count': len(matching_alert_jobs(request.user)),
        'unread_chat_count': unread_chat_message_count(request.user),
    }
