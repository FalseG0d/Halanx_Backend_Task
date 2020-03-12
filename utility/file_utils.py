from io import BytesIO

import boto3
import xhtml2pdf.pisa as pisa
from botocore.client import Config
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template


def get_secret_url(file_name):
    if not file_name: return
    key = settings.AWS_PRIVATE_MEDIA_LOCATION + '/' + file_name
    s3 = boto3.client('s3', region_name=settings.AWS_S3_REGION,
                      aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
                      config=Config(signature_version='s3v4'))
    return s3.generate_presigned_url('get_object',
                                     Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
                                     ExpiresIn=100)


def render_pdf_from_html(path: str, params: dict, filename: str='download.pdf'):
    template = get_template(path)
    html = template.render(params)
    response = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
    if not pdf.err:
        response = HttpResponse(response.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        return response
    else:
        return HttpResponse("Error Rendering PDF", status=400)
