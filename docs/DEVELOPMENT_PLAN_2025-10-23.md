# Knowledge Synthesis Platform - Development Plan
**Meeting Date:** October 23, 2025  
**Attendees:** Dr. K. Selcuk Candan, Dr. Belinda Akpa, Carter Whitworth, Abhinav Gorantla

---

## Executive Summary

This development plan outlines the strategic priorities, feature implementations, and technical decisions for the Knowledge Synthesis platform based on the October 23, 2025 team meeting. The platform is progressing well with core functionality in place, and the focus is now shifting toward user experience refinement, multi-user support, and intelligent querying capabilities.

---

## 1. Critical Infrastructure Issues

### 1.1 API Access & Cost Management
**Priority:** URGENT  
**Status:** Needs Resolution

**Current Situation:**
- Carter is currently paying for OpenAI API usage (~$1.20 per 1,000 papers)
- ChatGPT EDU access status unclear regarding API availability
- Cost will increase as extraction becomes more comprehensive (more triplets per paper, larger inputs/outputs)

**Action Items:**
1. **Abhinav to investigate:** Verify if ChatGPT EDU provides API access
   - Check if existing API keys are still valid
   - Determine token/credit limits if API access is available
   
2. **Dr. Candan to follow up:** 
   - Request API key specifically for this project if needed
   - Explore existing API key availability from other projects
   
3. **Immediate workaround:** If no API access, consider GPT interface-based extraction (not ideal for development)

**Success Criteria:**
- Carter no longer paying out of pocket
- Sustainable API access secured before public launch
- Cost monitoring system in place

---

## 2. User Management & Multi-User Support

### 2.1 User-Scoped Views
**Priority:** HIGH  
**Status:** Not Implemented

**Rationale:**
- Currently one unified graph for all users
- Users (especially Dr. Akpa) need to work on multiple independent problem spaces
- Need to prevent information overload and maintain focus

**Requirements:**

#### Phase 1: User Filtering (Immediate)
- **Default view:** Show only content created/extracted by current user
- **Filter by user:** Ability to view specific user's contributions
- **Collaborative view:** Option to view combined graph of selected users (e.g., "my content + Belinda's content")
- **Implementation:** Client-side filtering with user metadata on nodes/edges

**Database Schema:**
```cypher
// All nodes and relationships should track:
- created_by: user_id
- created_by_first_name
- created_by_last_name
- created_at: timestamp
```

#### Phase 2: Project/Workspace Scoping (Future)
- **Problem:** Dr. Akpa needs separate spaces for:
  - Plant biology research
  - Immune cell engineering
  - Other unrelated domains
  
- **Solution:** Project/workspace concept
  - Users can create multiple projects
  - Documents and extractions belong to specific projects
  - Can share projects with collaborators
  - Filter/view by project scope

**UI/UX Considerations:**
- Dropdown or sidebar to select active project/workspace
- Visual indicator of current scope (e.g., "Viewing: My Content" or "Viewing: Immune Cell Project")
- Easy toggle between "My View" and "All Content"
- Ability to expand view incrementally (start with mine, add collaborators)

**Technical Implementation:**
```javascript
// Example filter structure
{
  users: ['user_id_1', 'user_id_2'],  // Filter by users
  projects: ['project_id_1'],          // Filter by projects
  dateRange: { start: '2025-01-01', end: '2025-12-31' },
  entityTypes: ['Gene', 'Protein'],    // Optional: filter by entity types
}
```

---

## 3. Knowledge Extraction Strategy

### 3.1 Extraction Focus: Diversity vs. Connectedness
**Priority:** MEDIUM  
**Status:** Design Decision Needed

**Context:**
Carter raised the question: Should GPT focus on extracting:
- **Interconnected neighborhoods:** Dense clusters of concepts with many transitive relationships (A→B→C→A)
- **Isolated triplets:** More diverse, independent relationships

**Dr. Candan's Recommendation:** User-controlled parameter

**Use Cases:**

| Use Case | Strategy | Goal |
|----------|----------|------|
| Enriching existing graph | **Connectedness** | Find how new paper relates to existing knowledge |
| Exploring new domains | **Diversity** | Discover novel concepts not yet in graph |
| Literature review | **Balanced** | Both connected and diverse relationships |

**Proposed Implementation:**

#### Extraction Options UI
Add checkbox/toggle during document upload:

```
┌─────────────────────────────────────────┐
│ Document Upload Options                 │
├─────────────────────────────────────────┤
│ Extraction Strategy:                    │
│ ○ Seek Diversity (explore new concepts) │
│ ○ Seek Connectedness (relate to existing)│
│ ● Balanced (default)                    │
│                                         │
│ Max Relationships: [50] ▼               │
│                                         │
│ Extraction Context (optional):          │
│ [Text area for user guidance...]        │
└─────────────────────────────────────────┘
```

#### Prompt Engineering
Modify system prompt based on selection:

**Diversity Mode:**
```
"Prioritize extracting diverse, novel relationships that introduce 
new concepts and entities not commonly found in typical discussions 
of this topic. Focus on unique insights and less obvious connections."
```

**Connectedness Mode:**
```
"Prioritize extracting relationships that connect to concepts already 
present in the knowledge graph. Focus on how this document relates to, 
supports, or contradicts existing knowledge. Look for bridging concepts."
```

**Implementation Notes:**
- Pass existing graph context to GPT when in "Connectedness" mode
- Use entity embeddings to find related existing entities
- Provide top-K similar entities as context in extraction prompt

---

## 4. Visualization Features

### 4.1 3D Graph Visualization
**Priority:** LOW (Enhancement)  
**Status:** Implemented (Experimental)

**Team Consensus:**
- **Dr. Candan:** Neutral - adds flexibility but also complexity
- **Dr. Akpa:** Wants to test with real data before deciding
- **Carter:** Implemented as experiment

**Decision:** Keep as optional feature, gather user feedback

**Considerations:**
- More impressive visually, especially with large datasets
- May be harder to use for precise navigation
- Could be valuable for presentations/demos
- Toggle between 2D/3D should remain easy

**Action Items:**
1. Team to test 3D view with real research data
2. Gather feedback on usability vs. visual appeal
3. Consider making it a "presentation mode" vs. "work mode"

---

## 5. Document Discovery & Ingestion

### 5.1 Discovery Tab
**Priority:** HIGH  
**Status:** Implemented

**Current Features:**
- Search integration with arXiv and PubMed
- Direct PDF ingestion from search results
- Automatic detection of inaccessible PDFs
- Background processing (continues even if window closed)

**Feedback:**
- ✅ Feature well-received by team
- ✅ Simplifies workflow significantly

### 5.2 Auto-Ingestion System
**Priority:** LOW (Future Enhancement)  
**Status:** Proposed

**Carter's Proposal:** Automatic ingestion of research papers based on topics

**Team Decision:** Not recommended for primary workflow

**Rationale:**
1. **Cost concerns:** Could lead to unexpected large bills
2. **Expert curation value:** Dr. Akpa emphasized importance of expert-selected papers
3. **Quality over quantity:** Platform value is in curated, relevant knowledge

**Potential Implementation (if pursued):**
- User-defined ingestion limits (e.g., max 10 papers/day)
- Budget caps (e.g., max $5/month auto-ingestion)
- Approval queue (system suggests, user approves)
- Topic-based filters with confidence thresholds

**Alternative Approach:**
- "Suggested Papers" feature instead of auto-ingestion
- System recommends papers based on graph gaps
- User reviews and selects which to ingest

---

## 6. Email Notification System

### 6.1 Ingestion Completion Notifications
**Priority:** MEDIUM  
**Status:** Not Yet Implemented

**Requirements:**
- Notify users when document processing completes
- Include summary: document title, # relationships extracted
- Provide link to view results in graph
- Handle multiple simultaneous ingestions

**Use Cases:**
1. User uploads document and closes window
2. User uploads multiple documents via Discovery tab
3. Background processing takes several minutes

**Implementation Notes:**
- Already discussed in previous sessions
- Email service code exists but needs integration
- Consider in-app notifications as well (toast/banner)

**Email Template:**
```
Subject: ✅ Document Processed: [Document Title]

Hi [User Name],

Your document has been successfully processed and added to your knowledge graph!

📄 Document: [Title]
🔗 Relationships Extracted: [Count]
⏰ Processed: [Timestamp]

[View in Knowledge Graph Button]
```

---

## 7. Intelligent Querying with Neo4j Agents

### 7.1 Graph RAG Agent
**Priority:** HIGH  
**Status:** In Development

**Current Implementation:**
- Neo4j Aura Agent (beta feature) configured
- Three tools defined:
  1. Text-to-Cypher (natural language → Cypher query)
  2. Document embedding similarity search
  3. Entity/relationship embedding similarity search

**Strategic Decision on Embeddings:**

#### Dr. Candan's Guidance:
- **Primary focus:** Entity/node embeddings
- **Secondary (nice-to-have):** Document embeddings

**Rationale:**
- **Graph querying is the core value:** Users query the knowledge graph, not documents
- **Node embeddings as anchors:** Use entity embeddings to contextualize queries
- **Document similarity is orthogonal:** Different functionality, not the main focus
- **Resource allocation:** Prioritize what differentiates the platform

#### Implementation Priority:

**Phase 1: Entity-Based Querying (Primary)**
```cypher
// Example: Find entities similar to query
MATCH (e:Entity)
WHERE e.embedding IS NOT NULL
WITH e, gds.similarity.cosine(e.embedding, $query_embedding) AS similarity
WHERE similarity > 0.7
RETURN e.name, e.type, similarity
ORDER BY similarity DESC
LIMIT 10
```

**Phase 2: Graph Traversal from Similar Entities**
```cypher
// Expand from similar entities to find relationships
MATCH (e:Entity)-[r]->(o:Entity)
WHERE e.name IN $similar_entities
RETURN e.name, type(r), o.name, r.original_text, r.page_number
```

**Phase 3: Document Similarity (Optional Enhancement)**
```cypher
// Find similar documents (nice-to-have)
MATCH (d:Document)
WHERE d.embedding IS NOT NULL
WITH d, gds.similarity.cosine(d.embedding, $query_embedding) AS similarity
RETURN d.title, similarity
ORDER BY similarity DESC
```

### 7.2 Agent Tab UI
**Priority:** HIGH  
**Status:** UI Created, Functionality In Progress

**Target:** Functional by next week's meeting

**Features to Implement:**
- Natural language query input
- Display of agent reasoning/thinking process
- Visualization of retrieved context (entities, relationships)
- Source citations with links to original documents
- Ability to refine queries based on results

---

## 8. Competitive Analysis & Related Work

### 8.1 Cytoscape Integration Project
**Source:** Shared by Dr. Akpa from workshop presentation

**Key Points:**
- Similar concept: knowledge extraction + network visualization
- Uses Biological Expression Language (BEL)
- Integrated with Cytoscape (biology-focused network tool)
- Likely more domain-specific (biology only)

**Action Items:**
1. Review the preprint shared by Dr. Akpa
2. Identify unique features they have
3. Identify differentiators for our platform
4. Consider potential collaboration or integration opportunities

**Potential Differentiators:**
- Domain-agnostic (not just biology)
- Modern web-based interface
- Real-time collaboration features
- AI-powered querying (Graph RAG)
- User-friendly for non-technical researchers

---

## 9. Platform Readiness & Public Launch

### 9.1 Pre-Launch Checklist

**Infrastructure:**
- [ ] Resolve API access and cost management
- [ ] Implement user authentication and management
- [ ] Set up email notification system
- [ ] Configure production database (separate from dev)
- [ ] Implement rate limiting and usage quotas

**Core Features:**
- [ ] User-scoped views (filter by user)
- [ ] Project/workspace management
- [ ] Email notifications for ingestion completion
- [ ] Graph RAG agent fully functional
- [ ] Document discovery and ingestion working reliably

**User Experience:**
- [ ] Comprehensive user documentation
- [ ] Tutorial/onboarding flow for new users
- [ ] Example datasets/demo graphs
- [ ] Clear error messages and help text
- [ ] Mobile-responsive design (if applicable)

**Quality Assurance:**
- [ ] Test with multiple concurrent users
- [ ] Verify data isolation between users/projects
- [ ] Load testing for ingestion pipeline
- [ ] Security audit (authentication, authorization, data privacy)
- [ ] Backup and recovery procedures

**Legal/Administrative:**
- [ ] Terms of service
- [ ] Privacy policy
- [ ] Data retention policy
- [ ] Usage guidelines
- [ ] Attribution requirements for extracted knowledge

### 9.2 Launch Strategy

**Dr. Candan's Vision:** "Make it public soon so more people can benefit"

**Phased Rollout Recommendation:**

**Phase 1: Closed Beta (Current)**
- Team members + select collaborators
- Gather feedback on core functionality
- Identify and fix critical issues
- Refine user experience

**Phase 2: Limited Public Beta**
- Invite-only access
- Academic researchers in target domains
- Collect usage data and feedback
- Monitor costs and performance

**Phase 3: Open Public Launch**
- Public registration (with approval/waitlist if needed)
- Marketing to academic community
- Conference presentations and demos
- Publication of methodology paper

---

## 10. Technical Debt & Code Quality

### 10.1 Known Issues from TODO.md

**From User's TODO:**
- [ ] Fix index dropdown buttons
- [x] ~~Quality assure create relationship feature~~ (Completed)
- [x] ~~Fix edge "read more" button~~ (Completed)
- [x] ~~Remove merge feature + implement compare feature~~ (Completed)
- [ ] Documents ingested via discovery not visible in graph (CRITICAL)
- [ ] Verify shortest path feature

### 10.2 Code Quality Priorities

**Testing:**
- Unit tests for extraction pipeline
- Integration tests for ingestion workflow
- End-to-end tests for user workflows
- Performance benchmarks for large graphs

**Documentation:**
- API documentation (if exposing APIs)
- Architecture documentation
- Deployment guide
- Contribution guidelines (if open-sourcing)

**Monitoring:**
- Application performance monitoring (APM)
- Error tracking (e.g., Sentry)
- Usage analytics
- Cost tracking dashboard

---

## 11. Meeting Action Items Summary

### Immediate (This Week)

**Abhinav:**
- [ ] Investigate ChatGPT EDU API access
- [ ] Check validity of existing API keys
- [ ] Report findings to team

**Dr. Candan:**
- [ ] Read Carter's email with detailed questions
- [ ] Provide feedback on extraction strategy questions
- [ ] Follow up on API key request if needed
- [ ] Test the platform and provide feedback

**Dr. Akpa:**
- [ ] Test platform with real research papers
- [ ] Provide feedback on 3D visualization
- [ ] Share the Cytoscape preprint with team
- [ ] Test multi-domain use case (plant biology + immune cells)

**Carter:**
- [ ] Implement user-scoped view filtering
- [ ] Default view to show only user's own content
- [ ] Make Graph RAG agent tab functional
- [ ] Fix: Documents from discovery tab not appearing in graph
- [ ] Implement email notification system
- [ ] Add extraction strategy options (diversity vs. connectedness)

### Short-Term (Next 2 Weeks)

**Carter:**
- [ ] Implement project/workspace concept
- [ ] Add project selection UI
- [ ] Enhance agent querying with entity embeddings
- [ ] Create user documentation
- [ ] Set up usage monitoring

**Team:**
- [ ] Weekly testing and feedback sessions
- [ ] Decide on 3D visualization based on real usage
- [ ] Review Cytoscape paper and identify differentiators
- [ ] Plan public launch timeline

### Medium-Term (Next Month)

**Infrastructure:**
- [ ] Migrate to sustainable API access
- [ ] Implement comprehensive user management
- [ ] Set up production environment
- [ ] Create backup and recovery procedures

**Features:**
- [ ] Advanced filtering (by entity type, date, significance)
- [ ] Collaborative features (shared projects, comments)
- [ ] Export functionality (graph data, visualizations)
- [ ] Integration with reference managers (Zotero, Mendeley)

**Quality:**
- [ ] Comprehensive testing suite
- [ ] Performance optimization for large graphs
- [ ] Security audit
- [ ] Accessibility improvements

---

## 12. Design Principles & Philosophy

### 12.1 Core Values

**Expert Curation Over Automation**
- Dr. Akpa: "One of the beauties of what we're doing is it's expert curated"
- Platform should empower experts, not replace them
- Automation should assist, not dictate

**Simplicity Over Complexity**
- Dr. Candan: "I prefer simpler"
- Features should add clear value, not just complexity
- User experience should be intuitive

**Flexibility for Different Use Cases**
- Support diverse research domains
- Allow users to customize extraction and viewing
- Don't presume what users will want

**Collaboration and Knowledge Sharing**
- Enable cross-domain conversations
- Support multiple users working together
- Maintain proper attribution and provenance

### 12.2 User-Centered Design

**Progressive Disclosure:**
- Start with simple, focused view (user's own content)
- Allow expansion as needed (add collaborators, other projects)
- Advanced features available but not overwhelming

**Contextual Help:**
- Clear explanations of features
- Examples and tutorials
- Helpful error messages

**Feedback and Transparency:**
- Show progress during long operations
- Explain what the system is doing
- Provide confidence scores and sources

---

## 13. Success Metrics

### 13.1 Technical Metrics

**Performance:**
- Document ingestion time: < 2 minutes for typical paper
- Graph query response time: < 1 second for typical query
- UI responsiveness: < 100ms for interactions
- Uptime: > 99.5%

**Quality:**
- Extraction accuracy: > 85% (validated by domain experts)
- Relationship relevance: > 80% (user ratings)
- Query result quality: > 75% user satisfaction

**Scalability:**
- Support 100+ concurrent users
- Handle graphs with 100,000+ nodes
- Process 1,000+ documents/day

### 13.2 User Engagement Metrics

**Adoption:**
- Number of registered users
- Number of active users (weekly/monthly)
- Number of documents ingested
- Number of queries performed

**Retention:**
- User return rate (week-over-week)
- Session duration
- Feature usage patterns
- User-reported value

**Collaboration:**
- Number of shared projects
- Number of collaborative sessions
- Cross-domain knowledge connections
- Citations in publications

---

## 14. Risk Management

### 14.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API cost overrun | HIGH | MEDIUM | Implement quotas, monitoring, alerts |
| Performance degradation with large graphs | MEDIUM | HIGH | Optimize queries, implement pagination, caching |
| Data loss | HIGH | LOW | Regular backups, redundancy, testing |
| Security breach | HIGH | LOW | Security audit, encryption, access controls |

### 14.2 Product Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low user adoption | HIGH | MEDIUM | User testing, marketing, clear value prop |
| Competing solutions | MEDIUM | MEDIUM | Differentiation, continuous innovation |
| Extraction quality issues | HIGH | MEDIUM | Validation, user feedback, prompt tuning |
| Complexity overwhelming users | MEDIUM | HIGH | Simplified UI, progressive disclosure, tutorials |

---

## 15. Long-Term Vision

### 15.1 Future Enhancements (6-12 Months)

**Advanced AI Features:**
- Automatic hypothesis generation from graph patterns
- Contradiction detection across papers
- Gap analysis (what's missing from the graph)
- Trend analysis over time

**Enhanced Collaboration:**
- Real-time collaborative editing
- Discussion threads on nodes/edges
- Peer review and validation workflows
- Team analytics and insights

**Integration Ecosystem:**
- API for third-party tools
- Plugins for common research tools
- Export to standard formats (RDF, GraphML)
- Import from other knowledge bases

**Domain-Specific Features:**
- Customizable entity types per domain
- Domain-specific extraction templates
- Specialized visualizations (e.g., pathway diagrams for biology)
- Integration with domain databases (PubChem, UniProt, etc.)

### 15.2 Research Opportunities

**Publications:**
- Methodology paper on AI-assisted knowledge extraction
- Case studies in specific domains
- User study on cross-domain knowledge synthesis
- Comparison with existing tools

**Grants and Funding:**
- NSF grant for knowledge graph research
- NIH funding for biomedical applications
- Industry partnerships for domain-specific applications

**Academic Impact:**
- Tool for accelerating literature reviews
- Platform for interdisciplinary collaboration
- Resource for teaching knowledge synthesis
- Dataset for graph machine learning research

---

## 16. Conclusion

The Knowledge Synthesis platform is progressing excellently with strong core functionality in place. The immediate priorities are:

1. **Resolve API access and cost management** (blocking public launch)
2. **Implement user-scoped views** (critical for usability)
3. **Complete Graph RAG agent** (key differentiator)
4. **Fix discovery tab integration** (user-reported issue)

The team has a clear vision for the platform's value proposition: **expert-curated, AI-assisted knowledge synthesis that enables cross-domain collaboration**. With the planned enhancements and careful attention to user experience, the platform is well-positioned for successful public launch.

**Next Steps:**
- Team to test platform with real research data
- Weekly feedback sessions to refine features
- Resolve API access within 1-2 weeks
- Target public beta launch in 4-6 weeks

---

## Appendix A: Technical Architecture Notes

### Current Stack
- **Frontend:** JavaScript, modern web framework
- **Backend:** Python (FastAPI), Neo4j graph database
- **AI/ML:** OpenAI API (GPT-4o-mini), embeddings
- **Infrastructure:** Cloud-hosted (details TBD)

### Key Components
- Document ingestion pipeline
- Triplet extraction service
- Graph database (Neo4j)
- Vector embeddings (documents + entities)
- Graph RAG agent (Neo4j Aura Agent)
- 2D/3D visualization engine

### Data Model
```
Nodes:
- Entity (name, type, significance, embedding, created_by)
- Document (document_id, title, embedding, created_by)

Relationships:
- [EXTRACTED_FROM] (Entity → Document)
- [Dynamic relationship types] (Entity → Entity)
  Properties: original_text, confidence, page_number, sources, significance
```

---

## Appendix B: Meeting Participants

**Dr. K. Selcuk Candan**
- Role: Principal Investigator
- Focus: Architecture, strategy, technical guidance

**Dr. Belinda Akpa**
- Role: Domain Expert, User Representative
- Focus: Biomedical applications, user experience, cross-domain use cases

**Carter Whitworth**
- Role: Lead Developer
- Focus: Implementation, feature development, system design

**Abhinav Gorantla**
- Role: Research Assistant
- Focus: API access, infrastructure support

---

**Document Version:** 1.0  
**Last Updated:** October 23, 2025  
**Next Review:** October 30, 2025 (Weekly team meeting)
