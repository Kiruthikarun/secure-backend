from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer

User = get_user_model() 

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists. Please use a different email."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists. Please choose a different username."}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isupper() for c in password) or not any(c in "@$!%*?&" for c in password):
            return Response({"error": "Password must have at least 6 characters, including one uppercase, one lowercase, one number, and one special character."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier", "").strip().lower()
        password = request.data.get("password", "").strip()

        if not identifier or not password:
            return Response({"error": "Username or Email and Password required", "identifier": identifier, "password": password}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=identifier).first() or User.objects.filter(username=identifier).first()

        if user:
            if user.check_password(password):  
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid password", "identifier": identifier}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({"error": "User not found", "identifier": identifier}, status=status.HTTP_404_NOT_FOUND)

class SimplePasswordReset(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier") 
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not identifier or not new_password or not confirm_password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=identifier).first() or User.objects.filter(username=identifier).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful!"}, status=status.HTTP_200_OK)
