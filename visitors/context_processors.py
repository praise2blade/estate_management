from estate_management.settings import APP_VERSION

def app_version(request):
    return {
        'APP_VERSION': APP_VERSION
    }
