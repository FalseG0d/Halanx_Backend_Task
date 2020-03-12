import geopy.distance
import numpy as np
from sklearn.cluster import AffinityPropagation


def cluster_by_location(locations, lookup):
    if len(locations) == 1:
        return [{'c': locations[0], 'ids': [lookup[0]]}]
    af = AffinityPropagation().fit(locations)
    labels = af.labels_
    clusters = []
    for idx, center in enumerate(af.cluster_centers_):
        clusters.append({'c': center, 'ids': lookup[np.where(labels == idx)]})
    return clusters


def find_distance(a, b):
    return geopy.distance.vincenty(a, b)


def get_region(lat, lng):
    if not lat or not lng:
        return None
    lat, lng = float(lat), float(lng)
    from Places.models import Region
    regions = Region.objects.all()
    if not regions:
        return None
    distance, closest_region = min((find_distance((r.latitude, r.longitude), (lat, lng)).km, r) for r in regions)
    if distance <= closest_region.radius:
        return closest_region
    else:
        return None


def set_customer_region():
    from UserBase.models import Customer
    customers = Customer.objects.filter(is_registered=True)
    for customer in customers:
        customer.set_region()
        customer.save()


def set_place_region():
    from Places.models import Place
    places = Place.objects.all()
    for place in places:
        place.set_region()
        place.save()


def set_shopper_region():
    from ShopperBase.models import Shopper
    shoppers = Shopper.objects.all()
    for shopper in shoppers:
        shopper.set_region()
        shopper.save()


def set_order_region():
    from OrderBase.models import Order
    orders = Order.objects.all()
    for order in orders:
        order.set_region()
        order.save()


def set_batch_region():
    from BatchBase.models import Batch
    batches = Batch.objects.all()
    for batch in batches:
        batch.set_region()
        batch.save()


def set_post_region():
    from Post.models import Post
    posts = Post.objects.all()
    for post in posts:
        post.set_region()
        post.save()


def set_subscribeditem_region():
    from Subscriptions.models import SubscribedItem
    items = SubscribedItem.objects.all()
    for item in items:
        item.set_region()
        item.save()
