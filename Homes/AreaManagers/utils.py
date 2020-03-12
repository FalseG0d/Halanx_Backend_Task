def get_area_manager_profile_pic_upload_path(instance, filename):
    return "AreaManager/{}/{}".format(instance.user.id, filename.split('/')[-1])


AREA_MANAGER_CASH_COLLECTION_NOTIFY_MSG = """You have an upcoming cash collection on {time}.
Name: {name}
Phone No.: {phone_no}
Amount: {amount}
House: {house}"""

AREA_MANAGER_NEW_HOUSE_VISIT_NOTIFY_MSG = "A new house visit was scheduled by {name} ({phone_no}) on {time} for {" \
                                          "house}. "

AREA_MANAGER_HOUSE_VISIT_NOTIFY_MSG = """You have a scheduled house visit today at {time}.
Customer: {name} 
Phone No.: {phone_no}
House: {house}."""
