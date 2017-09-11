FROM python:3.6.2
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV HOME /opt/kean-concierge/kean-university-knowledge-graphs
RUN apt-get update && mkdir -p $HOME
COPY concierge $HOME
COPY instance $HOME
COPY requirements.txt $HOME
RUN cd $HOME && pip install -r requirements.txt
WORKDIR $HOME
CMD ["nohup", "gunicorn", "-b", "0.0.0.0:80", "app:concierge/app"]
