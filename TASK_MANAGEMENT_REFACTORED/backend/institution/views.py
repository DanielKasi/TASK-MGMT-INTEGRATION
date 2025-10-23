from django.http import Http404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.http import HttpResponseRedirect
from utilities.helpers import (
    build_password_link,
    send_password_link_to_user,
    create_and_institution_token,
    send_activation_confirmation_email,
)
from users.models import CustomUser, Profile

from .models import (
    Department,
    Institution,
    Branch,
    UserBranch,
    InstitutionBankAccount,
    InstitutionBankType,
    InstitutionWorkingDays,
    InstitutionKYCDocument,
    BranchWorkingDays,
)
from users.serializers import CustomUserSerializer, ProfileSerializer
from .serializers import (
    DepartmentSerializer,
    InstitutionSerializer,
    BranchSerializer,
    UserBranchSerializer,
    InstitutionBankTypeSerializer,
    InstitutionBankAccountSerializer,
    InstitutionWorkingDaysSerializer,
    InstitutionKYCDocumentSerializer,
    InstitutionKYCDocumentBulkCreateSerializer,
    BranchWorkingDaysSerializer,
    AIQuerySerializer,
    UserChatsSerializer,
)
from django.shortcuts import get_object_or_404
from .utils import add_message, generate_compliant_password, get_messages
from utilities.pagination import CustomPageNumberPagination
from django.db.models import Count, Sum, Q, F
from django.contrib.auth import get_user_model
import logging
from django.db import transaction
import uuid
from decimal import Decimal
from django.utils import timezone
from rest_framework import parsers
from utilities.sortable_api import SortableAPIMixin
from ai_assistant.query_runner import run_sql_with_retry
from ai_assistant.query_generator import generate_sql_from_question
from ai_assistant.result_interpreter import interpret_sql_results_with_groq
from ai_assistant.utils import (
    classify_intent_groq,
    map_permission_based_on_question,
    user_has_permission,
)
from .utils import _load_user_file, load_db_rules
from utilities.helpers import permission_required
from django.utils.decorators import method_decorator

User = get_user_model()
logger = logging.getLogger(__name__)


def home(request):
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}")


class UserChatsView(APIView):

    @extend_schema(
        responses={
            200: UserChatsSerializer,
            400: {"description": "Bad Request"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
            500: {"description": "Internal Server Error"},
        },
        summary="AI USER CHATS",
        tags=["Complete AI Assistant"],
    )
    def get(self, request):
        user_id = request.user.id

        try:
            user_data = _load_user_file(user_id)

            sorted_chats = sorted(
                user_data["chats"],
                key=lambda chat: max(msg["timestamp"] for msg in chat["messages"]),
                reverse=True,
            )
            user_data["chats"] = sorted_chats

            serializer = UserChatsSerializer(user_data)
            return Response(serializer.data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AIAssistantView(APIView):
    """
    AI Assistant for natural language Task queries.
    Accepts a question from an authenticated user,
    generates SQL, executes it, and returns a human-readable interpretation.
    """

    @extend_schema(
        request=AIQuerySerializer,
        responses={
            200: AIQuerySerializer,
            400: {"description": "Bad Request"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
            500: {"description": "Internal Server Error"},
        },
        description="Ask a Task question and get an AI-generated answer.",
        summary="AI Task Query Assistant",
        tags=["AI Assistant"],
    )
    def post(self, request, *args, **kwargs):
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data["question"]
        chat_id = serializer.validated_data.get("chat_id")
        user = request.user

        try:
            profile = Profile.objects.select_related("institution").get(user=user)
            institution = profile.institution
        except Profile.DoesNotExist:
            return Response(
                {"error": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not chat_id:
            chat_id = str(uuid.uuid4())

        try:
            intent = classify_intent_groq(question)
        except Exception as e:
            return Response(
                {
                    "error": f"Intent classification failed: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        record = add_message(user.id, "user", question, chat_id)

        recent_chats = get_messages(user.id, chat_id, limit=10)

        if intent == "GREETING":
            greeting_response = (
                "Hello! 👋 I'm here to help with Task questions. "
                "You can ask me things like:\n"
                "- What were the total employee headcount last month?\n"
                "- Which departments are low on staff?\n"
                "- Show top-performing employees this quarter.\n"
                "- How many leave applications did we get last week?\n"
                "- What's the salary distribution by department?"
            )

            add_message(user.id, "assistant", greeting_response, record)

            return Response(
                {
                    "answer": greeting_response,
                    "chat_id": chat_id,
                },
                status=status.HTTP_200_OK,
            )

        elif intent == "FEATURE_INQUIRY":
            feature_response = "This feature is currently under development. Please stay tuned for upcoming updates!"

            add_message(user.id, "assistant", feature_response, record)

            return Response(
                {
                    "answer": feature_response,
                    "chat_id": chat_id,
                },
                status=status.HTTP_200_OK,
            )

        elif intent == "TASK_QUERY":
            mapped_permission = map_permission_based_on_question(question)

            if mapped_permission and mapped_permission != "none":
                user_has_access = user_has_permission(
                    user, mapped_permission, institution.id
                )

                if user_has_access:

                    if not institution:
                        return Response(
                            {"error": "You are not assigned to any institution."},
                            status=status.HTTP_403_FORBIDDEN,
                        )

                    institution_id = institution.id

                    try:
                        schema = load_db_rules("db_schema.txt")

                        initial_sql = generate_sql_from_question(
                            schema, question, institution_id, recent_chats
                        )

                        sql_result = run_sql_with_retry(
                            schema=schema,
                            question=question,
                            institution_id=institution_id,
                            initial_sql=initial_sql,
                            recent_chats=recent_chats,
                        )

                        interpretation, links = interpret_sql_results_with_groq(
                            question=question,
                            columns=sql_result["columns"],
                            rows=sql_result["results"],
                            recent_chats=recent_chats,
                            sql=sql_result["sql"],
                        )

                        add_message(user.id, "assistant", interpretation, record)

                        return Response(
                            {
                                "answer": interpretation,
                                "chat_id": chat_id,
                                "link": links,
                            },
                            status=status.HTTP_200_OK,
                        )

                    except Exception as e:
                        error_message = f"Something went wrong: {str(e)}"

                        add_message(user.id, "assistant", error_message, chat_id)

                        return Response(
                            {
                                "error": f"Something went wrong: {str(e)}, answer: {error_message}, chat_id: {chat_id}"
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                else:
                    error_message = "You don't have access to this resource."

                    add_message(user.id, "assistant", error_message, chat_id)

                    return Response(
                        {
                            "answer": error_message,
                            "chat_id": chat_id,
                        },
                        status=status.HTTP_200_OK,
                    )
            else:
                error_message = "No Permission Found or Mapped"

                add_message(user.id, "assistant", error_message, chat_id)

                return Response(
                    {
                        "error": f"Something went wrong: {str(e)}, answer: {error_message}, chat_id: {chat_id}"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:
            fallback_msg = (
                "Sorry, I can only help with Human Resource based questions. "
                "Please ask about employee management, attendance, payroll, or benefits."
            )

            add_message(user.id, "assistant", fallback_msg, record)

            return Response(
                {
                    "answer": fallback_msg,
                    "chat_id": chat_id,
                },
                status=status.HTTP_200_OK,
            )





class BranchWorkingDaysListAPIView(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=BranchWorkingDaysSerializer,
                description="Working days for the specified branch.",
            ),
            400: OpenApiResponse(
                description="Branch ID required or working days not found."
            ),
            404: OpenApiResponse(description="Branch not found."),
        },
        description="Retrieve working days for a branch.",
        summary="Get working days for a branch",
        tags=["Branch Working Days Management"],
    )
    def get(self, request):
        branch_id = request.query_params.get("branch_id")

        if not branch_id:
            return Response(
                {"error": "Branch ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            branch = Branch.objects.get(id=int(branch_id))
        except Branch.DoesNotExist:
            return Response(
                {"error": "Branch with ID not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            working_days = BranchWorkingDays.objects.get(branch=branch)
            serializer = BranchWorkingDaysSerializer(working_days)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BranchWorkingDays.DoesNotExist:
            return Response(
                {
                    "error": "Working days for the given branch not found. Try creating them."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        request=BranchWorkingDaysSerializer,
        responses={201: BranchWorkingDaysSerializer},
        description="Create a new working days configuration for a branch.",
        summary="Create working days on a branch level",
        tags=["Branch Working Days Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = BranchWorkingDaysSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            working_days = serializer.save()
            working_days.confirm_create()
            return Response(
                BranchWorkingDaysSerializer(working_days).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class BranchWorkingDaysDetailView(APIView):
    @extend_schema(
        request=BranchWorkingDaysSerializer,
        responses={200: BranchWorkingDaysSerializer},
        description="Update the existing Branch Working Days.",
        summary="Update branch working days",
        tags=["Branch Working Days Management"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        try:
            branch_working_days = BranchWorkingDays.objects.get(id=pk)
        except BranchWorkingDays.DoesNotExist:
            return Response(
                {"error": "Working days configuration not found."}, status=404
            )

        branch_working_days.approval_status = "under_update"

        serializer = BranchWorkingDaysSerializer(
            branch_working_days, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            branch_working_days.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class InstitutionKYCDocumentListCreateView(APIView, SortableAPIMixin):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    allowed_ordering_fields = ["document_title", "created_at", "is_active"]
    default_ordering = ["document_title"]

    @extend_schema(
        request=InstitutionKYCDocumentBulkCreateSerializer,
        responses=InstitutionKYCDocumentBulkCreateSerializer,
        description="Create a new KYC document for an institution",
        summary="Create KYC Document",
        tags=["KYC Documents Management"],
    )
    def post(self, request):
        serializer = InstitutionKYCDocumentBulkCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            documents = serializer.save()
            return Response(
                InstitutionKYCDocumentSerializer(documents, many=True).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: InstitutionKYCDocumentSerializer},
        description="Retrieve all KYC documents for an institution",
        summary="Get KYC Documents",
        tags=["KYC Documents Management"],
    )
    def get(self, request):
        user = request.user.profile if request.user.is_authenticated else None

        institution = user.institution

        kyc_documents = InstitutionKYCDocument.objects.filter(institution=institution)

        try:
            kyc_documents = self.apply_sorting(kyc_documents, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(kyc_documents, request)
        serializer = InstitutionKYCDocumentSerializer(paginator_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class InstitutionKYCDocumentDetailView(APIView):
    @extend_schema(
        responses={200: InstitutionKYCDocumentSerializer},
        tags=["KYC Documents Management"],
        summary="Get KYC Document Detail",
    )
    def get(self, request, document_id):
        document = get_object_or_404(InstitutionKYCDocument, id=document_id)
        serializer = InstitutionKYCDocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=InstitutionKYCDocumentSerializer,
        responses={200: InstitutionKYCDocumentSerializer},
        tags=["KYC Documents Management"],
        summary="Update KYC Document",
    )
    def patch(self, request, document_id):
        document = get_object_or_404(InstitutionKYCDocument, id=document_id)
        serializer = InstitutionKYCDocumentSerializer(
            document, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=InstitutionKYCDocumentSerializer,
        responses={200: InstitutionKYCDocumentSerializer},
        tags=["KYC Documents Management"],
        summary="Delete KYC Document",
    )
    def delete(self, request, document_id):
        document = get_object_or_404(InstitutionKYCDocument, id=document_id)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstitutionListAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=InstitutionSerializer,
        responses={201: InstitutionSerializer},
        description="Create a new institution with name, address, owner, and optional departments",
        summary="Create a new institution",
        tags=["Institution Management"],
    )
    @transaction.atomic()
    def post(self, request):
        if Institution.objects.filter(
            institution_owner__id=request.data.get("institution_owner_id"),
            institution_name=request.data.get("institution_name"),
        ).exists():
            return Response(
                {"error": "User already has an institution with the same name."},
                status=status.HTTP_409_CONFLICT,
            )



        serializer = InstitutionSerializer(
            data=request.data,
            context={
                "request": request,
                "user": request.user,
            },
        )

        if serializer.is_valid():
            try:
                institution = serializer.save()
                logger.info(
                    f"Institution created: {institution.institution_name}, Country: {institution.country_code}"
                )


                return Response(
                    InstitutionSerializer(
                        institution, context={"user": request.user}
                    ).data,
                    status=status.HTTP_201_CREATED,
                )

            except Exception as e:
                logger.error(f"Error creating institution: {str(e)}")
                import traceback

                logger.error(f"Full traceback: {traceback.format_exc()}")
                return Response(
                    {
                        "error": "An error occurred while creating the institution. Please try again."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: InstitutionSerializer(many=True)},
        description="Retrieve all institutions.",
        summary="Get all institutions",
        tags=["Institution Management"],
    )
    def get(self, request, institution_id=None):

        if request.user.is_staff:
            institutions = Institution.objects.all()
        else:
            institutions = Institution.objects.filter(institution_owner=request.user)

        institutions = institutions.order_by("-created_at")
        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(institutions, request)
        serializer = InstitutionSerializer(paginator_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class InstitutionDetailAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        responses={200: InstitutionSerializer},
        description="Retrieve an institution.",
        summary="Get an institution",
        tags=["Institution Management"],
    )
    def get(self, request, institution_id):
        try:
            institution = Institution.objects.get(id=institution_id)
            if institution.institution_owner != request.user:
                return Response({"error": "Access denied."}, status=403)
            serializer = InstitutionSerializer(institution)
            return Response(serializer.data)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)

    @extend_schema(
        request=InstitutionSerializer,
        responses={200: InstitutionSerializer},
        description="Update an existing institution.",
        summary="Update an institution",
        tags=["Institution Management"],
    )
    def patch(self, request, institution_id):
        try:
            institution = Institution.objects.get(id=institution_id)
            if institution.institution_owner != request.user:
                return Response({"error": "Access denied."}, status=403)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)

        serializer = InstitutionSerializer(institution, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        description="Delete an existing institution.",
        summary="Delete as institution",
        tags=["Institution Management"],
    )
    def delete(self, request, institution_id):
        try:
            institution = Institution.objects.get(id=institution_id)
            if institution.institution_owner != request.user:
                return Response({"error": "Access denied."}, status=403)
            institution.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)


class InstitutionBankTypeListAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = ["bank_fullname", "created_at", "bank_code", "is_active"]
    default_ordering = ["bank_fullname"]

    @extend_schema(
        responses={200: InstitutionBankTypeSerializer(many=True)},
        description="Retrieve all attached banks .",
        summary="Get all attached banks ",
        tags=["Bank Type Management"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        user = request.user.profile if request.user.is_authenticated else None

        try:
            institution = Institution.objects.get(id=user.institution_id)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)

        bank_types = InstitutionBankType.objects.filter(
            institution=institution, deleted_at__isnull=True
        ).order_by("-created_at")

        if search_query:
            bank_types = bank_types.filter(
                Q(bank_fullname__icontains=search_query)
                | Q(bank_code__icontains=search_query)
                | Q(br_code__icontains=search_query)
            )

        try:
            bank_types = self.apply_sorting(bank_types, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(bank_types, request)

        serializer = InstitutionBankTypeSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=InstitutionBankTypeSerializer,
        responses={201: InstitutionBankTypeSerializer},
        description="Create a new bank type.",
        summary="Create a new bank type",
        tags=["Bank Type Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = InstitutionBankTypeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            bank_type = serializer.save()
            bank_type.confirm_create()
            return Response(
                InstitutionBankTypeSerializer(bank_type).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class InstitutionBankTypeDetailView(APIView):
    @extend_schema(
        responses={200: InstitutionBankTypeSerializer},
        description="Retrieve a bank type.",
        summary="Get a bank type",
        tags=["Bank Type Management"],
    )
    def get(self, request, bank_type_id):
        try:
            bank_type = InstitutionBankType.objects.get(id=bank_type_id)
            serializer = InstitutionBankTypeSerializer(bank_type)
            return Response(serializer.data)
        except InstitutionBankType.DoesNotExist:
            return Response({"error": "Bank type not found."}, status=404)

    @extend_schema(
        request=InstitutionBankTypeSerializer,
        responses={200: InstitutionBankTypeSerializer},
        description="Update an existing bank type.",
        summary="Update a bank type",
        tags=["Bank Type Management"],
    )
    @transaction.atomic()
    def patch(self, request, bank_type_id):
        try:
            bank_type = InstitutionBankType.objects.get(id=bank_type_id)
        except InstitutionBankType.DoesNotExist:
            return Response({"error": "Bank type not found."}, status=404)

        bank_type.approval_status = "under_update"

        serializer = InstitutionBankTypeSerializer(
            bank_type, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            bank_type.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        description="Delete an existing bank type.",
        summary="Delete a bank type",
        tags=["Bank Type Management"],
    )
    @transaction.atomic()
    def delete(self, request, bank_type_id):
        try:
            bank_type = InstitutionBankType.objects.get(id=bank_type_id)
            bank_type.approval_status = "under_deletion"
            bank_type.save(update_fields=["approval_status"])
            bank_type.confirm_delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except InstitutionBankType.DoesNotExist:
            return Response({"error": "Bank type not found."}, status=404)


class InstitutionBankAccountListAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = [
        "account_name",
        "created_at",
        "institution_bank",
        "is_active",
    ]
    default_ordering = ["account_name"]

    @extend_schema(
        responses={200: InstitutionBankAccountSerializer(many=True)},
        description="Retrieve all bank accounts.",
        summary="Get all bank accounts",
        tags=["Bank Account Management"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        user = request.user.profile if request.user.is_authenticated else None

        try:
            institution = Institution.objects.get(id=user.institution_id)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)

        bank_accounts = InstitutionBankAccount.objects.filter(
            institution_bank__institution=institution, deleted_at__isnull=True
        ).order_by("-created_at")

        if search_query:
            bank_accounts = bank_accounts.filter(
                Q(account_name__icontains=search_query)
                | Q(account_number__icontains=search_query)
                | Q(institution_bank__bank_fullname__icontains=search_query)
            )

        try:
            bank_accounts = self.apply_sorting(bank_accounts, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(bank_accounts, request)

        serializer = InstitutionBankAccountSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=InstitutionBankAccountSerializer,
        responses={201: InstitutionBankAccountSerializer},
        description="Create a new bank account.",
        summary="Create a new bank account",
        tags=["Bank Account Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = InstitutionBankAccountSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            bank_account = serializer.save()
            bank_account.confirm_create()
            return Response(
                InstitutionBankAccountSerializer(bank_account).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class InstitutionBankAccountDetailView(APIView):
    @extend_schema(
        responses={200: InstitutionBankAccountSerializer},
        description="Retrieve a bank account.",
        summary="Get a bank account",
        tags=["Bank Account Management"],
    )
    def get(self, request, bank_account_id):
        try:
            bank_account = InstitutionBankAccount.objects.get(id=bank_account_id)
            serializer = InstitutionBankAccountSerializer(bank_account)
            return Response(serializer.data)
        except InstitutionBankAccount.DoesNotExist:
            return Response({"error": "Bank account not found."}, status=404)

    @extend_schema(
        request=InstitutionBankAccountSerializer,
        responses={200: InstitutionBankAccountSerializer},
        description="Update an existing bank account.",
        summary="Update a bank account",
        tags=["Bank Account Management"],
    )
    @transaction.atomic()
    def patch(self, request, bank_account_id):
        try:
            bank_account = InstitutionBankAccount.objects.get(id=bank_account_id)
        except InstitutionBankAccount.DoesNotExist:
            return Response({"error": "Bank account not found."}, status=404)

        bank_account.approval_status = "under_update"

        serializer = InstitutionBankAccountSerializer(
            bank_account, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            bank_account.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        description="Delete an existing bank account.",
        summary="Delete a bank account",
        tags=["Bank Account Management"],
    )
    def delete(self, request, bank_account_id):
        try:
            bank_account = InstitutionBankAccount.objects.get(id=bank_account_id)
            bank_account.approval_status = "under_deletion"
            bank_account.save(update_fields=["approval_status"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except InstitutionBankAccount.DoesNotExist:
            return Response({"error": "Bank account not found."}, status=404)


class InstitutionWorkingDaysListAPIView(APIView):
    @extend_schema(
        responses={200: InstitutionWorkingDaysSerializer(many=True)},
        description="Retrieve all working days for an institution.",
        summary="Get all working days",
        tags=["Working Days Management"],
    )
    def get(self, request):
        user = request.user.profile if request.user.is_authenticated else None

        try:
            institution = Institution.objects.get(id=user.institution_id)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)

        working_days = InstitutionWorkingDays.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        serializer = InstitutionWorkingDaysSerializer(working_days, many=True)

        return Response(serializer.data)

    @extend_schema(
        request=InstitutionWorkingDaysSerializer,
        responses={201: InstitutionWorkingDaysSerializer},
        description="Create a new working days configuration for an institution.",
        summary="Create working days",
        tags=["Working Days Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = InstitutionWorkingDaysSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            working_days = serializer.save()
            working_days.confirm_create()
            return Response(
                InstitutionWorkingDaysSerializer(working_days).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class InstitutionWorkingDaysDetailView(APIView):
    @extend_schema(
        request=InstitutionWorkingDaysSerializer,
        responses={200: InstitutionWorkingDaysSerializer},
        description="Update existing working days configuration for an institution.",
        summary="Update working days",
        tags=["Working Days Management"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        try:
            working_days = InstitutionWorkingDays.objects.get(id=pk)
        except InstitutionWorkingDays.DoesNotExist:
            return Response(
                {"error": "Working days configuration not found."}, status=404
            )

        working_days.approval_status = "under_update"

        serializer = InstitutionWorkingDaysSerializer(
            working_days, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            working_days.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )



class BranchListAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = [
        "branch_name",
        "created_at",
        "branch_location",
        "is_active",
        "branch_phone_number",
        "branch_email",
        "branch_opening_time",
        "branch_closing_time",
    ]
    default_ordering = ["branch_name"]

    @extend_schema(
        request=BranchSerializer,
        responses={201: BranchSerializer},
        description="Create a new branch.",
        summary="Create a new branch",
        tags=["Branch Management"],
    )
    @method_decorator(permission_required('can_add_branch'))
    @transaction.atomic()
    def post(self, request):
        serializer = BranchSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            branch = serializer.save()
            branch.confirm_create()
            return Response(
                BranchSerializer(branch).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: BranchSerializer(many=True)},
        description="Retrieve all branches.",
        summary="Get all branches",
        tags=["Branch Management"],
    )
    @method_decorator(permission_required('can_view_branches'))
    def get(self, request):
        search_query = request.query_params.get("search", None)

        branches = Branch.objects.filter(deleted_at__isnull=True).order_by(
            "-created_at"
        )

        if not request.user.is_staff:
            branches = branches.filter(institution__institution_owner=request.user)

        if search_query:
            branches = branches.filter(
                Q(branch_name__icontains=search_query)
                | Q(branch_location__icontains=search_query)
            )

        try:
            branches = self.apply_sorting(branches, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(branches, request)

        serializer = BranchSerializer(paginator_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class BranchDetailAPIView(APIView):
    @extend_schema(
        responses={200: BranchSerializer},
        description="Retrieve a branch.",
        summary="Get a branch",
        tags=["Branch Management"],
    )
    @method_decorator(permission_required('can_view_branches'))
    def get(self, request, branch_id):
        try:
            branch = Branch.objects.get(id=branch_id)
            if (
                not request.user.is_staff
                and branch.institution.institution_owner != request.user
            ):
                return Response({"error": "Access denied."}, status=403)
            serializer = BranchSerializer(branch)
            return Response(serializer.data)
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found."}, status=404)

    @extend_schema(
        request=BranchSerializer,
        responses={200: BranchSerializer},
        description="Update an existing branch.",
        summary="Update a branch",
        tags=["Branch Management"],
    )
    @method_decorator(permission_required('can_edit_branch'))
    @transaction.atomic()
    def patch(self, request, branch_id):

        try:
            branch = Branch.objects.get(id=branch_id)
            if (
                not request.user.is_staff
                and branch.institution.institution_owner != request.user
            ):
                return Response({"error": "Access denied."}, status=403)
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found."}, status=404)

        branch.approval_status = "under_update"

        serializer = BranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():

            serializer.save()
            branch.confirm_update()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={204: None},
        description="Delete an existing branch.",
        summary="Delete a branch",
        tags=["Branch Management"],
    )
    @method_decorator(permission_required('can_delete_branch'))
    @transaction.atomic()
    def delete(self, request, branch_id):
        try:
            branch = Branch.objects.get(id=branch_id)
            if (
                not request.user.is_staff
                and branch.institution.institution_owner != request.user
            ):
                return Response({"error": "Access denied."}, status=403)
            branch.approval_status = "under_deletion"
            branch.save(update_fields=["approval_status"])
            branch.confirm_delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found."}, status=404)


class InstitutionBranchAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = [
        "branch_name",
        "created_at",
        "branch_location",
        "is_active",
        "branch_phone_number",
        "branch_email",
        "branch_opening_time",
        "branch_closing_time",
    ]
    default_ordering = ["branch_name"]

    @extend_schema(
        responses={200: BranchSerializer(many=True)},
        description="Retrieve all branches associated to a institution whose ID is given",
        summary="Get branches by Institution ID",
        tags=["Branch Management"],
    )
    def get(self, request, institution_id):
        try:
            institution = Institution.objects.get(id=institution_id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user == institution.institution_owner:
            branches = Branch.objects.filter(institution_id=institution_id)
        else:
            branches = Branch.objects.filter(
                institution_id=institution_id,
                id__in=UserBranch.objects.filter(user=request.user).values_list(
                    "branch_id", flat=True
                ),
            )

        branches = branches.order_by("-created_at")

        try:
            branches = self.apply_sorting(branches, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(branches, request)
        serializer = BranchSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserProfileListAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ProfileSerializer,
        responses={201: ProfileSerializer},
        description="Create a new user with profile.",
        summary="Create a new user profile",
        tags=["User Management"],
    )
    def post(self, request):
        random_password = generate_compliant_password()
        mutable_data = request.data.copy()
        user_data = mutable_data.get("user", {})
        user_data["password"] = random_password
        mutable_data["user"] = user_data

        serializer = ProfileSerializer(data=mutable_data)
        if serializer.is_valid():
            profile = serializer.save()
            profile.user.is_password_verified = False
            profile.user.save()

            token = create_and_institution_token(
                user=profile.user, purpose="registration", expiry_minutes=15
            )
            password_link = build_password_link(request=request, token=token)
            send_password_link_to_user(user=profile.user, link=password_link)

            return Response(
                ProfileSerializer(profile).data, status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        institution = request.user.profile.institution
        search_query = request.query_params.get("search", None)
        if not institution:
            return Response({"error": "Institution not found."}, status=404)

        user = request.user
        if not user.is_staff and institution.institution_owner != user:
            profile = user.profile
            if profile.institution.id != institution.id:
                return Response({"error": "Access denied."}, status=403)

        profiles = Profile.objects.filter(institution=institution)

        if search_query:
            profiles = profiles.filter(
                Q(user__fullname__icontains=search_query)
                | Q(user__email__icontains=search_query)
            )
        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(profiles, request)
        serializer = ProfileSerializer(
            paginator_qs, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)


class UserProfileDetailAPIView(APIView):
    @extend_schema(
        responses={200: ProfileSerializer(many=True)},
        description="Retrieve the user profile of all users attached to the institution.",
        summary="Get all user profiles",
        tags=["User Management"],
    )
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstitutionUserProfileAPIView(APIView):
    @extend_schema(
        request=ProfileSerializer(partial=True),
        responses={200: ProfileSerializer},
        description="Update a institution user's profile (partial update).",
        summary="Update institution user details",
        tags=["User Management"],
    )
    def patch(self, request, user_id):
        if user_id:
            try:
                user = Profile.objects.get(user_id=user_id)
                serializer = Profile(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "message": "Institution User updated successfully",
                            "user": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            except Profile.DoesNotExist:
                return Response(
                    {"error": "Institution User not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(
            {"error": "User ID is required for updating."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserBranchListCreateView(APIView):
    @extend_schema(
        request=UserBranchSerializer,
        responses={201: UserBranchSerializer},
        description="Create a new user-branch relationship.",
        summary="Create a new user-branch relationship",
        tags=["User Management"],
    )
    def post(self, request):
        serializer = UserBranchSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user_branch = serializer.save()

            return Response(
                UserBranchSerializer(user_branch).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        user_branches = UserBranch.objects.all().order_by("-created_at")
        serializer = UserBranchSerializer(user_branches, many=True)
        return Response(serializer.data)


class UserBranchDetailAPIView(APIView):
    @extend_schema(
        responses={200: UserBranchSerializer},
        description="Retrieve a user-branch relationship.",
        summary="Get a user-branch relationship",
        tags=["User Management"],
    )
    def get(self, request, user_branch_id):
        try:
            user_branch = UserBranch.objects.get(id=user_branch_id)
            serializer = UserBranchSerializer(user_branch)
            return Response(serializer.data)
        except UserBranch.DoesNotExist:
            return Response(
                {"error": "User-branch relationship not found."}, status=404
            )

    @extend_schema(
        request=UserBranchSerializer,
        responses={200: UserBranchSerializer},
        description="Update an existing user-branch relationship.",
        summary="Update a user-branch relationship",
        tags=["User Management"],
    )
    def patch(self, request, user_branch_id):
        user_branch = get_object_or_404(UserBranch, id=user_branch_id)
        serializer = UserBranchSerializer(user_branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class DepartmentListAPIView(APIView, SortableAPIMixin):
    allowed_ordering_fields = ["name", "created_at", "description", "is_active"]
    default_ordering = ["name"]

    @extend_schema(
        request=DepartmentSerializer,
        responses={201: DepartmentSerializer},
        description="Create a new department.",
        summary="Create a new department",
        tags=["Department Management"],
    )
    @transaction.atomic()
    def post(self, request, institution_id=None):
        if not institution_id:
            return Response(
                {"error": "Institution ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            department.confirm_create()
            return Response(
                DepartmentSerializer(department).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={200: DepartmentSerializer(many=True)},
        description="Retrieve all departments.",
        summary="Get all departments",
        tags=["Department Management"],
    )
    def get(self, request, institution_id=None):
        search_query = request.query_params.get("search", None)
        departments = Department.objects.filter(
            institution_id=institution_id, deleted_at__isnull=True
        ).order_by("-created_at")

        if search_query:
            departments = departments.filter(Q(name__icontains=search_query))

        try:
            departments = self.apply_sorting(departments, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginator_qs = paginator.paginate_queryset(departments, request)
        serializer = DepartmentSerializer(paginator_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class DepartmentDetailAPIView(APIView):
    @extend_schema(
        responses={200: DepartmentSerializer},
        description="Retrieve a department.",
        summary="Get a department",
        tags=["Department Management"],
    )
    def get(self, request, department_id):
        try:
            department = Department.objects.get(id=department_id)
            serializer = DepartmentSerializer(department)
            return Response(serializer.data)
        except Department.DoesNotExist:
            return Response({"error": "Department not found."}, status=404)

    @extend_schema(
        request=DepartmentSerializer,
        responses={200: DepartmentSerializer},
        description="Update an existing department.",
        summary="Update a department",
        tags=["Department Management"],
    )
    @transaction.atomic()
    def patch(self, request, department_id):
        try:
            department = Department.objects.get(id=department_id)
            department.approval_status = "under_update"
            serializer = DepartmentSerializer(
                department, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                department.confirm_update()
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        except Department.DoesNotExist:
            return Response({"error": "Department not found."}, status=404)

    @extend_schema(
        responses={204: None},
        description="Delete an existing department.",
        summary="Delete a department",
        tags=["Department Management"],
    )
    def delete(self, request, department_id):
        try:
            department = Department.objects.get(id=department_id)
            department.approval_status = "under_deletion"
            department.save(update_fields=["approval_status"])
            department.confirm_delete()
            return Response(status=204)
        except Department.DoesNotExist:
            return Response({"error": "Department not found."}, status=404)


# TODO: Make sure a user who does this has permissions to do so
@extend_schema(
    responses={204: None},
    description="Delete an existing user-branch relationship by user and branch IDs.",
    summary="Delete a user-branch relationship by user and branch",
    tags=["User Management"],
)
@api_view(["DELETE"])
def delete_user_branch_by_ids(request, user_id, branch_id):
    try:
        user_branch = UserBranch.objects.get(user_id=user_id, branch_id=branch_id)
        user_branch.is_active = False
        user_branch.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserBranch.DoesNotExist:
        return Response(
            {"error": "User-branch relationship not found."},
            status=status.HTTP_404_NOT_FOUND,
        )







class DashboardView(APIView):
    def get(self, request, institution_id):
        year = request.query_params.get("year", timezone.now().year)
        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "Invalid year"}, status=status.HTTP_400_BAD_REQUEST
            )

        prev_year = year - 1
        today = timezone.now().date()


        dep_count = Department.objects.filter(
            is_active=True, institution_id=institution_id
        ).count()



        basic_counts = {
            "department_count": dep_count,
        }


        data = {
            "basic_counts": basic_counts,
        }

        return Response(data, status=status.HTTP_200_OK)
    
    
class ResendPasswordResetLink(APIView):

    @extend_schema(
        description="Resend password reset link",
        summary="Resend password reset link to a user",
        tags=["User Management"],
        responses={200: CustomUserSerializer},
    )
    def get(self, request, pk):

        institution = request.user.profile.institution
        user = request.user
        if not user.is_staff and institution.institution_owner != user:
            profile = user.profile
            if profile.institution.id != institution.id:
                return Response({"error": "You can not perform this action."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=pk)
        except (CustomUser.DoesNotExist, ValueError):
            return Response(
                    {"error": "Invalid or non-existent user ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        token = create_and_institution_token(
                user=user, purpose="registration", expiry_minutes=15
            )
        password_link = build_password_link(request=request, token=token)
        send_password_link_to_user(user=user, link=password_link)

        return Response("Password reset link resent successfully", status=status.HTTP_200_OK)

