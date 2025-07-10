# Constitution Chatbot.

1. various builds to compare multi-stage and single stage builds of docker (image size).
2. names images and volumes and networks created for easy maintenance.

To setup the docker images/containers/volumes

```bash
sudo docker compose --build -d
```

To delete the docker containers/volumes

```bash
sudo docker compose down -v
```

# Prompt A Question, Get a response.

# Add a document, to be embedded.

After you add a document, ensure to have a stable internet connection so as to download the ChromaDB embedding model and the docling model. These are stored in chatbot_backend/.cache.

Use this command to monitor the named backend container

```bash
sudo docker logs backend_container -f
```

A better response for this will also be added to the Frontend.

# Documentation of the ChatBot.

I have exposed the backend container so that users can be able to access the automatic fastAPI docs.

```bash
    http://localhost:8081/docs
```

# Streamlit UI

The streamlit UI can be run found at

```bash
http://localhost:8082
```
