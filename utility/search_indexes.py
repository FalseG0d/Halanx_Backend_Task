from decouple import config
from elasticsearch import Elasticsearch

from Products.models import Product, ProductIndex
from StoreBase.models import Store
from StoreBase.utils import StoreIndex

url = config('ELASTIC_SEARCH_URL')


def store_bulk_indexing():
    es_client = Elasticsearch(hosts=[url], )
    StoreIndex.init(using=es_client)
    for item in Store.objects.all():
        if item.is_verified:
            obj = StoreIndex(
                meta={'id': item.id},
                Id=item.id,
                StoreName=item.name,
                StoreCategory=item.category,
                StoreAddress=item.place.address,
            )
            obj.save(using=es_client)


def product_bulk_indexing():
    es_client = Elasticsearch(hosts=[url], )
    ProductIndex.init(using=es_client)
    for item in Product.objects.all():
        if item.store.is_verified:
            obj = ProductIndex(
                meta={'id': item.id},
                Id=item.id,
                ProductName=item.name,
                Category=item.category,
                StoreId=item.store.id,
                Price=item.price,
                ProductSize=item.size,
                Features=item.features
            )
            obj.save(using=es_client)
