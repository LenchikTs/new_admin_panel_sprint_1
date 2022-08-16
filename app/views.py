from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def sample_view(request):
    html = '<body><h1>Django sample_view</h1><br><p>Отладка sample_view</p></body>'
    return HttpResponse(html)
