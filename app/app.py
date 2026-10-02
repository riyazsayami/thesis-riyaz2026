from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/doctors")
def doctors():
    return render_template("doctors.html")

@app.route("/appointment")
def appointment():
    return render_template("appointment.html")

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    return render_template("dashboard.html")

@app.route("/login")
def login():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False)
```

This corrected code ensures that the `/dashboard` route is only accessible via the `GET` and `POST` methods, improving the security of the application by restricting access to the route to only the intended HTTP methods.
