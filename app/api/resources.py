import datetime
from datetime import date

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from app.api.serializers import RegisterSerializer, CinemaHallSerializer, MovieShowSerializer, PurchaseSerializer, \
    PurchaseSerializerCreate
from app.models import CustomUser, CinemaHall, MovieShow, PurchasedTicket


class RegisterAPI(CreateAPIView):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer


class APILogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = self.request.data.get('refresh_token')
        print(refresh_token)
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        return Response({"status": "OK, goodbye"})


class CinemaHallViewSet(ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        return super().get_permissions()


class MovieViewSet(ModelViewSet):
    queryset = MovieShow.objects.all()
    serializer_class = MovieShowSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        show_day = self.request.query_params.get('show_day')
        if show_day == 'tomorrow':
            return super().get_queryset().filter(start_date__lte=date.today() + datetime.timedelta(days=1),
                                                 finish_date__gt=date.today())

        return super().get_queryset().filter(start_date__lte=date.today(),  # show_day == 'today'
                                             finish_date__gte=date.today())


class PurchaseList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purchase_list = PurchasedTicket.objects.filter(user=request.user.id)
        serializer = PurchaseSerializer(purchase_list, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PurchaseSerializerCreate(data=request.data, user_id=request.user.id)
        if serializer.is_valid():
            user = CustomUser.objects.get(id=request.user.id)

            with transaction.atomic():
                obj = serializer.save()
                user.money_spent += obj.get_purchase_amount()
                user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


