# DIG Tech 2.0 MVP

## To run for first time

need to create virtualenv. if already done, skip to next step

### Create virtualenv

```
virtualenv /path/to/venv/
```

### Start virtualenv

Windows:

```
\path\to\env\Scripts\activate
```

Mac / Linux

```
source /path/to/env/bin/activate
```

Install required packages

```
pip install -r requirements.txt
```

Navigate to the dig folder
to start the server

```
django-admin runserver
```

Problems?

```
export DJANGO_SETTINGS_MODULE=dig.settings
export PYTHONPATH="/current/working/directory"
```
