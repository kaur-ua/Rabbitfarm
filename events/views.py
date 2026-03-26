from django.shortcuts import render, redirect
from .forms import EventForm
from farms.models import Farm


def add_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = EventForm()
        farm = request.user.farms.first()

    return render(request, "events/add_event.html", {
        "form": form,
        "farm": farm
    })