from datetime import timedelta
from .forms import EventForm
from farms.models import Farm
from rabbits.models import Group, Rabbit
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from .models import Event
from django.db import transaction



@login_required
def add_event(request):
    farm = request.user.farms.first()

    if request.method == "POST":
        form = EventForm(request.POST)
        form.fields["rabbit"].queryset = farm.rabbits.all()

        if form.is_valid():
            event = form.save(commit=False)

            # 👉 перевірка для weaning
            if event.event_type == "weaning":
                new_cage = form.cleaned_data.get("cage")
                if not new_cage:
                    form.add_error("cage", "Для відсадки потрібно вказати клітку")
                    return render(request, "events/add_event.html", {
                        "form": form,
                        "farm": farm
                    })

            with transaction.atomic():

                # ✅ 1. завжди зберігаємо event
                event.save()

                # 🐣 ОКРОЛ
                if event.event_type == "kindling":
                    numbers = farm.rabbits.values_list("inventory_number", flat=True)

                    numeric_numbers = [
                        int(num) for num in numbers if num and num.isdigit()
                    ]

                    next_number = max(numeric_numbers, default=0) + 1
                    born_alive = event.born_alive or 0
                    mother = event.rabbit
                    mother_short_name = mother.name.split()[-1]

                    for i in range(1, born_alive + 1):
                        Rabbit.objects.create(
                            farm=farm,
                            mother=mother,
                            name=f"G{mother_short_name}-{i:02}",
                            inventory_number=f"{next_number + i - 1:04}",
                            sex="U",
                            breed=mother.breed,
                            birth_date=event.date,
                            cage=mother.cage,
                            status="ACTIVE"
                        )

                # 🏠 ВІДСАДКА
                if event.event_type == "weaning":
                    new_cage = form.cleaned_data.get("cage")
                    mother = event.rabbit

                    group, created = Group.objects.get_or_create(
                        name=f"{mother.name}_{event.date}",
                        farm=farm,
                        defaults={
                            "description": f"Створено після відсадки від {mother.name}",
                            "cage_number": new_cage,
                        }
                    )
                    if not created:
                        group.cage_number = new_cage
                        group.save()

                    # 👉 прив’язуємо event до group
                    event.group = group
                    event.rabbit = None
                    event.save()

                    babies = farm.rabbits.filter(
                        mother=mother,
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

@login_required
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.delete()
        return redirect("home")

    return render(request, "events/confirm_delete.html", {"event": event})

    