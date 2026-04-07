from django.shortcuts import render, redirect
from datetime import timedelta
from .forms import EventForm
from farms.models import Farm
from rabbits.models import Group
from django.contrib.auth.decorators import login_required

@login_required
def add_event(request):
    farm = request.user.farms.first()
    if request.method == "POST":
        form = EventForm(request.POST)
        form.fields["rabbit"].queryset = farm.rabbits.all()
        if form.is_valid():
            event = form.save(commit=False)
            

            if event.event_type == "mating":
                event.next_action = "Очікуваний окрол"
                event.next_action_date = event.date + timedelta(days=28)

            elif event.event_type == "kindling":
                event.next_action = "Відсадка"
                event.next_action_date = event.date + timedelta(days=60)

            elif event.event_type == "vaccination":
                event.next_action = "Наступна вакцинація"
                event.next_action_date = event.date + timedelta(days=180)

            elif event.event_type == "weaning":
                event.next_action = "Групу створено"
            
            event.save()

            if event.event_type == "weaning":
                Group.objects.get_or_create(
                   name=f"{event.rabbit.name}_{event.date}",
                   farm=farm,
                   defaults={
                       "description": f"Створено після відсадки від {event.rabbit.name}"
                }
                )

            return redirect("home")

    else:
        form = EventForm()
        form.fields["rabbit"].queryset = farm.rabbits.all()

    
    return render(request, "events/add_event.html", {
        "form": form,
        "farm": farm
    })