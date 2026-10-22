FROM public.ecr.aws/lambda/python:3.13@sha256:e0237850eecd760896365e768bac1526ea01098e325fa590e5bc735b26d5dbb9

RUN pip install --no-cache-dir --upgrade "pip==26.2.2"

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY main.py ${LAMBDA_TASK_ROOT}

CMD [ "main.handler" ]