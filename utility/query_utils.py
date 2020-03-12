from datetime import datetime

from django.db.models import Q
from django.utils import timezone


def convert_raw_dates(*dates):
    default_timezone = timezone.get_default_timezone()
    result = []
    for date in dates:
        if date:
            result.append(timezone.make_aware(datetime.strptime(date, "%Y-%m-%d"), default_timezone))
        else:
            result.append(None)
    return result


def date_filter(queryset, filter_key, params):
    from_date, to_date = convert_raw_dates(params.get('from_date'), params.get('to_date'))
    filters = {}
    if from_date:
        filters["{}__gte".format(filter_key)] = from_date
    if to_date:
        filters["{}__lte".format(filter_key)] = to_date
    q = Q(**filters)
    return queryset.filter(q)


def get_filter_extra_kwargs(query_filter_params, request, list_filter_dict=None):
    """
    :param query_filter_params: it is a dictionary with keys as keyword arguments for filtering and values corresponds
    to request.GET param key
    :param request: request object
    :param list_filter_dict : if list filter is provided we split string separated options to a list
    :return: returns the extra kwargs that is used for filtering the queryset e.g: .filter(**extra_kwargs)
    """

    if list_filter_dict is None:
        list_filter_dict = {}

    extra_args = {}

    for kwarg in query_filter_params:
        query_param_key = query_filter_params[kwarg]
        if query_param_key in request.GET:
            if kwarg in list_filter_dict:
                extra_args[kwarg] = list(map(lambda x: x.strip(), request.GET[query_param_key].split(",")))
            else:
                extra_args[kwarg] = request.GET[query_param_key]

    return extra_args
