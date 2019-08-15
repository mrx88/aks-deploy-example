from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
  return 'Test API index page'
  
@app.route('/martinapi')
def say_hello():
  return 'Martin API test'

@app.route('/version')
def say_version():
  return 'Version: v3'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
