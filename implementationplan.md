Briefing: Analysis of the Existing 'Skysong' Platform
Objective: This document deconstructs the existing "ASU Skysong IP Review Tool" based on the provided user guide and architecture diagram. It clarifies the system's purpose, technology stack, and workflow, providing critical context for your project.

1. What is the 'Skysong' Tool?
At its core, the Skysong tool is a human-in-the-loop AI platform for intellectual property (IP) discovery. Its purpose is to automate the initial review of academic publications from SCOPUS to flag papers that may contain valuable IP.

Workflow: An administrator generates a report of publications. The system uses AI (ChatGPT and other models) to score each paper on criteria like novelty and technicality. An expert human reviewer (an "IP Manager") then assesses the AI's suggestions, makes a final "IP" or "Not IP" judgment, and provides feedback that is used to retrain the AI models.

Users: The system has two main roles: Administrators who manage users, system configurations, and AI models, and IP Managers who review the publications.

End Goal: The system's goal is classification, not knowledge synthesis. It aims to answer the question: "Is this paper worth a closer look for IP?"

2. System Architecture Breakdown
The architecture diagram reveals a modern, asynchronous web application built on AWS.

Host: The entire backend runs on a single AWS EC2 Instance.

Frontend: A standard web-based user interface.

Backend Servers:

FastAPI (Python) Server: This is likely the main workhorse. Python is ideal for data processing and interacting with machine learning services, so this server probably handles the core logic: fetching data from SCOPUS, calling the OpenAI and SageMaker APIs, and interacting with the database.

Node.js Server: Often used for handling user interface requests or real-time communication. It works in tandem with the FastAPI server.

Database:

MongoDB: The primary database. As a NoSQL document database, it's flexible for storing varied information about publications, reports, and user data. It is not a graph database.

Asynchronous Processing:

RabbitMQ: This is a message queue. When a user requests a report, the request is likely placed on this queue. A backend process then picks up the job, allowing the user to continue working without waiting. This is crucial for long-running tasks.

AI & Machine Learning:

OpenAI API: Explicitly used for "Text Features." The user guide confirms "ChatGPT" assigns initial scores. This is the existing "Information Extraction" component.

Amazon SageMaker: Used to train and deploy the classification models (like the Neural Network and SVM models mentioned in the guide) that make the final "IP" vs "Not IP" prediction.

Amazon S3: Used to store the trained model files.

3. Key Takeaways for Your Knowledge Graph Project
This existing system is a goldmine of information for your project.

The Pattern is Proven: The architectural pattern—UI -> Async Job Queue -> Python Backend -> AI Service -> Database—is exactly what you need. You don't have to reinvent the wheel. Your project involves adapting this pattern for a different outcome.

The Core Difference is the Goal & Database:

Skysong's Goal: Classification.

Your Goal: Knowledge Synthesis.

This means the biggest technical change is swapping the MongoDB backend for a Graph Database (like Neo4j).

The "Information Extraction" Prompts Will Be Different: The current system uses OpenAI prompts designed to score features (e.g., "On a scale of 1-10, what is the novelty of this abstract?"). You will need to engineer new prompts designed to extract factual triplets (e.g., <Gene A, regulates, Protein B>). Analyzing their existing prompts is still valuable to see how they structure them, but your content will be different.

You're Building the "Next Step": The current tool finds important documents. Your tool will take those important documents and reveal the connections between them. This is a powerful and logical extension of their current work.

Implementation Plan: Collaborative Knowledge Synthesis Platform
Version: 1.0
Date: September 19, 2025

Objective: To design and build a multi-user application that extends the existing Skysong architecture to create a collaborative knowledge graph. Users will upload documents, from which the system will extract structured information (entities and relationships) and integrate it into a unified, queryable graph, enabling novel insight discovery.

1. Proposed System Architecture
The new system will adapt the proven asynchronous pattern of the Skysong tool. The core changes involve replacing the classification-oriented components (MongoDB, SageMaker classification models) with a knowledge synthesis stack centered around a graph database.

Architectural Changes from Skysong:

Database: MongoDB will be replaced by a Graph Database (e.g., Neo4j) as the primary data store for extracted knowledge. MongoDB may be retained for job metadata and user session information if needed.

User Document Upload: The UI will be expanded to allow authenticated users to upload their own documents (PDFs, text files, etc.), which will be stored in an Amazon S3 Bucket.

AI Extraction Logic: The Python (FastAPI) backend's AI function will be re-engineered. Instead of calling SageMaker for classification, it will use a powerful LLM (via the OpenAI API) with specialized prompts to extract knowledge triplets (e.g., (Entity A, relationship, Entity B)).

Query & Visualization Engine: A new, major component in the frontend application will be dedicated to allowing users to query the graph and visualize the results interactively.

2. Component Breakdown & Implementation Tasks
2.1. Frontend Application (React/Vue/Angular)
User Authentication: Extend the existing user management system to handle logins for the new interface.

Document Upload Interface:

Develop a secure file upload component.

Allow users to add metadata to their uploads (e.g., title, source).

Display the processing status of uploaded documents (Queued, Processing, Complete).

Graph Query Interface:

Simple Search: A basic search bar to find specific entities (nodes) in the graph.

Advanced Query Builder (Future): An interface that allows users to construct more complex queries (e.g., "Find all drugs that target proteins associated with Disease X").

Graph Visualization:

Integrate a library like D3.js, vis.js, or a dedicated Neo4j visualization tool.

Render query results as interactive nodes and edges.

Display metadata (provenance) when a user clicks on a node or edge.

2.2. Backend Services (Node.js & Python/FastAPI)
Node.js Server:

Create new API endpoints for handling document uploads from the UI.

Create endpoints to pass user queries to the Python backend.

Continue to manage user sessions and initial job requests.

Python (FastAPI) Server:

Document Consumer: Create a worker that retrieves uploaded documents from S3.

Text Pre-processing: Implement logic to parse text from various document formats (e.g., using PyPDF2 for PDFs).

Triplet Extraction Module:

Prompt Engineering: Design robust prompts for the OpenAI API that instruct the LLM to return a structured JSON array of triplets.

Output Validation: Implement strict validation to ensure the LLM's output conforms to the expected format and to handle errors or empty results.

Graph Integration Service: Logic to take the validated triplets and write them as nodes and relationships to the Neo4j database, including all necessary metadata.

Query Execution Engine: An API endpoint that receives queries from the Node.js server, translates them into the appropriate graph query language (e.g., Cypher for Neo4j), executes them, and returns the results.

2.3. Graph Database (Neo4j)
Data Model: The graph's structure is paramount. We will use a property graph model.

Nodes:

(:Entity {name: string, type: string}) -> e.g., (BRAF, Gene), (Melanoma, Disease)

(:Document {title: string, source: string, uploaded_at: datetime}) -> The source document.

(:User {username: string}) -> The user who contributed the information.

Relationships & Provenance:

An [:EXTRACTED_FROM] relationship will link every Entity node to its source Document.

An [:UPLOADED_BY] relationship will link every Document to a User.

The primary knowledge relationships (e.g., [:REGULATES], [:TARGETS]) will store provenance as properties on the edge itself:

source_document_id: The ID of the document it came from.

extracted_by: userId or system.

confidence_score: (Optional) A score from the LLM.

original_text: (Optional) The sentence from which the fact was extracted.

3. Phased Implementation Roadmap
Phase 1: Core Backend & Data Model (Weeks 1-4)

[ ] Set up a development instance of Neo4j.

[ ] Finalize and implement the core graph data model (nodes, relationships).

[ ] Adapt the Python worker to process a single, hardcoded text file.

[ ] Develop and test the "Triplet Extraction Module" with the OpenAI API.

[ ] Write the service to populate the Neo4j database with the extracted triplets.

Goal: Be able to manually trigger a script that reads a document and populates the graph.

Phase 2: End-to-End MVP (Weeks 5-8)

[ ] Build the basic user login and document upload UI.

[ ] Connect the UI to the backend, enabling file upload to S3.

[ ] Wire up the full asynchronous flow: UI -> Node.js -> RabbitMQ -> Python Worker -> OpenAI -> Neo4j.

[ ] Build a simple, non-visual query endpoint that can search for a node by name.

Goal: A user can upload a document and verify via a simple API call that the knowledge has been added to the graph.

Phase 3: Query & Visualization (Weeks 9-12)

[ ] Design and build the user-facing query interface in the frontend.

[ ] Integrate a graph visualization library.

[ ] Connect the UI to the backend query engine and render the results visually.

[ ] Implement the "show metadata on click" functionality.

Goal: A user can upload a document, ask a question about its contents, and see the answer as an interactive graph.

Phase 4: Collaboration & Refinement (Weeks 13+)

[ ] Implement logic to filter the graph view (e.g., "my contributions" vs. "all contributions").

[ ] Add user roles and permissions if necessary.

[ ] Conduct user testing and gather feedback to refine the UI and query capabilities.

[ ] Investigate and address issues of data conflict and redundancy.

Goal: A fully-featured, collaborative platform ready for initial user rollout.