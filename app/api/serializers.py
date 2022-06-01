from datetime import date, datetime

from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.models import CustomUser, CinemaHall, MovieShow, PurchasedTicket


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def save(self, **kwargs):
        if len(self.validated_data['password']) < 8 :
            raise serializers.ValidationError({'password': 'password must be at least 8 characters long'})
        self.validated_data['password'] = make_password(self.validated_data['password'])
        return super().save()


class LoginSerializer(serializers.ModelSerializer):
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = CustomUser.objects.get(user=obj)

        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }


class CinemaHallSerializer(serializers.ModelSerializer):

    class Meta:
        model = CinemaHall
        fields = ['id', 'hall_name', 'number_of_seats']

    def validate(self, data):
        if self.instance:
            cinema_hall_obj = CinemaHall.objects.get(id=self.instance.id)
            if cinema_hall_obj.get_tickets():
                raise serializers.ValidationError(
                    {'cinema_hall': 'В этом зале куплены билеты, изменить нельзя'})
        return data


class MovieShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = MovieShow
        fields = '__all__'

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        finish_time = attrs.get('finish_time')
        start_date = attrs.get('start_date')
        finish_date = attrs.get('finish_date')

        if start_date > finish_date:  # старт дата больше конца даты
            raise ValidationError({
                'start_date, finish_date': 'Дата конца сеанса не может быть раньше чем дата начала сеанса!'})

        if start_date == finish_date and start_time >= finish_time:  # дата старта равна дате конца, время начала больше время конца
            raise ValidationError({
                'start_date, finish_date':'Время начала сеанса не может быть позже чем время конца сеанса!'})

        if start_date < date.today():  # дата старта меньше сегодня
            raise ValidationError({
                'start_date, finish_date': 'Нельзя создать сеанс в прошлом!'})

        if start_date == date.today() and start_time < datetime.now().time():  # дата начала сегодня, время начала меньше чем сейчас
            raise ValidationError({
                'start_date, finish_date': 'Нельзя создать сеанс в прошлом!'})

        if self.instance:
            movie = self.instance
            if movie.get_purchased():
                raise serializers.ValidationError('На этот сеанс уже куплены билеты, поэтому нельзя изменить!')

        cinema_hall_obj = CinemaHall.objects.get(id=attrs.get('cinema_hall').id)

        enter_start_date = Q(start_date__range=(start_date, finish_date))
        enter_finish_date = Q(finish_date__range=(start_date, finish_date))
        middle_date_start = Q(start_date__lte=start_date, finish_date__gte=finish_date)
        enter_start_time = Q(start_time__range=(start_time, finish_time))
        enter_finish_time = Q(finish_time__range=(start_time, finish_time))

        movie_obj = MovieShow.objects.filter(cinema_hall=cinema_hall_obj.pk).filter(
            enter_start_date | enter_finish_date | middle_date_start).filter(enter_start_time | enter_finish_time)

        if movie_obj:
            raise serializers.ValidationError(
                {'start_date, finish_date': 'Сеансы в одном зале не могут накладываться друг на друга'})

        if start_time > finish_time:
            enter_start_time_until_midnight = Q(start_time__range=(start_time, '23:59:59'))
            enter_start_time_after_midnight = Q(start_time__range=('00:00:00', finish_time))
            enter_finish_time_until_midnight = Q(finish_time__range=(start_time, '23:59:59'))
            enter_finish_time_after_midnight = Q(finish_time__range=('00:00:00', finish_time))

            movie_obj = MovieShow.objects.filter(cinema_hall=cinema_hall_obj.pk).filter(
                enter_start_date | enter_finish_date | middle_date_start). \
                filter(enter_start_time_until_midnight | enter_start_time_after_midnight |
                       enter_finish_time_until_midnight | enter_finish_time_after_midnight).all()

        if movie_obj:
            raise serializers.ValidationError(
                {'start_date, finish_date': 'Сеансы в одном зале не могут накладываться друг на друга'})
        return attrs


class PurchaseSerializer(serializers.ModelSerializer):

    movie_show = MovieShowSerializer()

    class Meta:
        model = PurchasedTicket
        fields = ['date', 'movie_show', 'number_of_ticket']


class PurchaseSerializerCreate(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(PurchaseSerializerCreate, self).__init__(*args, **kwargs)

    class Meta:
        model = PurchasedTicket
        fields = ['date', 'movie_show', 'number_of_ticket']

    def create(self, validated_data):
        """
        Create and return a new `PurchasedTicket` instance, given the validated data.
        """
        return PurchasedTicket.objects.create(**validated_data)

    def validate(self, data):
        movie = data['movie_show']
        date_purchase = data['date']
        number_of_ticket = data['number_of_ticket']
        data['user'] = CustomUser.objects.get(id=self.user_id)
        if number_of_ticket <= 0:
            raise serializers.ValidationError({'number_of_ticket': 'Вы не выбрали нужного количества билетов'})
        if movie.get_tickets_count(data['date']) - int(number_of_ticket) < 0:
            raise serializers.ValidationError({'number_of_ticket': 'Такого количества свободных мест нет'})
        if movie.start_time < datetime.now().time() and date_purchase == date.today():
            raise serializers.ValidationError({'start_time': 'Онлайн продажи для этого сеанса закрыты'})
        if date_purchase < date.today():
            raise serializers.ValidationError({'date': 'Этот сеанс уже завершился'})
        return data

