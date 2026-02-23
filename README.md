# Aut0arch

Aut0arch is an autonomous architecture analysis and visualization application. It extracts software structures from source code repositories and utilizes LLMs to generate explanations of the resulting microservices/clusters.

The project is split into 6 core modules:
- `app`: The React/Vite Frontend visualization layer.
- `server`: The Flask back-end orchestrator.
- `parser`: A Tree-Sitter component that creates a graph representation of the source code.
- `clustering`: Applies the Louvain algorithm to map classes/files into domains.
- `explainer`: Uses an LLM to assign purpose and context to the architectural clusters.
- `docs`: GitBook documentation.

## Installation & Setup

Aut0arch is deeply distributed and requires multiple native dependencies, including C compilers for AST parsing. Consequently, we highly recommend running the platform via Docker.

### Method 1: Docker Compose (Recommended)

To run the entire suite locally across all repositories without configuring a deep Python/Node environment:

1. Ensure [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) are installed on your machine.
2. Ensure you have provisioned any credentials such as a `GOOGLE_API_KEY` in `explainer/.env` if you're using Gemini.
3. Run the following command from this root directory:

```bash
docker-compose up --build -d
```

Both the `frontend` (port 5173) and `backend` (port 5000) services will bind to your localhost.
Navigate to [http://localhost:5173](http://localhost:5173) to view the application.

*To stop the cluster:*
```bash
docker-compose down
```

### Method 2: Manual Local Execution
If you wish to run the app manually without Docker, see the individual `README.md` files localized within each sub-repository for specific compilation and setup instructions. You will generally need Node.js 20+ and Python 3.10+.
