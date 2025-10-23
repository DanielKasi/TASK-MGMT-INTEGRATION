from .models import PublicHoliday, Event, Calendar
from .serializers import (
    PublicHolidaySerializer,
    EventSerializer,
    CalendarSerializer,
    EventSerializer,
    CalendarSerializer,
)
from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from institution.models import Institution
from utilities.pagination import CustomPageNumberPagination
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view
from django.utils import timezone
from django.db.models import Q
from django.db import transaction


class PublicHolidayListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Public Holidays",
        responses={
            200: OpenApiResponse(
                response=PublicHolidaySerializer(many=True),
                description="List of public holidays",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
        },
        tags=["Calendar"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        date = request.query_params.get("date", None)
        institution = get_object_or_404(
            Institution, id=request.user.profile.institution.id
        )
        public_holidays = PublicHoliday.objects.filter(
            institution=institution, deleted_at__isnull=True
        )
        if date:
            public_holidays = public_holidays.filter(date=date)
        if search_query:
            public_holidays = public_holidays.filter(
                Q(title__icontains=search_query) | Q(date__icontains=search_query)
            )
        paginator = CustomPageNumberPagination()
        paginated_holidays = paginator.paginate_queryset(public_holidays, request)
        serializer = PublicHolidaySerializer(paginated_holidays, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create a Public Holiday",
        request=PublicHolidaySerializer,
        responses={
            201: OpenApiResponse(
                response=PublicHolidaySerializer,
                description="Public holiday created successfully",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
        },
        tags=["Calendar"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = PublicHolidaySerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicHolidayDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve a Public Holiday",
        responses={
            200: OpenApiResponse(
                response=PublicHolidaySerializer,
                description="Public holiday details",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Public holiday not found",
            ),
        },
        tags=["Calendar"],
    )
    def get(self, request, pk):
        public_holiday = get_object_or_404(PublicHoliday, pk=pk)
        serializer = PublicHolidaySerializer(public_holiday)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update a Public Holiday",
        request=PublicHolidaySerializer,
        responses={
            200: OpenApiResponse(
                response=PublicHolidaySerializer,
                description="Public holiday updated successfully",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Public holiday not found",
            ),
        },
        tags=["Calendar"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        public_holiday = get_object_or_404(PublicHoliday, pk=pk)
        public_holiday.approval_status = "under_update"
        serializer = PublicHolidaySerializer(
            public_holiday, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            public_holiday.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a Public Holiday",
        responses={
            204: OpenApiResponse(description="Public holiday deleted successfully"),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Public holiday not found",
            ),
        },
        tags=["Calendar"],
    )
    def delete(self, request, pk):
        public_holiday = get_object_or_404(PublicHoliday, pk=pk)
        public_holiday.approval_status = "under_deletion"
        public_holiday.save(update_fields=["approval_status"])
        public_holiday.confirm_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Events",
        responses={
            200: OpenApiResponse(
                response=EventSerializer(many=True),
                description="List of events",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
        },
        tags=["Calendar"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        date = request.query_params.get("date", None)
        mode = request.query_params.get("mode", None)
        institution = get_object_or_404(
            Institution, id=request.user.profile.institution.id
        )
        events = Event.objects.filter(institution=institution, deleted_at__isnull=True)

        if date:
            events = events.filter(date=date)

        if mode:
            events = events.filter(event_mode=mode)
        if search_query:
            events = events.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(date__icontains=search_query)
                | Q(frequency__icontains=search_query)
                | Q(target_audience__icontains=search_query)
            )
        paginator = CustomPageNumberPagination()
        paginated_events = paginator.paginate_queryset(events, request)
        serializer = EventSerializer(paginated_events, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create an Event",
        request=EventSerializer,
        responses={
            201: OpenApiResponse(
                response=EventSerializer,
                description="Event created successfully",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
        },
        tags=["Calendar"],
    )
    @transaction.atomic()
    def post(self, request):

        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(created_by=request.user)
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve an Event",
        responses={
            200: OpenApiResponse(
                response=EventSerializer,
                description="Event details",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Event not found",
            ),
        },
        tags=["Calendar"],
    )
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update an Event",
        request=EventSerializer,
        responses={
            200: OpenApiResponse(
                response=EventSerializer,
                description="Event updated successfully",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Event not found",
            ),
        },
        tags=["Calendar"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        event.approval_stage = "under_update"
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            event.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete an Event",
        responses={
            204: OpenApiResponse(description="Event deleted successfully"),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Event not found",
            ),
        },
        tags=["Calendar"],
    )
    @transaction.atomic()
    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        event.approval_status = "under_deletion"
        event.save(update_fields=["approval_status"])
        event.confirm_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstitutionCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Institution Calendar",
        responses={
            200: OpenApiResponse(
                response=CalendarSerializer,
                description="Institution calendar details",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Calendar not found",
            ),
        },
        tags=["Calendar"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        institution = get_object_or_404(
            Institution, id=request.user.profile.institution.id
        )

        year = request.query_params.get("year", None)
        if year:
            try:
                year = int(year)
            except ValueError:
                return Response(
                    {"error": "Invalid year format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            year = timezone.now().year

        calendar = Calendar.objects.filter(
            institution=institution, year=year, deleted_at__isnull=True
        ).first()

        if not calendar:
            return Response(
                {"error": f"Calendar not found for the year {year}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if search_query:
            calendar = calendar.filter(Q(year__icontains=search_query))

        serializer = CalendarSerializer(calendar)
        return Response(serializer.data, status=status.HTTP_200_OK)
