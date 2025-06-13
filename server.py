from flask import Flask , render_template



app = Flask(__name__)


@app.route("/")
def homepage():
    '''
    This will be the landing / Registration page
    '''
    return render_template("register.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0" , port=3333 , debug=False)