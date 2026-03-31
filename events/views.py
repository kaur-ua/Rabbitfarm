from django.shortcuts import render, redirect
from datetime import timedelta
from .forms import EventForm
from farms.models import Farm


def add_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)

            if event.event_type == "mating":
                event.next_action = "Очікуваний окрол"
                event.next_action_date = event.date + timedelta(days=28)

            elif event.event_type == "birth":
                event.next_action = "Відлучення"
                event.next_action_date = event.date + timedelta(days=60)

            elif event.event_type == "vaccination":
                event.next_action = "Наступна вакцинація"
                event.next_action_date = event.date + timedelta(days=180)

            event.save()
            return redirect("home")

    else:
        form = EventForm()

    farm = request.user.farms.first()

    return render(request, "events/add_event.html", {
        "form": form,
        "farm": farm
    })