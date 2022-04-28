from django.shortcuts import get_list_or_404, get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status, views, permissions

from ..serializers.movieSerializers import *
from ..utils import *
from ..models.movies import Movie


""" For Admin(superuser)
GET: Get Movie Detail By Id  # for any
PUT: Update Movie By Id      # for superuser
DELETE: Delete Movie By Id (set isDelete = True)     # for superuser
"""
class MovieDetailView(generics.GenericAPIView):
    serializer_class = MovieDetailSerializer
    permissions_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Get Movie Detail By Id
    def get(self, request, movieId):
        try:
            movie = get_object_or_404(Movie, pk=movieId)
            serializer = self.serializer_class(instance=movie)
            return Response(data=serializer.data ,status=status.HTTP_200_OK)
        except:
            return Response({"message": "Get Movie Detail Failed"}, status=status.HTTP_400_BAD_REQUEST)

    # Update Movie By Id
    def put(self, request, movieId):
        movie = get_object_or_404(Movie, pk=movieId)
        serializer = self.serializer_class(instance=movie, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Update Movie Successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    # Delete Movie By Id
    def delete(self, request, movieId):
        try:
            movie = get_object_or_404(Movie, pk=movieId)
            movie.delete()
            return Response({"message": "Delete Movie Successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Delete Movie Failed"}, status=status.HTTP_400_BAD_REQUEST)


"""
GET: Get All Movies
POST: Create Movie
"""
class MovieListAndCreateView(generics.ListCreateAPIView):
    serializer_class = ListMovieSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            # Since the ReadSerializer does nested lookups
            # in multiple tables, only use it when necessary
            return ListMovieSerializer
        return MovieCreateSerializer

    # Get All Movies
    def get_queryset(self):
        return Movie.objects.filter()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)