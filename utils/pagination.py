from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination


class CustomLimitPagination(LimitOffsetPagination):
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100



    """
    
    
    page = self.paginate_queryset(booking_list_qs)
    serializer = self.get_serializer(page, many=True)
    paginated_data = self.get_paginated_response(serializer.data)

    """


class NoLimitPagination(LimitOffsetPagination):
    # default_limit = 1000000000
    # limit_query_param = 'limit'
    # offset_query_param = 'offset'
    # max_limit = 1000000000
    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        self.limit = self.get_limit(request)
        self.offset = self.get_offset(request)
        self.request = request
        self.display_page_controls = False

        return list(queryset)
