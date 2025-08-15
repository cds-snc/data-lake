FROM public.ecr.aws/lambda/python:3.13@sha256:b281081b54f2b2df0ec1144ca128678fd0d4203eda3ee987c35e8bb64095b014

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD [ "main.handler" ]
