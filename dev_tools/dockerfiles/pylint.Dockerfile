FROM python:3.7-alpine

RUN pip install --no-cache-dir \
        pylint \
    && mkdir /.pylint.d \
    && chmod a+rwx /.pylint.d

WORKDIR /workdir

CMD python -m pylint \
        --rcfile /workdir/dev_tools/lint/pylintrc \
        /workdir