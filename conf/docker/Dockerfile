FROM odoo:16

USER root
RUN groupadd -g 1000 administrator && useradd -u 1000 -g 1000 -m -s /bin/bash administrator
USER administrator
RUN pip install openpyxl==3.1.5 dropbox==12.0.2 pyncclient==0.7 nextcloud-api-wrapper==0.2.3 boto3==1.37.5 paramiko==3.5.1