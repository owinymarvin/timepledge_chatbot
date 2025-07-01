# timepledge_chatbot

# Docker compose yaml

1. various builds to compare multi-stage and single stage builds of docker.
2. names images and volumes and networks created for easy maintenance.

To setup the docker images/containers/volumes

```bash
sudo docker compose --build -d
```

To delete the docker containers/volumes

```bash
sudo docker compose down -v
```
