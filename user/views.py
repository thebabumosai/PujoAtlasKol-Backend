from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q, F
from .models import User, BlacklistedToken
from .serializers import UserSerializer,UserLoginSerializer,UserLogoutSerializer,RefreshTokenSerializer,UserDetailsSerializer,CollectionSerializer
from core.ResponseStatus import ResponseStatus
import logging
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from .permission import IsAuthenticatedUser
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from django.core.management import call_command

logger = logging.getLogger("user")

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticatedUser]

    def get_permissions(self):
        if self.action == 'create':
            # Allow anyone to create a user
            return [permissions.AllowAny()]
        return super().get_permissions()
         
    def create(self, request, *args, **kwargs):
        try:
            required_fields = ['email', 'password', 'username', 'user_type']
            missing_fields = [field for field in required_fields if field not in request.data or not request.data.get(field)]
                
            if missing_fields:
                response_data = {
                'error': f"The following fields are required: {', '.join(missing_fields)}",
                'status': ResponseStatus.FAIL.value
                }
                logger.error(f"Error: {response_data['error']}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_data={
                    'result':'User registered successfully',
                    'status':ResponseStatus.SUCCESS.value
                }
                logger.info(f"Success: {response_data['result']}")
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data={
                    'error':serializer.errors,
                    'status': ResponseStatus.FAIL.value
                }
                logger.error(f"Error: {(response_data['error'])}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:  # Catch any other unexpected exceptions
            response_data = {
                'error': str(e),
                'status': ResponseStatus.FAIL.value
            }
            logger.error(f"Error: {str(response_data['error'])}")
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='get_user_details')
    def get_user_details(self, request, user_id=None, *args, **kwargs):
        try:
            user = self.get_queryset().filter(id=user_id).first()
            if user is None:
                response_data={
                'error':"User not found",
                'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
            else:
                serializer = UserDetailsSerializer(user)
                response_data = {
                'result': serializer.data,
                'message':'User Details fetched successfully',
                'status': ResponseStatus.SUCCESS.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = {
                'error': str(e),
                'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, uuid, *args, **kwargs):
        try:
            user = self.get_queryset().filter(id=uuid).first()
            self.check_object_permissions(request, user)
            if not user:
                response_data={
                'error':"User does not exist",
                'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
            else:
                serializer = self.get_serializer(user)
                response_data = {
                    'result':serializer.data,
                    'message':'User data fetched successfully',
                    'status':ResponseStatus.SUCCESS.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            response_data = {
                'result':'User does not exist',
                'status':ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, uuid=None, *args, **kwargs):
        user = self.get_queryset().filter(id=uuid).first()
        self.check_object_permissions(request, user)
        if not user:
            response_data = {
                'error': "User does not exist",
                'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        
        # Pass the data to the serializer
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            response_data = {
                'result': serializer.data,
                'message':'User updated successfully',
                'status': ResponseStatus.SUCCESS.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.info(f"Error: {response_data['message']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                'error': serializer.errors,
                'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        
    def destroy(self, request, uuid=None, *args, **kwargs):
        user = self.get_queryset().filter(id=uuid).first()
        self.check_object_permissions(request, user)

        if not user:
            response_data={
                'error':"User does not exist",
                'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        else:
            logout_view = LogoutView.as_view()
            logout_request = request._request  # Get the original request object
            logout_response = logout_view(logout_request)

            # Log the response if necessary
            if logout_response.status_code != status.HTTP_200_OK:
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: Failed to logout user", extra={'user_id': user_id})
                return Response({
                    'error': 'Failed to log out the user',
                    'status': ResponseStatus.FAIL.value
                }, status=logout_response.status_code)
            
            user.delete()

            response_data = {
                'result': 'User deleted successfully',
                'status': 'success'
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.info(f"Success: {response_data['result']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, uuid=None, *args, **kwargs):
        try:
            user = self.get_queryset().filter(id=uuid).first()
            self.check_object_permissions(request, user)
            
            if not user:
                response_data={
                    'error':"User does not exist",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
            else:
                for field in ['user_type', 'last_login', 'is_superuser', 'is_staff', 'date_joined',
                      'groups', 'user_permissions', "favorites", "created_at", "saves", "wishlists"]:
                    request.data.pop(field, None)
                
                serializer = self.get_serializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save(updated_at=timezone.now())
                    response_data = {
                        'result': serializer.data,
                        'message':'User updated successfully',
                        'status': ResponseStatus.SUCCESS.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            response_data = {
                'error': 'Given user does not exist',
                'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Create JWT tokens
                refresh = RefreshToken.for_user(user)
                user_data = UserSerializer(user).data

                response_data = {
                    'result': {
                        'user': user_data,
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'message': 'Logged in successfully',
                    'status': ResponseStatus.SUCCESS.value
                }
                logger.info(f"Success: {response_data['message']}")
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                    'error': 'Invalid credentials',
                    'status': ResponseStatus.FAIL.value
                }
                logger.info(f"Error: {response_data['error']}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
                    response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
                    }
                    logger.info(f"Error: {str(response_data['error'])}")
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticatedUser]
    serializer_class = UserLogoutSerializer

    def post(self, request):
        if not request.user.is_authenticated:
                response_data = {
                    'error': 'No user is currently logged in',
                    'status': ResponseStatus.FAIL.value
                }
                logger.info(f"Error: {response_data['error']}")
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserLogoutSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            userid = serializer.validated_data.get('id')

            if str(request.user) != str(userid):
                response_data = {
                    'error': f'User {username} is not logged in',
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            # If authenticated and username matches
            token = request.META.get('HTTP_AUTHORIZATION').split()[1]
            if not token:
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: Token not found", extra={'user_id': user_id})
                return Response({
                    'error': 'Token not found',
                    'status': ResponseStatus.FAIL.value
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if BlacklistedToken.objects.filter(token=token).exists():
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: Token already invalidated", extra={'user_id': user_id})
                    return Response({'error': 'Token is already invalidated','status': ResponseStatus.FAIL.value}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    BlacklistedToken.objects.create(token=token)
                except Exception as e:
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {str(e)}", extra={'user_id': user_id})
                    return Response({'error': str(e), 'status': ResponseStatus.FAIL.value}, status=status.HTTP_400_BAD_REQUEST)

                response_data = {
                    'result': 'Logged out successfully',
                    'status': ResponseStatus.SUCCESS.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.info(f"Success: {response_data['result']}", extra={'user_id': user_id})
                call_command('delete_old_logs')
                return Response(response_data, status=status.HTTP_200_OK)
        else:
                    response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [IsAuthenticatedUser]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
                response_data = {
                    'error': 'User not authenticated',
                    'status': ResponseStatus.FAIL.value
                }
                return Response(response_data, status=status.HTTP_403_FORBIDDEN)
        else:
            # check if incoming access_token is not in blacklist
            access_token = request.META.get('HTTP_AUTHORIZATION').split()[1]
            if not access_token:
                return Response({
                    'error': 'Token not found',
                    'status': ResponseStatus.FAIL.value
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if BlacklistedToken.objects.filter(token=access_token).exists():
                    return Response({'error': 'Token is already invalidated','status': ResponseStatus.FAIL.value}, status=status.HTTP_400_BAD_REQUEST)

            serializer = RefreshTokenSerializer(data=request.data)
            if serializer.is_valid():
                incoming_refresh_token = serializer.validated_data.get('refresh')
                ref_token = RefreshToken(incoming_refresh_token)
                    
                user_id=ref_token["user_id"]
                if str(user_id) != str(request.user):
                    response_data = {
                    'error': 'User not authenticated',
                    'status': ResponseStatus.FAIL.value
                    }
                    return Response(response_data, status=status.HTTP_403_FORBIDDEN)
                    
                user = User.objects.get(id=user_id)
                new_refresh = RefreshToken.for_user(user)
                response_data = {
                    'result': {
                        'accessToken': str(new_refresh.access_token),
                        'refreshToken': str(new_refresh),
                    },
                    'status': ResponseStatus.SUCCESS.value
                }
                #blacklist the previous access token and incoming refresh token
                try:
                    BlacklistedToken.objects.create(token=access_token)
                    BlacklistedToken.objects.create(token=incoming_refresh_token)
                except Exception as e:
                    return Response({'error': str(e),'status': ResponseStatus.FAIL.value}, status=status.HTTP_400_BAD_REQUEST)


                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
                    }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class FavoritesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedUser]
    serializer_class = CollectionSerializer

    def add_favorite(self, request, *args, **kwargs):       
        self.check_object_permissions(request, request.user)

        serializer = CollectionSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                response_data = {
                    "error": "User does not exist",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            favorite_item = serializer.validated_data['pujo_id']

            if favorite_item is None:
                response_data = {
                        "error": "No favorite item provided",
                        'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


            if favorite_item in user.favorites:
                response_data = {
                        'error': f"This pujo is already {user.username}'s favorite",
                        'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:    
                user.favorites.append(favorite_item)
                user.save()
                response_data = {
                        'result': user.favorites,
                        'message':'User Favorite set',
                        'status': ResponseStatus.SUCCESS.value
                    }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    def remove_favorite(self, request, *args, **kwargs):
        self.check_object_permissions(request, request.user)

        serializer = CollectionSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                response_data = {
                    "error": "User does not exist",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
            favorite_item = serializer.validated_data['pujo_id']

            if favorite_item is None:
                response_data = {
                    "error": "No favorite item provided",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
 
            if favorite_item in user.favorites:
                user.favorites.remove(favorite_item)
                user.save()
                response_data = {
                'result': user.favorites,
                'message':'User favorite removed',
                'status': ResponseStatus.SUCCESS.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                    "error": "Favorite item not found",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_data = {
                        'error': serializer.errors,
                        'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

class WishlistViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticatedUser]
        serializer_class = CollectionSerializer

        def add_wishlist(self, request, *args, **kwargs):
            self.check_object_permissions(request, request.user)

            serializer = CollectionSerializer(data=request.data)

            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    response_data = {
                        "error": "User does not exist",
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
                item = serializer.validated_data['pujo_id']

                if item is None:
                    response_data = {
                            "error": "No wishlist item provided",
                            'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                if item in user.wishlist:
                    response_data = {
                            'error': f"This pujo is already {user.username}'s wishlist",
                            'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
                else:    
                    user.wishlist.append(item)
                    user.save()
                    response_data = {
                            'result': user.wishlist,
                            'message':'Item added to user wishlist',
                            'status': ResponseStatus.SUCCESS.value
                        }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                            'error': serializer.errors,
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
            
        def remove_wishlist(self, request, *args, **kwargs):
            self.check_object_permissions(request, request.user)

            serializer = CollectionSerializer(data=request.data)

            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    response_data = {
                        "error": "User does not exist",
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
                item = serializer.validated_data['pujo_id']

                if item is None:
                    response_data = {
                        "error": "No wishlist item provided",
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                if item in user.wishlist:
                    user.wishlist.remove(item)
                    user.save()
                    response_data = {
                    'result': user.wishlist,
                    'message':'Item removed',
                    'status': ResponseStatus.SUCCESS.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    response_data = {
                        "error": "wishlist item not found",
                        'status': ResponseStatus.FAIL.value
                    }
                    user_id = request.user.id if request.user.is_authenticated else None
                    logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            else:
                response_data = {
                            'error': serializer.errors,
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
            
class SaveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedUser]
    serializer_class = CollectionSerializer

    def add_saved(self, request, *args, **kwargs):
        self.check_object_permissions(request, request.user)

        serializer = CollectionSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                response_data = {
                        "error": "User does not exist",
                        'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
            item = serializer.validated_data['pujo_id']

            if item is None:
                response_data = {
                            "error": "No item to save",
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


            if item in user.saves:
                response_data = {
                            'error': f"This pujo is already {user.username}'s saves",
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:    
                user.saves.append(item)
                user.save()
                response_data = {
                            'result': user.saves,
                            'message':'item saved',
                            'status': ResponseStatus.SUCCESS.value
                    }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.info(f"Success: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                            'error': serializer.errors,
                            'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    

    def remove_saved(self, request, *args, **kwargs):
        self.check_object_permissions(request, request.user)

        serializer = CollectionSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                response_data = {
                        "error": "User does not exist",
                        'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
            item = serializer.validated_data['pujo_id']


            if item is None:
                response_data = {
                    "error": "No item to save",
                    'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                
            if item in user.saves:
                user.saves.remove(item)
                user.save()
                response_data = {
                'result': user.saves,
                'message':'Item removed',
                'status': ResponseStatus.SUCCESS.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                "error": "save item not found",
                'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_data = {
                            'error': serializer.errors,
                            'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        
class PandalVisitsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedUser]
    serializer_class = CollectionSerializer

    def add_visits(self, request, *args, **kwargs):
        self.check_object_permissions(request, request.user)

        serializer = CollectionSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                response_data = {
                        "error": "User does not exist",
                        'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
            item = serializer.validated_data['pujo_id']

            if item is None:
                response_data = {
                            "error": "No pandal visits",
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


            if item in user.pandal_visits:
                response_data = {
                            'error': f"This pandal has already been visited by {user.username}",
                            'status': ResponseStatus.FAIL.value
                }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['error']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:    
                user.pandal_visits.append(item)
                user.save()
                response_data = {
                            'result': user.pandal_visits,
                            'message':'pandal visited by user',
                            'status': ResponseStatus.SUCCESS.value
                    }
                user_id = request.user.id if request.user.is_authenticated else None
                logger.error(f"Error: {response_data['message']}", extra={'user_id': user_id})
                return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                            'error': serializer.errors,
                            'status': ResponseStatus.FAIL.value
            }
            user_id = request.user.id if request.user.is_authenticated else None
            logger.error(f"Error: {str(response_data['error'])}", extra={'user_id': user_id})
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)