from django.contrib import admin

from app.models import CinemaHall, PurchasedTicket, MovieShow


admin.site.register(CinemaHall)
admin.site.register(PurchasedTicket)
admin.site.register(MovieShow)
