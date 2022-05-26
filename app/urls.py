from django.urls import path

from app.views import MovieListView, Login, Register, HallListView, MovieShowCreateView, HallCreateView, \
    TicketBuyCreateView, Logout, PurchasesListView, HallUpdateView, MovieUpdateView

urlpatterns = [
    path('', MovieListView.as_view(), name='index'),
    path('login/', Login.as_view(), name='login'),
    path('register/', Register.as_view(), name='register'),
    path('logout/', Logout.as_view(), name='logout'),
    path('create/hall/', HallCreateView.as_view(), name='create_hall'),
    path('hall/list/', HallListView.as_view(), name='hall_list'),
    path('create/movie/', MovieShowCreateView.as_view(), name='create_movie'),
    path('ticket/buy/', TicketBuyCreateView.as_view(), name='ticket_buy'),
    path('purchases/', PurchasesListView.as_view(), name='purchases'),
    path('update/hall/<int:pk>/', HallUpdateView.as_view(), name='update_hall'),
    path('update/movie/<int:pk>/', MovieUpdateView.as_view(), name='update_movie'),


]