from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum


class CustomUser(AbstractUser):
    money_spent = models.PositiveIntegerField(default=0)


class CinemaHall(models.Model):
    hall_name = models.CharField(max_length=200, unique=True)
    number_of_seats = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.hall_name

    def get_tickets(self):
        movie_shows_id = MovieShow.objects.filter(cinema_hall=self).values_list('id', flat=True)
        return PurchasedTicket.objects.filter(movie_show__in=movie_shows_id).first()


class MovieShow(models.Model):
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    movie_name = models.CharField(max_length=120)
    ticket_price = models.PositiveIntegerField(default=100)
    start_time = models.TimeField()
    finish_time = models.TimeField()
    start_date = models.DateField()
    finish_date = models.DateField()
    cinema_hall = models.ForeignKey(CinemaHall, on_delete=models.CASCADE, related_name='movie_show')

    def get_purchased(self):
        return self.purchased_tickets.filter().first()

    def get_tickets_count(self, date_today=date.today()):
        if self.purchased_tickets.filter(date=date_today).aggregate(Sum('number_of_ticket')).get(
                'number_of_ticket__sum'):
            return self.cinema_hall.number_of_seats - self.purchased_tickets.filter(date=date_today) \
                .aggregate(Sum('number_of_ticket')).get('number_of_ticket__sum')
        return self.cinema_hall.number_of_seats


    def __str__(self):
        return self.movie_name


class PurchasedTicket(models.Model):
    date = models.DateField(auto_now=False)
    number_of_ticket = models.PositiveIntegerField(default=1)
    movie_show = models.ForeignKey(MovieShow, on_delete=models.DO_NOTHING, related_name='purchased_tickets')
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, related_name='user')

    def get_purchase_amount(self):
        return self.number_of_ticket * self.movie_show.ticket_price
