from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rabbits.models import Rabbit
from events.models import Event
from datetime import date, timedelta
from farms.models import Farm
from django.shortcuts import render, get_object_or_404

def rabbit_detail(request, pk):
    rabbit = get_object_or_404(Rabbit, pk=pk)
    events = rabbit.events.all().order_by("-date")
    return render(
        request,
        "rabbits/rabbit_detail.html",
        {"rabbit": rabbit, "events": events}
    )


def rabbit_list(request):
    rabbits = Rabbit.objects.all()
    farm = Farm.objects.first()

    return render(request, "rabbits/rabbit_list.html", {
        "rabbits": rabbits,
        "farm": farm,
    })
@login_required

def home(request):

    rabbits = Rabbit.objects.all()
    farm = Farm.objects.first()

    rabbits_count = rabbits.count()
    males = rabbits.filter(sex="M").count()
    females = rabbits.filter(sex="F").count()

    red_light = True
    yellow_light = False
    green_light = False

    context = {
        "farm": farm,
        "rabbits_count": rabbits_count,
        "males": males,
        "females": females,
        "red_light": red_light,
        "yellow_light": yellow_light,
        "green_light": green_light,
    }
    return render(request, "home.html", context)

    