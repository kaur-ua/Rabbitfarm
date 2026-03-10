from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rabbits.models import Rabbit
from events.models import Event
from datetime import date, timedelta

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
    return render(request, "rabbits/rabbit_list.html", {"rabbits": rabbits})

@login_required

def home(request):

    rabbits = Rabbit.objects.all()

    rabbits_count = rabbits.count()
    males = rabbits.filter(sex="M").count()
    females = rabbits.filter(sex="F").count()


    # 🚦 Логіка світлофора
    today = date.today()

    red_events = Event.objects.filter(date__lte=today + timedelta(days=2))

    yellow_events = Event.objects.filter(
        date__gt=today + timedelta(days=2),
        date__lte=today + timedelta(days=5)
    )

    if red_events.exists():
        traffic_light = "red"
    elif yellow_events.exists():
        traffic_light = "yellow"
    else:
        traffic_light = "green"


    context = {
        "rabbits_count": rabbits_count,
        "males": males,
        "females": females,
        "traffic_light": traffic_light,
    }

    return render(request, "home.html", context)

    