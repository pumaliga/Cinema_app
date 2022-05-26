import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from app.forms import RegisterForm, MovieShowCreateForm, HallCreateForm, BuyTicketForm, ChoiceForm, MovieShowUpdateForm
from app.models import MovieShow, CinemaHall, PurchasedTicket


class Login(LoginView):
    success_url = '/'
    template_name = 'login.html'


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = '/'


class Logout(LoginRequiredMixin, LogoutView):
    next_page = '/'
    login_url = reverse_lazy('login')


class MovieListView(LoginRequiredMixin, ListView):
    model = MovieShow
    login_url = 'login/'
    template_name = 'index.html'
    paginate_by = 3
    extra_context = {'buy_ticket_form': BuyTicketForm}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_form'] = ChoiceForm

        if self.request.GET.get('filter_by'):
            context['filter'] = self.request.GET.get('filter_by')

        if self.request.GET.get('show_date') == 'Tomorrow':
            context['date'] = str(datetime.date.today() + datetime.timedelta(days=1))
            context['day'] = 'Tomorrow'

        elif self.request.GET.get('show_date') == 'Today':
            context['date'] = str(datetime.date.today())
            context['day'] = 'Today'
        else:
            context['date'] = str(datetime.date.today())
        return context

    def get_ordering(self):
        filter_by = self.request.GET.get('filter_by')
        if filter_by == 'start_time':
            self.ordering = ['start_time']
        elif filter_by == 'price_max':
            self.ordering = ['ticket_price']
        elif filter_by == 'price_min':
            self.ordering = ['-ticket_price']
        return self.ordering

    def get_queryset(self):
        if self.request.GET.get('show_date') == 'Tomorrow':
            return super().get_queryset().filter(start_date__lte=datetime.date.today() + datetime.timedelta(days=1),
                                                 finish_date__gte=datetime.date.today() + datetime.timedelta(days=1))
        elif self.request.GET.get('show_date') == 'Today':
            return super().get_queryset().filter(start_date__lte=datetime.date.today(),
                                                 finish_date__gte=datetime.date.today())
        else:
            return super().get_queryset()


class MovieShowCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'is_superuser'
    model = MovieShow
    form_class = MovieShowCreateForm
    template_name = 'create_movie.html'
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class MovieUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'is_superuser'
    model = MovieShow
    form_class = MovieShowUpdateForm
    template_name = 'update_movie.html'
    success_url = '/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.get_purchased():
            messages.warning(self.request, 'На этот сеанс уже куплены билеты, поэтому нельзя изменить!')
            return super().form_invalid(form=form)

        enter_start_date = Q(start_date__range=(obj.start_date, obj.finish_date))
        middle_date_start = Q(start_date__lte=obj.start_date, finish_date__gte=obj.finish_date)
        enter_finish_date = Q(finish_date__range=(obj.start_date, obj.finish_date))
        enter_start_time = Q(start_time__range=(obj.start_time, obj.finish_time))
        enter_finish_time = Q(finish_time__range=(obj.start_time, obj.finish_time))

        movie_obj = MovieShow.objects.filter(cinema_hall=obj.cinema_hall).exclude(id=obj.id).filter(
            enter_start_date | enter_finish_date | middle_date_start).filter(enter_start_time | enter_finish_time).all()

        if movie_obj:
            messages.warning(self.request, 'В это время зал занят!')
            return super().form_invalid(form=form)

        if obj.start_time > obj.finish_time:
            enter_start_time_until_midnight = Q(start_time__range=(obj.start_time, '23:59:59'))
            enter_start_time_after_midnight = Q(start_time__range=('00:00:00', obj.finish_time))
            enter_finish_time_until_midnight = Q(finish_time__range=(obj.start_time, '23:59:59'))
            enter_finish_time_after_midnight = Q(finish_time__range=('00:00:00', obj.finish_time))

            movie_obj = MovieShow.objects.filter(cinema_hall=obj.cinema_hall).exclude(id=obj.id).filter(
                enter_start_date | enter_finish_date | middle_date_start).filter(
                enter_start_time_until_midnight | enter_start_time_after_midnight |
                enter_finish_time_until_midnight | enter_finish_time_after_midnight)

        if movie_obj:
            messages.warning(self.request, 'Сеансы в одном зале не могут накладываться друг на друга')
            return super().form_invalid(form=form)

        obj.save()
        return super().form_valid(form=form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class TicketBuyCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login/'
    http_method_names = ['post', ]
    form_class = BuyTicketForm
    success_url = '/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        number_of_ticket = int(self.request.POST.get('number_of_ticket'))
        movie_id = self.request.POST.get('movie-id')
        obj.movie_show = MovieShow.objects.get(id=movie_id)
        obj.user.money_spent += obj.movie_show.ticket_price * number_of_ticket

        if self.request.POST.get('date-buy'):
            obj.date = self.request.POST.get('date-buy')

        else:
            obj.date = str(datetime.date.today())
            obj.purchase_amount = obj.movie_show.ticket_price * number_of_ticket
        with transaction.atomic():
            obj.user.save()
            obj.save()
        return super().form_valid(form=form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        return HttpResponseRedirect(reverse_lazy('index'))


class HallCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login/'
    form_class = HallCreateForm
    template_name = 'create_hall.html'
    success_url = '/hall/list/'


class HallListView(ListView):
    model = CinemaHall
    template_name = 'hall_list.html'


class HallUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'is_superuser'
    model = CinemaHall
    form_class = HallCreateForm
    template_name = 'update_hall.html'
    success_url = '/hall/list/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.get_tickets():
            messages.warning(self.request, 'В этот зал уже куплены билеты, изменить нельзя')
            return super().form_invalid(form=form)
        obj.save()
        return super().form_valid(form=form)


class PurchasesListView(LoginRequiredMixin, ListView):
    login_url = 'login/'
    model = PurchasedTicket
    template_name = 'purchases.html'
    paginate_by = 2

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['all_purchases'] = self.request.user.money_spent
            return context
        return context

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user.id)
