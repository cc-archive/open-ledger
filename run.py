from openledger import application
from flask_debugtoolbar import DebugToolbarExtension

if __name__ == '__main__':
    # Run me in development as 'python -m app' to avoid path/import problems
    toolbar = DebugToolbarExtension(application)
    application.run(debug=True)
