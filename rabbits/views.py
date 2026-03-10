from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from farms.utils import get_user_farm
from django.utils.timezone import now
from .models import Rabbit
from events.models import Event

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
    farm = get_user_farm(request.user)

    if not farm:
        return redirect("create_farm")

    rabbits = Rabbit.objects.filter(farm=farm)

    today = now().date()

    due_events = Event.objects.filter(
        rabbit__farm=farm,
        date__lte=today
    ).order_by("date")

    context = {
        "farm": farm,
        "rabbit_count": rabbits.count(),
        "female_count": rabbits.filter(sex="F").count(),
        "male_count": rabbits.filter(sex="M").count(),
        "due_events": due_events,
    }

    return render(request, "home.html", context)