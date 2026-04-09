def notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False)
        return {
            'unread_notifications_count': unread.count(),
            'recent_notifications': request.user.notifications.all()[:5] # Последние 5
        }
    return {}