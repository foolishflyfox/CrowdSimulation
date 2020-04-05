FROM python
MAINTAINER hbfeng "fenghb@mail.ustc.edu.cn"

RUN git clone https://github.com/foolishflyfox/CrowdSimulation.git &&\
    cd CrowdSimulation &&\
    pip install -r requirements.txt
CMD cd CrowdSimulation-master && python app.py

