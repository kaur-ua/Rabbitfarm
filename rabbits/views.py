from django.contrib.auth.decorators import login_required
from rabbits.models import Rabbit
from events.models import Event
from datetime import date, timedelta
from farms.models import Farm
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import RabbitForm, GroupForm
from .models import Group

@login_required
def create_group(request):
    farm = request.user.farms.first()

    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.farm = farm
            group.save()
            return redirect("home")
    else:
        form = GroupForm()

    return render(request, "rabbits/create_group.html", {"form": form})

@login_required
def group_list(request):
    farm = request.user.farms.first()
    groups = Group.objects.filter(farm=farm)

    return render(request, 'rabbits/group_list.html', {
        'groups': groups,
        'farm': farm
    })

@login_required
def edit_group(request, pk):
    farm = request.user.farms.first()
    group = get_object_or_404(Group, pk=pk, farm=farm)

    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect("group_list")
    else:
        form = GroupForm(instance=group)

    return render(request, "rabbits/create_group.html", {"form": form})

def rabbit_detail(request, pk):
    rabbit = get_object_or_404(Rabbit, pk=pk)
    events = rabbit.events.all().order_by("-date")
    return render(
        request,
        "rabbits/rabbit_detail.html",
        {"rabbit": rabbit, "events": events}
    )


def rabbit_list(request):
    rabbits_list = Rabbit.objects.all().order_by("inventory_number")

    paginator = Paginator(rabbits_list, 5)
    page_number = request.GET.get("page")
    rabbits = paginator.get_page(page_number)

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

    farm = Farm.objects.filter(owner=request.user).first()

    return render(request, "rabbits/rabbit_list.html", {
        "rabbits": rabbits,
        "farm": farm
})

def rabbit_create(request):
    if request.method == "POST":
        form = RabbitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Кролика додано успішно")
            return redirect("rabbit_list")
    else:
        form = RabbitForm()

    return render(request, "rabbits/rabbit_form.html", {
        "form": form
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

