from Carts.models import ProductItem
from Coupon.models import Coupon, CouponUser

SUCCESS = "Promo code can be successfully redeemed."
FAIL1 = "You are not eligible to redeem this promo code."
FAIL2 = "No such promo code exists!"
FAIL3 = "You already have an active promo code."


def verify_coupon(coupon_code, customer):
    if CouponUser.objects.filter(user=customer, active=True).count():
        return False, FAIL3

    try:
        coupon = Coupon.objects.get(code=coupon_code)
        if not coupon.can_redeem(customer):
            return False, FAIL1
    except Coupon.DoesNotExist:
        return False, FAIL2

    items = ProductItem.objects.filter(cart__customer=customer, removed_from_cart=False)

    if coupon.code == 'ENGIX':
        if any([item for item in items if item.product.store.id == 75]):
            if not customer.polls.count() or \
                    customer.orders.count() or \
                    len(items) > 1 or \
                    items[0].Quantity > 1:
                return False, FAIL1
        return True, SUCCESS

    elif coupon.code in ['ROHINI100', 'JAMNGR100']:
        if customer.orders.count() >= 10:
            return False, FAIL1
        return True, SUCCESS

    elif coupon.code == 'HALANX100':
        if customer.orders.count():
            return False, FAIL1
        return True, SUCCESS

    return False, FAIL1


def update_coupon(coupon, customer):
    coupon_user = CouponUser.objects.get(user=customer, coupon=coupon)
    if coupon.code == 'ENGIX':
        coupon_user.active = False

    elif coupon.code in ['ROHINI100', 'JAMNGR100']:
        if customer.orders.count() >= 10:
            coupon_user.active = False

    elif coupon.code == 'HALANX100':
        coupon_user.active = False

    coupon_user.save()


def get_coupon_value(coupon, customer):
    if coupon.code in ['ROHINI100', 'JAMNGR100']:
        coupon_user = CouponUser.objects.filter(user=customer, coupon=coupon)
        if coupon_user.count() and coupon_user[0].redeemed:
            value = 0
        else:
            value = coupon.value
    else:
        value = coupon.value

    return value
