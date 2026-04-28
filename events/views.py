from datetime import timedelta
from .forms import EventForm
from farms.models import Farm
from rabbits.models import Group, Rabbit
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django import forms



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
                event.next_action = "Розділення за статтю"
                event.next_action_date = event.date + timedelta(days=30)

            event.save()
           
                           
            if event.event_type == "kindling":
                numbers = farm.rabbits.values_list("inventory_number", flat=True)

                numeric_numbers = [
                    int(num) for num in numbers if num and num.isdigit()
                ]

                next_number = max(numeric_numbers, default=0) + 1
                
                born_alive = event.born_alive or 0

                mother_short_name = event.rabbit.name.split()[-1]
                
                for i in range(1, born_alive + 1):
                    Rabbit.objects.create(
                    farm=farm,
                    mother=event.rabbit,
                    name=f"G{mother_short_name}-{i:02}",
                    inventory_number=f"{next_number + i - 1:04}",
                    sex="U",
                    breed=event.rabbit.breed,
                    birth_date=event.date,
                    cage=event.rabbit.cage,
                    status="ACTIVE"
                )

            if event.event_type == "weaning":
                new_cage = form.cleaned_data["cage"]

                if not new_cage:
                    form.add_error("cage", "Для відсадки потрібно вказати клітку")
                    form.fields["rabbit"].queryset = farm.rabbits.all()

                    return render(request, "events/add_event.html", {
                        "form": form,
                        "farm": farm
                    })

                group, created = Group.objects.get_or_create(
                    name=f"{event.rabbit.name}_{event.date}",
                    farm=farm,
                    defaults={
                        "description": f"Створено після відсадки від {event.rabbit.name}",
                        "cage_number": new_cage,
                    }
                )

                babies = farm.rabbits.filter(
                    mother=event.rabbit,
                    group__isnull=True
                )

                for baby in babies:
                    baby.group = group
                    baby.cage = new_cage
                    baby.save()
                                
            return redirect("home")

    else:
        form = EventForm()
        form.fields["rabbit"].queryset = farm.rabbits.all()

    
    return render(request, "events/add_event.html", {
        "form": form,
        "farm": farm
    })

@login_required
def edit_event(request, rabbit_id):
    farm = request.user.farms.first()

    rabbit = get_object_or_404(farm.rabbits, id=rabbit_id)
    event = rabbit.events.order_by("-date").first()

    if not event:
        return redirect("home")

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        form.fields["rabbit"].queryset = farm.rabbits.all()

        form.fields["rabbit"].disabled = True
        form.fields["event_type"].disabled = True

        if event.event_type != "kindling":
            form.fields.pop("born_alive", None)
            form.fields.pop("born_dead", None)

        if form.is_valid():
            edited_event = form.save(commit=False)

            if edited_event.event_type == "mating":
                edited_event.next_action = "Очікуваний окрол"
                edited_event.next_action_date = edited_event.date + timedelta(days=28)

            elif edited_event.event_type == "kindling":
                edited_event.next_action = "Відсадка"
                edited_event.next_action_date = edited_event.date + timedelta(days=60)

            elif edited_event.event_type == "vaccination":
                edited_event.next_action = "Наступна вакцинація"
                edited_event.next_action_date = edited_event.date + timedelta(days=180)

            elif edited_event.event_type == "weaning":
                edited_event.next_action = "Розділення за статтю"
                edited_event.next_action_date = edited_event.date + timedelta(days=30)

                new_cage = form.cleaned_data["cage"]

                if new_cage:
                    babies = farm.rabbits.filter(
                    mother=rabbit,
                    group__isnull=False
                )

                    for baby in babies:
                        baby.cage = new_cage
                        baby.save()

                    group = Group.objects.filter(
                        farm=farm,
                        rabbits__mother=rabbit
                    ).first()

                    if group:
                        group.cage_number = new_cage
                        group.save()

            edited_event.save()

            return redirect("home")

    else:
        form = EventForm(instance=event)
        form.fields["rabbit"].queryset = farm.rabbits.all()

        form.fields["rabbit"].disabled = True
        form.fields["event_type"].disabled = True

        if event.event_type != "kindling":
            form.fields.pop("born_alive", None)
            form.fields.pop("born_dead", None)

    return render(request, "events/edit_event.html", {
        "form": form,
        "rabbit": rabbit,
        "event": event,
        "farm": farm
    })
@login_required
def create_group_event(request, group_id):
    farm = request.user.farms.first()
    group = get_object_or_404(Group, pk=group_id, farm=farm)

    if request.method == "POST":
        form = EventForm(request.POST)
        form.instance.group = group
        form.fields["rabbit"].widget = forms.HiddenInput()
        form.fields["group"].widget = forms.HiddenInput()

        if form.is_valid():
            event = form.save(commit=False)
            event.group = group
            event.rabbit = None

            if event.event_type == "weaning":
                event.next_action = "Розділення за статтю"
                event.next_action_date = event.date + timedelta(days=30)

            event.save()
            return redirect("group_list")

    else:
        form = EventForm()
        form.fields["rabbit"].widget = forms.HiddenInput()
        form.fields["group"].widget = forms.HiddenInput()
        

    return render(request, "events/add_event.html", {
        "form": form,
        "farm": farm
    })


    