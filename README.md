# Plex Recommendations AI

This project involves creating a 'Recommended' collection on your Plex server using the power of Ollama. 
By analyzing your unique watch history, it will provide you with personalized suggestions that perfectly align with your preferred genre. 
With this feature, you'll easily discover a handful of delightful recommendations from your extensive movie list, making it a breeze to find your next enjoyable watch!

## Features

- Auto create/update a plex movie collection.
- Dynamic results based on Ollama results and Plex watch history.
- Creates a short description on the plex collection describing why it chose them movies.

## You'll need

- Plex server host and port
- Plex token
- Ollama server up and running
- Docker setup

## Setup

You'll need docker set up on your server and to best way to run this is through docker-compose.

Use this example below:

```yaml
version: "2.1"
services:
  plex-recommendations:
    build: .
    container_name: plex-recommendations
    env_file:
      - .env  # Load environment variables from the .env file
    restart: unless-stopped
```

## Stuff to do / to add
- Implement individual user collections for managed users (if possible?).
- Create more configurable options cater the movie list.
- Add TV shows functionality.
- Allow matching data past 2021?
