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
            return redirect("group_list")
    else:
        form = GroupForm()

    return render(request, "rabbits/create_group.html", {"form": form})

@login_required
def group_list(request):
    farm = Farm.objects.filter(owner=request.user).first()
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

    return render(request, "rabbits/edit_group.html", {"form": form})

@login_required
def rabbit_detail(request, pk):
    farm = request.user.farms.first()
    rabbit = get_object_or_404(Rabbit, pk=pk, farm=farm)
    events = rabbit.events.all().order_by("-date")
    return render(
        request,
        "rabbits/rabbit_detail.html",
        {"rabbit": rabbit, "events": events}
    )


@login_required
def rabbit_list(request):
    farm = Farm.objects.filter(owner=request.user).first()
    rabbits_list = Rabbit.objects.filter(farm=farm).order_by("inventory_number")

    paginator = Paginator(rabbits_list, 5)
    page_number = request.GET.get("page")
    rabbits = paginator.get_page(page_number)

    for rabbit in rabbits:
        rabbit.last_event = Event.objects.filter(
            rabbit=rabbit
        ).order_by("-date").first()

        if rabbit.last_event and rabbit.last_event.next_action_date:
            days_left = (rabbit.last_event.next_action_date - date.today()).days

            if days_left < 0:
                rabbit.status = "критичний"
            elif days_left <= 7:
                rabbit.status = "увага"
            else:
                rabbit.status = "норма"
        else:
            rabbit.status = "—"

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
        "rabbits": rabbits,
        "farm": farm
    })

@login_required
def rabbit_create(request):
    farm = request.user.farms.first()

    if request.method == "POST":
        form = RabbitForm(request.POST, request.FILES)
        if form.is_valid():
            rabbit = form.save(commit=False)
            rabbit.farm = farm
            rabbit.save()
            messages.success(request, "Кролика додано успішно")
            return redirect("rabbit_list")
    else:
        form = RabbitForm()

    return render(request, "rabbits/rabbit_form.html", {
        "form": form
    })

def landing(request):
    return render(request, "landing.html")

@login_required
def home(request):
    farm = Farm.objects.filter(owner=request.user).first()

    if not farm:
        return redirect("create_farm")

    rabbits = Rabbit.objects.filter(farm=farm)
    

    rabbits_count = rabbits.count()
    males = rabbits.filter(sex="M").count()
    females = rabbits.filter(sex="F").count()

    today = date.today()

    red_light = False
    yellow_light = False
    green_light = False

    upcoming_events = []

    for rabbit in rabbits:
        latest_event = Event.objects.filter(
            rabbit=rabbit,
            next_action_date__isnull=False
        ).order_by("-date").first()

        if latest_event:
            upcoming_events.append(latest_event)

            if latest_event.next_action_date < today:
                red_light = True
            elif latest_event.next_action_date <= today + timedelta(days=7):
                yellow_light = True
            else:
                green_light = True

    upcoming_event = sorted(
        upcoming_events,
        key=lambda x: x.next_action_date
    )[0] if upcoming_events else None

    if red_light:
        yellow_light = False
        green_light = False
    elif yellow_light:
        green_light = False
    context = {
        "farm": farm,
        "rabbits_count": rabbits_count,
        "males": males,
        "females": females,
        "red_light": red_light,
        "yellow_light": yellow_light,
        "green_light": green_light,
        "upcoming_event": upcoming_event,
    }

    return render(request, "home.html", context)

