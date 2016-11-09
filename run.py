from subprocess import Popen
from openledger import application
from flask_debugtoolbar import DebugToolbarExtension

if __name__ == '__main__':
    # Run me in development as 'python -m app' to avoid path/import problems
    toolbar = DebugToolbarExtension(application)
    # Also run the asset compilers
    Popen(["webpack", "-w"])  # JS/ES6/Babel
    Popen(["sass", "-w", "openledger/static/scss:openledger/static/css"])  # Sass/CSS
    application.run(debug=True)
