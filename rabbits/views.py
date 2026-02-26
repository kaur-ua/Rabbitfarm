<<<<<<< HEAD
from django.shortcuts import render
from .models import Rabbit


=======
from django.shortcuts import render, get_object_or_404
from .models import Rabbit


def rabbit_detail(request, pk):
    rabbit = get_object_or_404(Rabbit, pk=pk)
    events = rabbit.events.all().order_by("-date")
    return render(
        request,
        "rabbits/rabbit_detail.html",
        {"rabbit": rabbit, "events": events}
    )

>>>>>>> 0b1fb24 (MVP v1.0: inventory number, rabbit detail page, event journal)
def rabbit_list(request):
    rabbits = Rabbit.objects.all()
    return render(request, "rabbits/rabbit_list.html", {"rabbits": rabbits})
