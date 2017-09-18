FROM python:3.6.2
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

ENV HOME /opt/kean-concierge/kean-university-knowledge-graphs
RUN apt-get update && mkdir -p $HOME
COPY concierge $HOME/concierge
COPY instance $HOME/instance
COPY requirements.txt $HOME
RUN cd $HOME && pip install -r requirements.txt
WORKDIR $HOME
CMD ["nohup", "gunicorn", "-b", "0.0.0.0:5000", "concierge:app"]
