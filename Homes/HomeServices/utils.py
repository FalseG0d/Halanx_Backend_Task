SR_NOT_RESOLVED = 'Not Resolved'
SR_IN_PROGRESS = 'In Progress'
SR_RESOLVED = 'Resolved'

ServiceRequestStatusCategories = (
    (SR_NOT_RESOLVED, SR_NOT_RESOLVED),
    (SR_IN_PROGRESS, SR_IN_PROGRESS),
    (SR_RESOLVED, SR_RESOLVED),
)


def get_service_request_picture_upload_path(instance, filename):
    return "ServiceRequests/{}.{}".format(instance.service_request.id, filename.split('.')[-1])


def get_service_category_picture_upload_path(instance, filename):
    return "ServiceCategory/{}.{}".format(instance.name, filename.split('.')[-1])


def get_major_service_category_picture_upload_path(instance, filename):
    return "MajorServiceCategory/{}.{}".format(instance.name, filename.split('.')[-1])


def get_support_staff_member_picture_upload_path(instance, filename):
    return "SupportStaffMember/{}/{}".format(instance.id, filename.split('/')[-1])
