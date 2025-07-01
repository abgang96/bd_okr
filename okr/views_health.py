from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "Health Check Status: OK"}, status=200)
