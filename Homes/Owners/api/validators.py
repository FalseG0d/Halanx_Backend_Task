from rest_framework.exceptions import ValidationError

from Homes.Houses.utils import DISTRIBUTION_TYPE_RATIO, DISTRIBUTION_TYPE_AMOUNT


def validate_single_amount_or_ratio_value(bill, distribution_type, value):
    if distribution_type == DISTRIBUTION_TYPE_RATIO:
        if value > 1:
            raise ValidationError({'detail': "Ratio greater than 1 not possible"})
        return value
    if distribution_type == DISTRIBUTION_TYPE_AMOUNT:
        if value > bill.amount:
            raise ValidationError({'detail': "Value can't be greater than bill amount"})
        return value
