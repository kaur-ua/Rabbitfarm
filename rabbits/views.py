from django.contrib.auth.decorators import login_required
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

    for rabbit in rabbits:
        rabbit.last_event = Event.objects.filter(
            rabbit=rabbit
        ).order_by("-date").first()

        days = (date.today() - rabbit.birth_date).days

        if days < 60:
            rabbit.age_display = f"{days // 7} тиж."
        elif days < 365:
            rabbit.age_display = f"{days // 30} міс."
        else:
            years = days // 365
            months = (days % 365) // 30
            rabbit.age_display = f"{years} р. {months} міс."

    return render(request, "rabbits/rabbit_list.html", {
        "rabbits": rabbits
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

