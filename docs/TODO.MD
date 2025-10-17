Step 1.2: Implement the RabbitMQ Job Queue.

Address the critical feedback on handling latency. Refactor the ingestion process to be fully asynchronous using RabbitMQ. The Node.js server should only place a job on the queue and immediately return a response to the user. The Python worker will process the queue in the background.

Step 1.3: Implement Pagination for the Viewer.

Address the second scalability issue. Modify the API endpoint that serves graph data to the viewer. Instead of sending all nodes at once, implement pagination or a "lazy loading" strategy. The frontend should only request the nodes and relationships needed for the current viewport, and fetch more as the user pans or zooms. Implement any other visualization optimizations to make the viewer as smooth as possible. 

Phase 2: Refine the Visual Language & Expert Tools

Goal: Incorporate the specific visual and functional feedback to make the tool more intuitive for researchers.

Step 2.1: Implement Edge Width Based on Source Count.

As discussed, the thickness of an edge should visually represent the number of sources that confirm that relationship. This is a key visual indicator of "consensus."

Step 2.2: Add "Edit" Capability for Node Types.

Implement the feature that allows an expert reviewer to change the type of a node (e.g., from "Device" to "Method") if the LLM has miscategorized it. Also allow a user to change the name of a document

Step 2.3: Refine the Visual Distinction of Node Types.

The prompt is generating too many granular node types. First, try to refine the prompt to use a smaller, more consistent set of categories. Then, consider using different shapes (e.g., circles for concepts, squares for methods) or a subtle color scheme to visually distinguish between these primary categories in the viewer.

Step 2.4 Node/Relationship taxonomy/hierarchy

One eventual goal of this system is to implement a comprehensive taxonomy/hierarchy of all entities, layered via abstraction via generalization. Obviously, we can't have the first information extraction LLM worker do all of this. Brainstorm the best ways to develop this. We could use an LLM. Then, implement this hierarchy, both in the index, and as a new page. 