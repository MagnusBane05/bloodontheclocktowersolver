## Prerequisites: 
- git
- docker ([docker install](https://docs.docker.com/desktop/setup/install/windows-install/))

## Steps to run the application:
1. Clone the project into a directory by using the command: `git clone https://github.com/MagnusBane05/bloodontheclocktowersolver.git`
2. Navigate to the project directory: `cd bloodontheclocktowersolver`
3. Make sure Docker Desktop is running on your machine
4. Run the project with the command: `docker compose up --build`
5. Navigate to `http://localhost` in your browser

## Steps to run development application:
1. Navigate to frontend `cd fronend` and start application `npm run dev`
2. Create venv if not present `python -m venv` and activate venv `source .venv/bin/activate`
3. Install dependencies `pip install -r backend_requirements.txt`
4. Run app `python app.py`