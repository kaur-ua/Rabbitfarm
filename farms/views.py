from django.shortcuts import render, redirect
from .forms import FarmForm


def create_farm(request):
    if request.method == "POST":
        form = FarmForm(request.POST)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.owner = request.user
            farm.save()
            return redirect("home")
    else:
        form = FarmForm()

    return render(request, "farms/create_farm.html", {"form": form})