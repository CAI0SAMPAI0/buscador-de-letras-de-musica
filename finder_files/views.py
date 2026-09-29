from django.http import JsonResponse

def index_view(request):
    return JsonResponse({
        "app": "Buscador de Músicas",
        "status": "online",
        "api_docs": "/api/v1/docs"
    })
