from app import create_app

app = create_app()

if __name__ == "__main__": # This checks if the file is being run directly (not imported somewhere else)
    app.run(host="0.0.0.0", port=5000) # host="0.0.0.0" means "accept connections from any device"