FROM public.ecr.aws/lambda/python:3.13@sha256:b281081b54f2b2df0ec1144ca128678fd0d4203eda3ee987c35e8bb64095b014

RUN python3 -c 'import ssl; c = ssl.create_default_context(cafile="/etc/pki/tls/certs/ca-bundle.crt"); [open("/etc/pki/ca-trust/source/blocklist/emsign-ecc-root-ca-g3.pem", "w").write(ssl.DER_cert_to_PEM_cert(d)) for m, d in zip(c.get_ca_certs(), c.get_ca_certs(binary_form=True)) if ("commonName", "emSign ECC Root CA - G3") in [x for r in m["subject"] for x in r]]' \
    && update-ca-trust extract \
    && python3 -c 'import ssl, sys; c = ssl.create_default_context(cafile="/etc/pki/tls/certs/ca-bundle.crt"); sys.exit(1 if any(("commonName", "emSign ECC Root CA - G3") in [x for r in m["subject"] for x in r] for m in c.get_ca_certs()) else 0)'

RUN pip install --no-cache-dir --upgrade "pip==26.2.2"

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD [ "main.handler" ]