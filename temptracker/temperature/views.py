from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.


def monitor_status(request):
    return HttpResponse("Monitoring status is active.")
