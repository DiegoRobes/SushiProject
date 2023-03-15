from django.shortcuts import render, redirect
from django.urls import reverse
import main.models as m


# Create your views here.
def home(request):
    all_dishes = None
    context = {'dishes': all_dishes}
    return render(request, "main/index.html", context=context)


def details(request, slug):
    selected = None  # m.Dish.objects.get(slug=slug)
    context = {'selected': selected}
    return render(request, "main/details.html", context=context)


def about(request):
    context = {}
    return render(request, "main/about.html", context=context)
