[ -d "log" ] || mkdir log
gunicorn -c gunicorn.conf fdxqs:app
