Action Plan: Next Implementation Steps in Order

small features:

*convert the extract knowledge button INTO a status bar when clicked, and keep the logging at the bottom neatly.

* add automatic title-extraction from documents

* create signifance attribute for relationships + nodes, from GPT extraction to database ingestion and storage, to the UI

* add keyword filtering for the review page

* filtering dashboard minimizing/maximizing

*presentation mode for viewer

Phase 1: Connect Filtering and Reviewing (Immediate Priority)

Goal: Allow a user to filter the main graph view and then review only that specific slice of data. This makes the review process manageable.

Step 1.1: Implement Advanced Filtering on the Viewer Page.

Right now, you have a basic search. Expand this. The user should be able to filter the graph to show a "sub-graph" based on a specific concept.

When a user searches for a concept (e.g., "motor"), the viewer should highlight that node and its direct relationships. You could use color or size to distinguish the searched concept from its neighbors, as discussed.

Step 1.2: Link the Filtered View to the Review Queue.

Create a button on the Viewer page like "Review this Selection."

When a user clicks this, the Review Queue page should now only show the unverified relationships from the set of data they just filtered.

This directly addresses the feedback to "tie the visualization, the filtering with the review queue."
(allow user to shift click multiple nodes, then filter, then review those, as well)

Phase 2: Develop a Visual Language for the Graph

Goal: Make the graph more intuitive by using visual cues to represent different data properties, as Professor Candan suggested.

Step 2.1: Create a "Visual Alphabet" Document.

Start a simple markdown document to define your visual language. This creates consistency.

Example Definitions:

Color: Node color represents the primary search term (red) vs. its neighbors (blue).

Size: Node size represents its "significance" score from the GPT extraction.

Edge Thickness: Represents the number of documents that cite this relationship (the more sources, the thicker the line).

Border Style: A dashed border could indicate a relationship is unverified, while a solid border means it's verified.

Step 2.2: Implement the Visual Language in Cytoscape.

Begin implementing these rules. Start with the easiest ones, like using color for filtering and border style for verification status. Cytoscape has a rich API for dynamically styling nodes and edges based on their data properties.

Phase 3: Add an Export Feature

Goal: Allow users to export their filtered view of the graph, making the data portable.

Step 3.1: Create an "Export" Button on the Viewer + Review Page.

This button should only become active after a user has filtered the graph.

Step 3.2: Build the Export API Endpoint.

When the button is clicked, the frontend tells the backend what the current filter is (e.g., concept='motor').

The backend queries Neo4j for that sub-graph and formats the data into a simple text file (e.g., a list of nodes and edges in a JSON or CSV format).

The backend then sends this file back to the user's browser to be downloaded.

By following this order, you are building on your existing work in a logical sequence. You're first making the data easier to navigate (filtering), then easier to understand (visual language), and finally easier to share (export).


Phase 5: "Closing the Loop" - Advanced Review & Manual Annotation
Goal: Empower domain experts to not just verify AI output, but to actively curate and enrich the graph with their own knowledge. This addresses the final pieces of the human-in-the-loop quality control.

Step 5.1: Implement the "Edit" Functionality in the Review Queue.

When an expert clicks "Edit" on a relationship, create a simple modal form that allows them to correct typos in concept names or change the relationship type from a dropdown menu(or input a new one). This is a crucial curation tool.

Step 5.2: Implement Manual Edge Creation.

In the Viewer, allow a user to select two nodes and manually add a new relationship between them. This is for cases where the AI completely missed a connection that an expert knows exists. The user would provide the relationship type and the source text as evidence.

Step 5.3: Handle Reviewer Disagreements.

As discussed, experts might disagree. Your system should handle this gracefully.

Implementation: Instead of a single status property, a relationship should have a list of reviews, e.g., reviews: [{userId: 'expertA', vote: 'confirm'}, {userId: 'expertB', vote: 'reject'}].

Your visual language can then represent this conflict (e.g., a node with a yellow border) to signal areas of scientific debate.

Phase 6: Advanced Discovery - Pathway and Complex Queries
Goal: Move beyond simple concept lookups and enable users to ask complex questions that reveal multi-step connections across the entire knowledge graph. This is the core "synthesis" feature.

Step 6.1: Implement Pathway Finding.

Create a new search feature in the UI called "Find Path Between."

The user selects two concepts (e.g., "Drug X" and "Disease Z").

Backend: Your backend will execute a "shortest path" query in Neo4j to find if there is a chain of relationships connecting the two concepts, even if they never appear in the same paper.

Frontend: The viewer then visualizes this path, instantly showing the inferred, multi-document connection.

Step 6.2: Build a "Query Builder" Interface.

Create an advanced search interface that allows users to construct queries without writing code.

Example: A user could build a query like: "Show me all (:Gene) nodes that are [:TARGETED_BY] a (:Drug) and also [:IMPLICATED_IN] the (:Disease {name: 'Melanoma'})."

Phase 7: Improving AI Quality - Entity Resolution & RAG
Goal: Tackle the "data cleaning" and consistency issues that were deferred. This makes the AI smarter and the graph more accurate.

Step 7.1: Implement Entity Resolution.

Address the issue of synonyms (e.g., "digital communication" vs. "digital_communication").

Implementation: Create a feature where an expert can select two nodes in the graph and "merge" them, indicating they are the same concept. The backend would combine their relationships and sources onto a single canonical node.

Step 7.2: Introduce Retrieval Augmented Generation (RAG).

This is the final step to supercharge your ingestion pipeline. Before sending a new document to the LLM, first query your Neo4j database for concepts that are already mentioned in the document's text.

Implementation:

Extract text from the new PDF.

Scan the text for terms that already exist as nodes in your graph.

Modify the GPT prompt to include this context: "You are about to process a document. The following concepts already exist in our knowledge graph: ['Melanoma', 'BRAF', 'V600E_Mutation']. When you extract new information, please use these existing terms where appropriate."

This gives the LLM context, dramatically improving the consistency of its output and reducing the need for manual entity resolution.