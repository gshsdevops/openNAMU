import flask;
from flask_mail import Message;

mail = None;

def custom_send_email(to, subject, **kwargs):
    msg = Message (subject=subject, sender='gshswiki.noreply@gmail.com', recipients=[to])
    msg.html = flask.render_template('./views/flask-mail/template.html', **kwargs)
    mail.send(msg)