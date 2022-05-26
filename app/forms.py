from datetime import datetime, date

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.widgets import TextInput
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from app.models import CustomUser, MovieShow, CinemaHall, PurchasedTicket


class NumberInput(TextInput):
    input_type = 'number'


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']


class HallCreateForm(ModelForm):
    class Meta:
        model = CinemaHall
        fields = ['hall_name', 'number_of_seats']


class ChoiceForm(forms.Form):
    sort_by_price_max = 'price_max'
    sort_by_price_min = 'price_min'
    sort_by_start_time = 'start_time'
    sort_movies = [
        (sort_by_start_time, 'For start movie'),
        (sort_by_price_max, 'Price range up'),
        (sort_by_price_min, 'Price range down')
    ]
    filter_by = forms.ChoiceField(choices=sort_movies, label='Filter')


class MovieShowCreateForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = MovieShow
        fields = '__all__'

        widgets = {
            'start_date': DateInput(),
            'finish_date': DateInput(),
            'start_time': TimeInput(),
            'finish_time': TimeInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        finish_time = cleaned_data.get('finish_time')
        start_date = cleaned_data.get('start_date')
        finish_date = cleaned_data.get('finish_date')
        cinema_hall_obj = cleaned_data.get('cinema_hall')

        if start_date > finish_date:  # старт дата больше конца даты
            raise ValidationError('Дата конца сеанса не может быть раньше чем дата начала сеанса!')

        if start_date == finish_date and start_time >= finish_time:  # дата старта равна дате конца, время начала больше время конца
            raise ValidationError('Время начала сеанса не может быть позже чем время конца сеанса!')

        if start_date < date.today():  # дата старта меньше сегодня
            raise ValidationError('Нельзя создать сеанс в прошлом!')

        if start_date == date.today() and start_time < datetime.now().time():  # дата начала сегодня, время начала меньше чем сейчас
            raise ValidationError('Нельзя создавать сеанс в прошедшем времени!')

        enter_start_date = Q(start_date__range=(start_date, finish_date))  # date
        enter_finish_date = Q(finish_date__range=(start_date, finish_date))
        middle_date_start = Q(start_date__lte=start_date, finish_date__gte=finish_date)
        enter_start_time = Q(start_time__range=(start_time, finish_time))  # time
        enter_finish_time = Q(finish_time__range=(start_time, finish_time))

        movie_obj = MovieShow.objects.filter(cinema_hall=cinema_hall_obj.pk).filter(
            enter_start_date | enter_finish_date | middle_date_start).filter(enter_start_time | enter_finish_time).all()

        if start_time > finish_time:
            enter_start_time_until_midnight = Q(start_time__range=(start_time, '23:59:59'))
            enter_start_time_after_midnight = Q(start_time__range=('00:00:00', finish_time))
            enter_finish_time_until_midnight = Q(finish_time__range=(start_time, '23:59:59'))
            enter_finish_time_after_midnight = Q(finish_time__range=('00:00:00', finish_time))

            movie_obj = MovieShow.objects.filter(cinema_hall=cinema_hall_obj.pk).filter(
                enter_start_date | enter_finish_date | middle_date_start). \
                filter(enter_start_time_until_midnight | enter_start_time_after_midnight |
                       enter_finish_time_until_midnight | enter_finish_time_after_midnight)

        if movie_obj:
            raise ValidationError('Сеансы в одном зале не могут накладываться друг на друга')


class MovieShowUpdateForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request',  None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = MovieShow
        fields = '__all__'

        widgets = {
            'start_date': DateInput(),
            'finish_date': DateInput(),
            'start_time': TimeInput(),
            'finish_time': TimeInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        finish_time = cleaned_data.get('finish_time')
        start_date = cleaned_data.get('start_date')
        finish_date = cleaned_data.get('finish_date')

        if start_date > finish_date:
            # messages.warning(self.request, 'Дата конца сеанса не может быть раньше чем дата начала сеанса!')
            raise ValidationError('Дата конца сеанса не может быть раньше чем дата начала сеанса!')

        if start_date == finish_date and start_time >= finish_time:
            # messages.warning(self.request, 'Время начала сеанса не может быть позже чем время конца сеанса!')
            raise ValidationError('Время начала сеанса не может быть позже чем время конца сеанса!')

        if start_date < date.today() or start_date == date.today() and start_time < datetime.now().time():
            # messages.warning(self.request, 'Нельзя создать сеанс в прошлом!')
            raise ValidationError('Нельзя создать сеанс в прошлом!')


class BuyTicketForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = PurchasedTicket
        fields = ['number_of_ticket']

        widgets = {
            'number_of_ticket': NumberInput(attrs={'min': '1', 'step': '1'})
        }

    def clean(self):
        cleaned_data = super().clean()
        movie_id = self.request.POST.get('movie-id')
        movie_show = MovieShow.objects.get(id=movie_id)
        count_of_buy = int(cleaned_data.get('number_of_ticket'))
        tickets_left = int(self.request.POST.get('tickets_left'))

        if movie_show.start_time < datetime.now().time() and self.request.POST.get('date-buy') == str(date.today()):
            messages.warning(self.request, 'Продажи для этого сеанса на сегодня закрыты')
            raise ValidationError('Этот сеанс уже завершился')

        if count_of_buy > tickets_left:
            messages.warning(self.request, 'Такого количества свободных мест нет')
            raise ValidationError('Такого количества свободных мест нет')
