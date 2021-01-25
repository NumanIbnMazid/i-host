import requests
from weasyprint import pdf
from restaurant.models import *

def print_node(pdf_obj,**kwargs):
    # data = {"title": "My Test PrintJob", "contentType": "pdf_uri", "content": "https://ihost-space.sgp1.digitaloceanspaces.com/ihost-space-development/pdfresizer.com-pdf-crop.pdf",
    #         "source": "test documentation!", "options": {'fit_to_page': True}, 'printer': 69976050}
    try:
        print_node_qs = PrintNode.objects.filter(restaurant_id=kwargs.get('restaurant_id')).first()
        if not print_node_qs:
            return False
    except:
       return False

    data = {"title": "My Test PrintJob", "contentType": "pdf_base64", "content": pdf_obj,
            "source": "test documentation!", "options": {'fit_to_page': True, "dpi": "300*300"}, 'printer': print_node_qs.printer_id}

    response = requests.post('https://api.printnode.com/printjobs',
                             auth=('ToDuOdQbZTW5d9n0TP6JFNRfLScEth4vsg1om5AqmOw', ''), data=data)
    if 300 > response.status_code >= 200:
        return True
    else:
        return False
