
if [ ! -d "venv" ]; then
    python3 -m venv venv
    sleep 2
    wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
    venv/bin/python3 get-pip.py
    rm get-pip.py
fi

venv/bin/python3 -m pip install -r /application/requirements.txt

venv/bin/python3 /application/frontend/app.py