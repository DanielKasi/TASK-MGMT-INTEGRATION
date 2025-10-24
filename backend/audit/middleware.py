import threading

_thread_locals = threading.local()

def get_current_institution():
    return getattr(_thread_locals, 'institution', None)

def set_current_institution(inst):
    _thread_locals.institution = inst


class InstitutionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inst = None
        resolver_match = getattr(request, "resolver_match", None)

        # Only proceed if resolver_match exists
        if resolver_match and hasattr(resolver_match, "kwargs"):
            inst_slug = resolver_match.kwargs.get("inst_slug")
            if inst_slug:
                from institution.models import Institution
                inst = Institution.objects.filter(slug=inst_slug).first()

        # Fallback: get from user profile
        if not inst and request.user.is_authenticated:
            from users.models import Profile
            try:
                profile = Profile.objects.get(user=request.user)
                inst = profile.institution
            except Profile.DoesNotExist:
                pass

        set_current_institution(inst)
        return self.get_response(request)