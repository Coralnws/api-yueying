from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from rest_framework.response import Response
from rest_framework import generics, status, views, permissions
from django.contrib.auth.hashers import make_password,check_password
from django.db.models import Q

import jwt
from ..serializers.userSerializers import *
from ..utils import get_tokens, send_smtp
from ..models.users import CustomUser
from ..models.userRelations import *

"""
POST: Register
"""
class UserRegisterView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            newUser = CustomUser.objects.get(email=serializer.data['email'])
            newToken = get_tokens(newUser)['access']

            send_smtp(newUser, request, newToken, "Activate Account", "register_email.txt" )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            return Response({"message": "Register Failed"}, status=status.HTTP_400_BAD_REQUEST)

"""
GET: Activate Account
"""
class UserActivateView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserActivateSerializer

    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user = CustomUser.objects.get(id=payload['user_id'])
            if not user.is_active:
                user.is_active = True
                user.updatedAt = timezone.now()
                user.save()
            return Response({"message": "Activate Account Successfully!"}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Activation Code Expire"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


"""
POST: Request Password
"""
class RequestPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestPasswordSerializer

    def post(self, request):
        try: 
            email = request.data.get('email', '')
            username = request.data.get('username', '')

            if CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.get(email=email)
                if not user.username == username: # incase the username is not the same as email
                    return Response({"message": "Invalid Username or Email"}, status=status.HTTP_400_BAD_REQUEST)
                newToken = get_tokens(user)['access']
                send_smtp(user, request, newToken, "Reset Password for YueYing", "reset_email.txt")
                return Response({"message": "Please check your email for futher info."}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Failed to Request Password"}, status=status.HTTP_400_BAD_REQUEST)

"""
GET: Validate Token for Reset Password
"""
class ResetPasswordTokenValidateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user = CustomUser.objects.get(id=payload['user_id'])
            authToken = get_tokens(user)
            return Response(authToken, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"message": "Reset Link Expire"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
'''
class ResetPasswordbyOldpasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResetPasswordSerializer

    def put(self, request):
        try:
            oldpassword=request.data['oldpassword']
            newpassword=request.data['newpassword']
            username = request.user
            user = CustomUser.objects.get(username=username)
            result = user.check_password(oldpassword)
            if result:
                user.set_password(newpassword)
                user.save()
                # When update success, should terminate the token, so it cannot be used again
                return Response({"message": "Password Reset Successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Password Reset Failed"}, status=status.HTTP_400_BAD_REQUEST)
'''

"""
PUT: Reset Password (for authenticated user only)
"""
class ResetPasswordbyOldpasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResetPasswordByPasswordSerializer

    def put(self, request):
        try:
            oldpassword = request.data['oldpassword']
            username = request.user.username
            user = CustomUser.objects.get(username=username)
            result = user.check_password(oldpassword)
            if result:
                serializer = self.get_serializer(data=request.data, user=self.request.user)
                if serializer.is_valid(raise_exception=True):
                    serializer.updatePassword()
                    # When update success, should terminate the token, so it cannot be used again
                    return Response({"message": "Password Reset Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Old Password Is Incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Password Reset Failed"}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordbyQuestionView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordByQuestionSerializer

    def put(self, request):
        try:
            username = request.data['username']
            questionNo = int(request.data['securityQuestion'])
            answer = request.data['securityAnswer'].lower()
            answer = make_password(answer,"a","pbkdf2_sha1")
            user = CustomUser.objects.get(username=username)
            user = get_object_or_404(CustomUser, username=username)

            correctAns = user.securityAnswer
            correctNo = user.securityQuestion

            if questionNo == correctNo:
                if correctAns == answer:
                    serializer = self.get_serializer(data=request.data, user=user)
                    if serializer.is_valid(raise_exception=True):
                        serializer.updatePassword()
                        # When update success, should terminate the token, so it cannot be used again
                        return Response({"message": "Password Reset Successfully"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Security Answer Is Incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"message": "Security Question Is Incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Password Reset Failed"}, status=status.HTTP_400_BAD_REQUEST)

class ResetSecurityQuestionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            password = request.data['password']
            username = request.user.username
            user = CustomUser.objects.get(username=username)
            result = user.check_password(password)

            if result:
                securityAnswer = request.data['securityAnswer']
                securityQuestion = request.data['securityQuestion']
                securityAnswer = securityAnswer.lower()
                user.securityAnswer = make_password(securityAnswer, "a", "pbkdf2_sha1")
                user.securityQuestion = securityQuestion
                user.updatedAt = timezone.now()
                user.save()
                return Response({"message": "Security Question Reset Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Password Is Incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Security Question Reset Failed"}, status=status.HTTP_400_BAD_REQUEST)
"""
POST: Login
"""
class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status= status.HTTP_200_OK)

"""
POST: Logout
"""
class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        try:
            # apparently no need to delete access token on logout, it should time out quickly enough anyway.
            # https://medium.com/devgorilla/how-to-log-out-when-using-jwt-a8c7823e8a6
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response({"message": "Logout Failed"}, status=status.HTTP_400_BAD_REQUEST)


""" For Admin(superuser)
GET: Get User Detail By Id  # for any
PUT: Update User By Id      # for superuser or owner
DELETE: Delete User By Id (set isDelete = True)     # for superuser or owner
"""
class UserDetailView(generics.GenericAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return UserProfileSerializer
        return UserDetailSerializer


    def get(self, request, userId):
        try:
            user = CustomUser.objects.get(pk=userId)
            books = userBook.objects.filter(user=user, isSaved=True)
            movies = userMovie.objects.filter(user=user, isSaved=True)
            feeds = userFeed.objects.filter(user=user, isFollowed=True)
            user.books = books;
            user.movies = movies;
            user.feeds = feeds;
            serializer=self.get_serializer(instance=user)
            return Response(data=serializer.data ,status=status.HTTP_200_OK)
        except:
            return Response({"message": "Get User Detail Failed"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, userId):
        try:
            user = get_object_or_404(CustomUser, pk=userId)
            if not request.user.is_staff and request.user != user:
                return Response({"message": "Unauthorized for update user"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = self.get_serializer(instance=user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updatedAt=timezone.now())
            return Response({"message": "Update User Successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Update User Failed"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, userId):
        try:
            user = get_object_or_404(CustomUser, pk=userId)
            if not request.user.is_staff and request.user != user:
                return Response({"message": "Unauthorized for delete user"}, status=status.HTTP_401_UNAUTHORIZED)
            user.isDeleted = True
            user.updatedAt = timezone.now()
            user.save()
            return Response({"message": "Delete User Successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Delete User Failed"}, status=status.HTTP_400_BAD_REQUEST)

"""
POST: Create User (email, username)
"""
class UserCreateView(generics.ListCreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request): 
        try:
            if not request.user.is_staff:
                return Response({"message": "Unauthorized for create user"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            newUser = CustomUser.objects.get(email=serializer.data['email'])
            newToken = get_tokens(newUser)['access']

            send_smtp(newUser, request, newToken, "Activate Account", "register_email.txt" )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            return Response({"message": "Create User Failed"}, status=status.HTTP_400_BAD_REQUEST)


"""
GET: Get All Users
"""
class UserListView(generics.ListCreateAPIView):
    serializer_class = ListUserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        search = self.request.GET.get('search')
        isDeleted = self.request.GET.get('isDelete')
        isActive = self.request.GET.get('isActive')
        gender = self.request.GET.get('gender')
        filter = Q()
        if search is not None:
            searchTerms = search.split(' ')
            for term in searchTerms:
                filter &= Q(username__icontains=term) | Q(firstName__icontains=term) | Q(lastName__icontains=term) | Q(email__icontains=term)

        if isDeleted is None:
            isDeleted = False

        if isActive is None:
            isActive = True

        if gender is not None:
            filter &= Q(gender=gender)

        filter &= Q(is_active=isActive)
        filter &= Q(isDelete=isDeleted)

        return CustomUser.objects.filter(filter)
