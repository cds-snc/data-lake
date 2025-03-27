FROM public.ecr.aws/lambda/python:3.13@sha256:2cb6ce5433f8ae6ddb114eeabc7b68c89b19017a57849f4e077a0cd3585e4e8c

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD [ "main.handler" ]