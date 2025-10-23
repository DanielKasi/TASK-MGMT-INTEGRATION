from typing import Literal
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Q
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from django.db.models import Prefetch
from institution.models import Institution, UserBranch
from datetime import datetime
from utilities.helpers import (
    build_password_link,
    create_and_institution_otp,
    send_otp_to_user,
    send_password_link_to_user,
    verify_otp,
    cleanup_expired_otps,
    send_password_reset_link_to_user,
    create_and_institution_token,
)
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .serializers import (
    CustomUserSerializer,
    LoginRequestSerializer,
    InstitutionUserLoginResponseSerializer,
    RoleSerializer,
    PermissionSerializer,
    PermissionCategorySerializer,
    StaffGroupRoleSerializer,
    StaffGroupSerializer,
    StaffGroupUserSerializer,
    UserOTPVerificationSerializer,
    UserPasswordResetSerializer,
    UserResendOTPVerificationSerializer,
    UserSendForgotPasswordTokenSerializer,
    ResendOTPSerializer,
    ProfileSerializer,
    LogoutRequestSerializer,
    ChangePasswordSerializer,
)
from utilities.sortable_api import SortableAPIMixin
from .models import (
    CustomUser,
    Role,
    Permission,
    PermissionCategory,
    StaffGroup,
    StaffGroupRole,
    StaffGroupUser,
    UserType,
    OTPModel,
    Profile,
)
from institution.serializers import InstitutionWithBranchesSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenRefreshView
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from utilities.pagination import CustomPageNumberPagination
import logging
from utilities.password_validator import validate_password_strength
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
import requests
import secrets
import urllib.parse
from institution.utils import generate_compliant_password
from django.db import transaction
from utilities.helpers import permission_required
from django.utils.decorators import method_decorator
from institution.models import UserBranch


logger = logging.getLogger(__name__)


class CountryListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses={200: {"countries": "array"}},
        description="Retrieve a list of countries.",
        summary="Get countries",
        tags=["Location Management"],
    )
    def get(self, request):
        from django_countries import countries

        country_list = [{"code": code, "name": name} for code, name in countries]
        return Response({"countries": country_list}, status=status.HTTP_200_OK)


class UserListAPIView(APIView, SortableAPIMixin):
    permission_classes = [permissions.AllowAny]
    allowed_ordering_fields = ['fullname', 'created_at', 'email', 'is_active', 'gender']
    default_ordering = ['fullname']

    @extend_schema(
        request=CustomUserSerializer,
        responses={201: CustomUserSerializer},
        description="Register a new user with email, full name, and password.",
        summary="Create a new user",
        tags=["User Management"],
    )
    def post(self, request):

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():

            user = serializer.save()

            otp = create_and_institution_otp(
                user_id=user.id, purpose=f"registration_{user.id}", expiry_minutes=15
            )

            send_otp_to_user(user, otp)

            cleanup_expired_otps()

            return Response(
                CustomUserSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


    @extend_schema(
        responses={200: CustomUserSerializer(many=True)},
        description="Retrieve the authenticated user's details.",
        summary="Get user details",
        tags=["User Management"],
    )
    def get(self, request):
        try:
            user_institution = request.user.profile.institution
        except Profile.DoesNotExist:
            return Response(
                {"error": "Logged-in user does not have a profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = CustomUser.objects.filter(
            profile__institution=user_institution
        )

        queryset = queryset.prefetch_related(
            "user_roles__role__permissions__permission",
            Prefetch(
                "attached_branches",
                queryset=UserBranch.objects.select_related("branch__institution"),
                to_attr="prefetched_user_branches",
            ),
        )

        try:
            queryset = self.apply_sorting(queryset, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_users = paginator.paginate_queryset(queryset, request)
        serializer = CustomUserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)

class ChangePasswordAPIView(APIView):
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: {"description": "Password changed successfully"}},
        description="Change the authenticated user's password.",
        summary="Change password",
        tags=["User Management"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class ChangeEmailAndResendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "old_email": {"type": "string", "format": "email"},
                "new_email": {"type": "string", "format": "email"},
            },
            "required": ["old_email", "new_email"],
        },
        responses={
            200: {"message": "string"},
            400: {"detail": "string"},
            404: {"detail": "string"},
        },
        description="Change user email and resend OTP for registration verification",
        summary="Change email and resend OTP",
        tags=["User Management"],
    )
    def post(self, request):
        old_email = request.data.get("old_email")
        new_email = request.data.get("new_email")

        if not old_email or not new_email:
            return Response(
                {"error": "Both old_email and new_email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_email == new_email:
            return Response(
                {"error": "New email must be different from the old email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = CustomUser.objects.get(email=old_email)
            if CustomUser.objects.filter(email=new_email).exists():
                return Response(
                    {"error": "New email is already in use"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.email = new_email
            user.save()

            otp = create_and_institution_otp(
                user_id=user.id, purpose=f"registration_{user.id}", expiry_minutes=15
            )

            send_otp_to_user(user, otp)

            cleanup_expired_otps()

            logger.info(f"Email changed for user {user.id} from {old_email} to {new_email}, OTP resent")
            return Response(
                {"message": f"OTP sent to new email: {new_email}"},
                status=status.HTTP_200_OK,
            )

        except CustomUser.DoesNotExist:
            logger.error(f"User with email {old_email} not found during email change")
            return Response(
                {"error": "User with old email not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error during email change for user with email {old_email}: {str(e)}")
            return Response(
                {"error": "An error occurred during email change"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )        


class UserDetailAPIView(APIView):
    @extend_schema(
        responses={200: CustomUserSerializer},
        description="Retrieve a specific user's details.",
        summary="Get user details",
        tags=["User Management"],
    )
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = CustomUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=CustomUserSerializer(partial=True),
        responses={200: CustomUserSerializer},
        description="Update the authenticated user's details (partial update).",
        summary="Update user details",
        tags=["User Management"],
    )
    def patch(self, request, user_id):
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                serializer = CustomUserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "message": "User updated successfully",
                            "user": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {"error": "User ID is required for updating."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        responses={204: None},
        description="Delete a specific user.",
        summary="Delete user",
        tags=["User Management"],
    )
    def delete(self, request, user_id):
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.delete()
                return Response(
                    {"message": "User deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {"error": "User ID is required for deletion."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerifyOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserOTPVerificationSerializer,
        responses={200: {"message": "string"}},
        description="Verify OTP for user registration",
        tags=["User Management"],
    )
    def post(self, request):
        serializer = UserOTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = CustomUser.objects.get(email=email)

            success, message = verify_otp(user.id, received_otp=otp)

            if success:
                user.is_active = True
                user.is_email_verified = True
                user.is_staff = True
                user.save()

                logger.info(f"User {user.id} verified and activated successfully")
                return Response(
                    {"message": "OTP verified successfully. Account activated."},
                    status=status.HTTP_200_OK,
                )
            else:
                logger.warning(f"OTP verification failed for user {user.id}: {message}")
                return Response(
                    {"message": message}, status=status.HTTP_400_BAD_REQUEST
                )

        except CustomUser.DoesNotExist:
            logger.error(f"User {user.id} not found during OTP verification")
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error during OTP verification for user {user.id}: {str(e)}")
            return Response(
                {"error": "An error occurred during verification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )





class ResendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserResendOTPVerificationSerializer,
        responses={200: {"message": "string"}},
        description="Resend email OTP for user registration",
        tags=["User Management"],
    )
    def post(self, request):
        mode: Literal["otp", "password_link"] = request.query_params.get("mode", "otp")
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        try:

            email = serializer.validated_data["email"]
            user_instance = CustomUser.objects.get(email=email)
            otp = create_and_institution_otp(
                user_id=user_instance.id, purpose="registration", expiry_minutes=15
            )
            if mode == "otp":
                send_otp_to_user(user_instance, otp)
            else:
                token = create_and_institution_token(
                    user=user_instance.profile.user,
                    purpose="registration",
                    expiry_minutes=15,
                )
                password_link = build_password_link(request=request, token=token)
                send_password_link_to_user(user=user_instance, link=password_link)

            return Response(
                CustomUserSerializer(user_instance).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": "Could not send the OTP"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginRequestSerializer,
        responses={200: InstitutionUserLoginResponseSerializer},
        description="Authenticate user to receive JWT tokens and user details.",
        summary="User Login",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user_instance = CustomUser.objects.get(email=email)
                # The custom_codes are in sync with the frontend, they should be kept so or modified together
                if (
                    not user_instance.is_password_verified
                    and not user_instance.is_email_verified
                ):
                    return Response(
                        {
                            "error": "You need to reset your password to be able to login, custom_code: ADMIN_CREATED_UNVERIFIED"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if not user_instance.is_email_verified:
                    return Response(
                        {
                            "error": "You need to verify your account to be able to login, custom_code: SELF_CREATED_UNVERIFIED"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                user = authenticate(email=user_instance.email, password=password)

                if user is not None:
                    if user.user_type == UserType.STAFF:
                        institution_attached = user.institutions_owned.all()

                        # If user is not an institution owner, check if they are associated with an institution in profile
                        if not institution_attached:
                            try:
                                institution_attached = (
                                    [user.profile.institution]
                                    if user.profile.institution
                                    else []
                                )
                            except ObjectDoesNotExist:
                                institution_attached = (
                                    []
                                    if not institution_attached
                                    else institution_attached
                                )

                        serializer_context = {"user": user}

                        return Response(
                            {
                                "tokens": user.get_token(),
                                "user": CustomUserSerializer(user).data,
                                "institution_attached": InstitutionWithBranchesSerializer(
                                    institution_attached,
                                    many=True,
                                    context=serializer_context,
                                ).data,
                            },
                            status=status.HTTP_200_OK,
                        )
                return Response(
                    {
                        "error": "Invalid Credentials, custom_code: INVALID_CREDENTIALS"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except CustomUser.DoesNotExist:
                return Response(
                    {
                        "error": "Invalid Credentials, custom_code: INVALID_CREDENTIALS"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class UserInstitutionsListAPIView(APIView):
    def get(self, request):
        try:
            user = request.user

            if not user:
                return Response(status=status.HTTP_403_FORBIDDEN)
            institution_attached = user.institutions_owned.all()

            if not institution_attached or not len(institution_attached):
                try:
                    institution_attached = (
                        [user.profile.institution] if user.profile.institution else []
                    )
                except ObjectDoesNotExist:
                    institution_attached = (
                        [] if not institution_attached else institution_attached
                    )

            serializer = InstitutionWithBranchesSerializer(
                institution_attached,
                many=True,
                context={"user": user},
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        refresh_token = serializer.validated_data.get("refresh")
        access_token = serializer.validated_data.get("access")

        try:
            token = RefreshToken(refresh_token)
            user_id = token.payload.get("user_id")

            user = CustomUser.objects.get(id=user_id)
            if user.user_type == UserType.STAFF:
                response_data = {
                    "tokens": {
                        "access": str(access_token),
                        "refresh": str(refresh_token),
                    },
                    "user": CustomUserSerializer(user).data,
                    "institution_attached": InstitutionWithBranchesSerializer(
                        user.institutions_owned.all(), many=True, context={"user": user}
                    ).data,
                }
            else:
                return Response(
                    {"error": "Invalid user type."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(response_data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Token refresh failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RoleListAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = ['name', 'created_at', 'is_active']
    default_ordering = ['name']
    @extend_schema(
        request=RoleSerializer,
        responses={201: RoleSerializer},
        description="Create a new role.",
        summary="Create a new role",
        tags=["User Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer: RoleSerializer = RoleSerializer(data=request.data)

        if serializer.is_valid():
            role = serializer.save()
            role.confirm_create()
            return Response(
                RoleSerializer(role).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: RoleSerializer(many=True)},
        description="Retrieve all roles.",
        summary="Get all roles",
        tags=["User Management"],
    )
    def get(self, request):
        Institution_id = request.query_params.get("Institution_id", None)
        roles = Role.objects.filter(institution__id=Institution_id).order_by(
            "-created_at"
        )
        try:
            roles = self.apply_sorting(roles, request)
        except ValueError as e:
            return Response ({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)    
        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(roles, request)
        serializer = RoleSerializer(
            paginator_qs, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)


class RoleDetailAPIView(APIView):
    @extend_schema(
        responses={200: RoleSerializer},
        summary="Get a role",
        tags=["User Management"],
    )
    def get(self, request, role_id):
        role = get_object_or_404(Role, pk=role_id)
        serializer = RoleSerializer(role)
        return Response(serializer.data)

    @extend_schema(
        request=RoleSerializer,
        responses={200: RoleSerializer},
        summary="Update a role",
        tags=["User Management"],
    )
    @transaction.atomic()
    def patch(self, request, role_id):
        role = get_object_or_404(Role, pk=role_id)
        role.approval_status = 'under_update'
        serializer = RoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            role.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        summary="Delete a role",
        tags=["User Management"],
    )
    def delete(self, request, role_id):
        role = get_object_or_404(Role, pk=role_id)
        role.approval_status = 'under_deletion'
        role.save(update_fields=['approval_status'])
        role.confirm_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionCategoryListAPIView(APIView):
    @extend_schema(
        request=PermissionSerializer,
        responses={201: PermissionSerializer},
        description="Create a new permission Category.",
        summary="Create a new permission Category",
        tags=["User Management"],
    )
    def post(self, request):
        serializer: PermissionCategorySerializer = PermissionCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():
            permission_category = serializer.save()
            return Response(
                PermissionCategorySerializer(permission_category).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: PermissionCategorySerializer(many=True)},
        description="Retrieve all permission categories.",
        summary="Retrieve all permission categories",
        tags=["User Management"],
    )
    def get(self, request):
        permission_categories = PermissionCategory.objects.all().order_by("-created_at")
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(permission_categories, request)
        serializer = PermissionCategorySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class PermissionCategoryDetailAPIView(APIView):
    @extend_schema(
        responses={200: PermissionCategorySerializer},
        summary="Get a permission category",
        tags=["User Management"],
    )
    def get(self, request, permission_category_id):
        role = get_object_or_404(PermissionCategory, pk=permission_category_id)
        serializer = PermissionCategorySerializer(role)
        return Response(serializer.data)

    @extend_schema(
        request=PermissionCategorySerializer,
        responses={200: PermissionCategorySerializer},
        summary="Update a permission category",
        tags=["User Management"],
    )
    def patch(self, request, permission_category_id):
        role = get_object_or_404(PermissionCategory, pk=permission_category_id)
        serializer = PermissionCategory(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        summary="Delete a permission category",
        tags=["User Management"],
    )
    def delete(self, request, permission_category_id):
        permission_category = get_object_or_404(PermissionCategory, pk=permission_category_id)
        permission_category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionListAPIView(APIView):
    @extend_schema(
        request=PermissionSerializer,
        responses={201: PermissionSerializer},
        description="Create a new permission.",
        summary="Create a new permission",
        tags=["User Management"],
    )
    def post(self, request):
        serializer: PermissionSerializer = PermissionSerializer(data=request.data)

        if serializer.is_valid():
            permission = serializer.save()
            return Response(
                PermissionSerializer(permission).data, status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: PermissionSerializer(many=True)},
        description="Retrieve all permissions.",
        summary="Retrieve all permissions",
        tags=["User Management"],
    )
    def get(self, request):
        system_permissions = Permission.objects.all()
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(system_permissions, request)
        serializer = PermissionSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class PermissionDetailAPIView(APIView):
    @extend_schema(
        responses={200: PermissionSerializer},
        summary="Get a permission",
        tags=["User Management"],
    )
    def get(self, request, permission_id):
        role = get_object_or_404(Permission, pk=permission_id)
        serializer = PermissionSerializer(role)
        return Response(serializer.data)

    @extend_schema(
        request=PermissionSerializer,
        responses={200: PermissionSerializer},
        summary="Update a permission",
        tags=["User Management"],
    )
    def patch(self, request, permission_id):
        role = get_object_or_404(Permission, pk=permission_id)
        serializer = PermissionSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        summary="Delete a permission",
        tags=["User Management"],
    )
    def delete(self, request, permission_id):
        permission = get_object_or_404(Permission, pk=permission_id)
        permission.delete
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserSendForgotPasswordTokenSerializer,
        responses={200: {"detail": "string"}},
        description="Request a password reset link",
        summary="Forgot Password",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = UserSendForgotPasswordTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"].lower()
        frontend_url = serializer.validated_data.get("frontend_url")

        # user = get_object_or_404(CustomUser, email=email)
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            return Response(
                {"error": "No user found with this email address."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Generate token
            token = create_and_institution_token(
                user=user, purpose="password_reset", expiry_minutes=1440
            )

            # Build reset link
            reset_link = f"{frontend_url}/forgot-password/reset-password/{token}"

            # Send reset email
            send_password_reset_link_to_user(user=user, link=reset_link)

            return Response(
                {"error": "Password reset link sent successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error in forgot password: {str(e)}")
            return Response(
                {"error": "An error occurred while processing your request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyTokenAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={"token": "string"},
        responses={200: {"valid": "boolean"}},
        description="Verify if a password reset token is valid",
        summary="Verify Reset Token",
        tags=["Authentication"],
    )
    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if token exists and is not expired
            token_obj = OTPModel.objects.filter(
                value=token,
                purpose="password_reset",
                is_used=False,
                expires_at__gt=timezone.now(),
            ).first()

            return Response({"valid": bool(token_obj)}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in verify token: {str(e)}")
            return Response(
                {"error": "An error occurred while verifying the token."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResetPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserPasswordResetSerializer,
        responses={200: {"detail": "string"}},
        description="Reset password using token",
        summary="Reset Password",
        tags=["Authentication"],
    )
    def post(self, request):
        
        serializer = UserPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            # Validate password
            try:
                validate_password_strength(new_password)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Find token
            token_obj = OTPModel.objects.filter(
                value=token,
                purpose="registration",
                is_used=False,
                expires_at__gt=timezone.now(),
            ).first()

            if not token_obj:
                return Response(
                    {"error": "Invalid or expired token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set new password
            user = token_obj.user
            user.set_password(new_password)
            user.is_password_verified = True
            user.is_email_verified = True
            user.save()

            # Mark token as used
            token_obj.is_used = True
            token_obj.save()

            # Mark token as used
            logger.info(f"Password reset successful for user {user.id}")
            return Response(
                {"error": "Password has been reset successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in reset password: {str(e)}")
            return Response(
                {"error": "An error occurred while resetting your password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GoogleAuthURLView(APIView):
    """
    Generate Google OAuth URL for frontend to redirect to
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)

        # Store state in cache for 10 minutes (you can also use sessions)
        cache.set(f"google_oauth_state_{state}", True, timeout=600)

        # Build Google OAuth URL
        params = {
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_AUTH_REDIRECT_URL,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

        return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)


class GoogleAuthCallbackView(APIView):
    """
    Handle Google OAuth callback and authenticate user
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        state = request.data.get("state")

        if not code or not state:
            return Response(
                {
                    "error": "Code and state are required, custom_code: MISSING_PARAMS"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_AUTH_REDIRECT_URL,
            }

            token_response = requests.post(token_url, data=token_data)
            token_json = token_response.json()

            if "error" in token_json:
                return Response(
                    {
                        "error": f"Google token exchange failed: {token_json.get('error_description', 'Unknown error')} custom_code: GOOGLE_TOKEN_EXCHANGE_FAILED"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            access_token = token_json.get("access_token")

            user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            user_response = requests.get(user_info_url)

            user_data = user_response.json()

            if "error" in user_data:
                return Response(
                    {
                        "error": "Failed to get user info from Google, custom_code: GOOGLE_USER_INFO_FAILED"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            email = user_data.get("email")
            fullname = user_data.get("name", "")

            if not email:
                return Response(
                    {
                        "error": "Email not provided by Google, custom_code: NO_EMAIL_FROM_GOOGLE"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = CustomUser.objects.get(email=email)

            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    email=email,
                    fullname=fullname,
                    is_active=True,
                    user_type=UserType.STAFF,
                    is_email_verified=True,
                    is_password_verified=True,
                    password=generate_compliant_password(),
                )

            user_profile, _ = Profile.objects.get_or_create(user=user)

            return Response(
                {
                    "tokens": user.get_token(),
                    "user": ProfileSerializer(user_profile).data,
                    "message": "User authenticated successfully",
                },
                status=status.HTTP_200_OK,
            )

        except requests.RequestException as e:
            return Response(
                {"error": f"Network error: {str(e)}", "custom_code": "NETWORK_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {
                    "error": f"Authentication failed: {str(e)}, custom_code: AUTH_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserDetailsWithInstitutions(APIView):
    """
    Returns the same response as the login endpoint for an authenticated user.
    """

    def get(self, request):
        user = request.user

        if user.user_type == UserType.STAFF:
            institution_attached = user.institutions_owned.all()

            if not institution_attached:
                try:
                    institution_attached = (
                        [user.profile.institution] if user.profile.institution else []
                    )
                except ObjectDoesNotExist:
                    institution_attached = []

            serializer_context = {"user": user}

            return Response(
                {
                    "user": CustomUserSerializer(user).data,
                    "institution_attached": InstitutionWithBranchesSerializer(
                        institution_attached,
                        many=True,
                        context=serializer_context,
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "error": "Only staff users are supported in this endpoint, custom_code:UNSUPPORTED_USER_TYPE."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

class LogoutView(APIView):
    @extend_schema(
        request=LogoutRequestSerializer,
        responses={205: None},
        description="Invalidate the refresh token to log out the user.",
        summary="User Logout",
        tags=["Authentication"],
    )   
    def post(self, request):
        serializer = LogoutRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh']
                UntypedToken(refresh_token)
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"error": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
            except (InvalidToken, TokenError) as e:
                return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     


class StaffGroupListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['name', 'created_at']
    default_ordering = ['name']

    @extend_schema(
        request=StaffGroupSerializer,
        responses={
            201: OpenApiResponse(
                response=StaffGroupSerializer,
                description="Staff group created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_create_staff_groups'))
    @transaction.atomic()
    def post(self, request):
        serializer = StaffGroupSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by name or description"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=StaffGroupSerializer(many=True),
                description="List of staff groups.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_view_staff_groups'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        groups = StaffGroup.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if search_query:
            groups = groups.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if created_at:
            groups = groups.filter(created_at=created_at)

        try:
            groups = self.apply_sorting(groups, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(groups, request)
        serializer = StaffGroupSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

class StaffGroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user_institution):
        return get_object_or_404(
            StaffGroup,
            pk=pk,
            institution=user_institution,
            deleted_at__isnull=True
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StaffGroupSerializer,
                description="Staff group retrieved successfully.",
            ),
            404: OpenApiResponse(description="Staff group not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_view_staff_groups'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group = self.get_object(pk, institution)
        serializer = StaffGroupSerializer(group)
        return Response(serializer.data)

    @extend_schema(
        request=StaffGroupSerializer,
        responses={
            200: OpenApiResponse(
                response=StaffGroupSerializer,
                description="Staff group updated successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
            404: OpenApiResponse(description="Staff group not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_edit_staff_groups'))
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group = self.get_object(pk, institution)
        serializer = StaffGroupSerializer(
            group, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Staff group deleted successfully."),
            404: OpenApiResponse(description="Staff group not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_delete_staff_groups'))
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group = self.get_object(pk, institution)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        

class StaffGroupRoleListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['group__name', 'role__name', 'created_at']
    default_ordering = ['group__name']

    @extend_schema(
        request=StaffGroupRoleSerializer,
        responses={
            201: OpenApiResponse(
                response=StaffGroupRoleSerializer,
                description="Staff group role assignment created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Staff Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = StaffGroupRoleSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by group name or role name"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'group__name,-role__name,created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=StaffGroupRoleSerializer(many=True),
                description="List of staff group role assignments.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_view_staff_roles'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        group_roles = StaffGroupRole.objects.filter(
            group__institution=institution, deleted_at__isnull=True
        )

        if search_query:
            group_roles = group_roles.filter(
                Q(group__name__icontains=search_query) |
                Q(role__name__icontains=search_query)
            )

        if created_at:
            group_roles = group_roles.filter(created_at=created_at)

        try:
            group_roles = self.apply_sorting(group_roles, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(group_roles, request)
        serializer = StaffGroupRoleSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class StaffGroupRoleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user_institution):
        return get_object_or_404(
            StaffGroupRole,
            pk=pk,
            group__institution=user_institution,
            deleted_at__isnull=True
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StaffGroupRoleSerializer,
                description="Staff group role assignment retrieved successfully.",
            ),
            404: OpenApiResponse(description="Staff group role assignment not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_view_staff_roles'))  
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_role = self.get_object(pk, institution)
        serializer = StaffGroupRoleSerializer(group_role)
        return Response(serializer.data)

    @extend_schema(
        request=StaffGroupRoleSerializer,
        responses={
            200: OpenApiResponse(
                response=StaffGroupRoleSerializer,
                description="Staff group role assignment updated successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
            404: OpenApiResponse(description="Staff group role assignment not found."),
        },
        tags=["Staff Management"],
    )
    @method_decorator(permission_required('can_edit_staff_roles'))
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_role = self.get_object(pk, institution)
        serializer = StaffGroupRoleSerializer(
            group_role, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Staff group role assignment deleted successfully."),
            404: OpenApiResponse(description="Staff group role assignment not found."),
        },
        tags=["Staff Management"],
    )
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_role = self.get_object(pk, institution)
        group_role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

class StaffGroupUserListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['group__name', 'user__fullname', 'created_at']
    default_ordering = ['group__name']

    @extend_schema(
        request=StaffGroupUserSerializer,
        responses={
            201: OpenApiResponse(
                response=StaffGroupUserSerializer,
                description="Staff group user assignment created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Staff Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = StaffGroupUserSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by group name or user fullname"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'group__name,-user__fullname,created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=StaffGroupUserSerializer(many=True),
                description="List of staff group user assignments.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Staff Management"],
    )
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        group_users = StaffGroupUser.objects.filter(
            group__institution=institution, deleted_at__isnull=True
        )

        if search_query:
            group_users = group_users.filter(
                Q(group__name__icontains=search_query) |
                Q(user__fullname__icontains=search_query)
            )

        if created_at:
            group_users = group_users.filter(created_at=created_at)

        try:
            group_users = self.apply_sorting(group_users, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(group_users, request)
        serializer = StaffGroupUserSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class StaffGroupUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user_institution):
        return get_object_or_404(
            StaffGroupUser,
            pk=pk,
            group__institution=user_institution,
            deleted_at__isnull=True
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StaffGroupUserSerializer,
                description="Staff group user assignment retrieved successfully.",
            ),
            404: OpenApiResponse(description="Staff group user assignment not found."),
        },
        tags=["Staff Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_user = self.get_object(pk, institution)
        serializer = StaffGroupUserSerializer(group_user)
        return Response(serializer.data)

    @extend_schema(
        request=StaffGroupUserSerializer,
        responses={
            200: OpenApiResponse(
                response=StaffGroupUserSerializer,
                description="Staff group user assignment updated successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
            404: OpenApiResponse(description="Staff group user assignment not found."),
        },
        tags=["Staff Management"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_user = self.get_object(pk, institution)
        serializer = StaffGroupUserSerializer(
            group_user, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Staff group user assignment deleted successfully."),
            404: OpenApiResponse(description="Staff group user assignment not found."),
        },
        tags=["Staff Management"],
    )
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_user = self.get_object(pk, institution)
        group_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    
class BranchUsersView(APIView):
    @extend_schema(
        responses={200: CustomUserSerializer(many=True)},
        description="Retrieve users that belong under same branch as the logged in user",
        summary="Get users under the same branch as the logged in user.",
        tags=["User Management"],
    )
    def get(self, request, pk):
        
        try:
            user = CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist as e:
            return Response(
                {"error": "User with this id does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # handle case for user who is an institution owner

        institutions_owned = user.institutions_owned.all()
        if institutions_owned:
            branch_ids = []
            for institution in institutions_owned:
                # Get all branches
                branches = institution.branches.all()
                for branch in branches:
                    branch_ids.append(branch.id)
        else:
            branch_ids = UserBranch.objects.filter(user=user).values_list("branch_id", flat=True)

        if not branch_ids:
            return Response({"error": "User is not assigned to any branch."},status=status.HTTP_404_NOT_FOUND)

        # Get all users in the same branches
        user_ids = UserBranch.objects.filter(branch_id__in=branch_ids).values_list("user_id", flat=True)
        
        users_in_same_branch = CustomUser.objects.filter(Q(id__in=user_ids) | Q(id=user.id))
        paginator = CustomPageNumberPagination()
        paginated_users = paginator.paginate_queryset(users_in_same_branch, request)
        serializer = CustomUserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)