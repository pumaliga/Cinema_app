from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.api.resources import RegisterAPI, APILogoutView, CinemaHallViewSet, MovieViewSet, PurchaseList
from app.views import MovieListView, Login, Register, HallListView, MovieShowCreateView, HallCreateView, \
    TicketBuyCreateView, Logout, PurchasesListView, HallUpdateView, MovieUpdateView


router = routers.SimpleRouter()
# router.register(r'session', MovieShowViewSet)


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

urlpatterns += [
    path('api/register/', RegisterAPI.as_view(), name='sign-up'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/logout/', APILogoutView.as_view(), name='logout_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/hall/', CinemaHallViewSet.as_view({'get': 'list',
                                                 'post': 'create'}), name='cinema_hall_list'),
    path('api/hall/<int:pk>/', CinemaHallViewSet.as_view({'put': 'update'}), name='cinema_hall_update'),
    path('api/movie/', MovieViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update'}), name='show_movie'),
    path('api/movie/<int:pk>/', MovieViewSet.as_view({'put': 'update'}), name='show_movie'),
    path('api/movie/<str:show_day>/', MovieViewSet.as_view({'get': 'list'}), name='show_day'),
    path('api/purchased/', PurchaseList.as_view(), name='api-purchased'),

]