import datetime
from django.contrib.auth import logout
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self,request):
        if not request.user.is_authenticated:
            return
        if 'last_activity' in request.session:
            last_activity_str = request.session.get('last_activity')
            last_activity = datetime.datetime.fromisoformat(last_activity_str.replace('Z','+00:00')) if last_activity_str else None 
            if last_activity:
                time_diff = (timezone.now()-last_activity).total_seconds()
                if time_diff>settings.SESSION_COOKIE_AGE:
                    logout(request)
                    return
        request.session['last_activity'] = timezone.now().isoformat().replace('+00:00','Z')