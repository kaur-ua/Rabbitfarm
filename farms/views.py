from django.shortcuts import render, redirect
from .forms import FarmForm
from django.contrib.auth.decorators import login_required
from .models import Farm


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

@login_required
def farm_page(request):
    farm = Farm.objects.get(owner=request.user)
    return render(request, "farms/farm_page.html", {"farm": farm})