// Neo4j schema initialization for Knowledge Synthesis graph

// Entities
// Unique identity defined by (name, type)
CREATE CONSTRAINT entity_nodekey IF NOT EXISTS
FOR (e:Entity)
REQUIRE (e.name, e.type) IS NODE KEY;

// Documents
// Each document has a unique, stable identifier
CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (d:Document)
REQUIRE d.document_id IS UNIQUE;

// Users
CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User)
REQUIRE u.username IS UNIQUE;

// Full text search index for entities and documents
CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
FOR (n:Entity|Document)
ON EACH [n.name, n.title];

// Relationship uniqueness at the semantic level is enforced by writing a single relationship type
// with arrays of source document ids and provenance. No constraint here; handled in write logic.

