from .views import matching_alert_jobs


def alert_badge(request):
    if not request.user.is_authenticated:
        return {'alert_match_count': 0}

    return {'alert_match_count': len(matching_alert_jobs(request.user))}
