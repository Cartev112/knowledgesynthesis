/**
 * AI Query - Natural language querying using Neo4j Aura Agent
 */
import { state } from '../state.js';
import { API } from '../utils/api.js';

export class AIQuery {
  constructor() {
    this.messages = [];
    this.isProcessing = false;
    this.settings = {
      scope: 'hybrid',
      k: 8
    };
  }

  async init() {
    console.log('AI Query initialized');
    this.renderUI();
    this.attachEventListeners();
  }

  renderUI() {
    const container = document.getElementById('ai-query-content');
    if (!container) return;

    container.innerHTML = `
      <!-- Header -->
      <div class="ai-query-header">
        <h2>
          <span>🤖</span>
          <span>AI Query Assistant</span>
        </h2>
        <p>Ask questions about your knowledge graph in natural language. Powered by Neo4j Aura Agent with vector similarity search.</p>
      </div>

      <!-- Main Content -->
      <div class="ai-query-main">
        <!-- Left Sidebar -->
        <div class="ai-query-sidebar">
          <div class="ai-query-settings">
            <div class="ai-query-section-title">Search Settings</div>
            
            <div class="ai-query-setting-group">
              <label for="ai-query-scope">Search Scope</label>
              <select id="ai-query-scope">
                <option value="hybrid">Hybrid (Entities + Documents)</option>
                <option value="entity">Entities Only</option>
                <option value="document">Documents Only</option>
              </select>
            </div>

            <div class="ai-query-setting-group">
              <label for="ai-query-k">Top K Results</label>
              <input type="number" id="ai-query-k" min="1" max="20" value="8" />
            </div>
          </div>
        </div>

        <!-- Right Chat Panel -->
        <div class="ai-query-chat-panel">
          <div class="ai-query-messages" id="ai-query-messages">
            <div class="ai-query-empty-state">
              <div class="ai-query-empty-icon">💬</div>
              <div class="ai-query-empty-title">Start a Conversation</div>
              <div class="ai-query-empty-text">
                Ask me anything about your knowledge graph. I'll search through entities and documents to provide accurate, cited answers.
              </div>
            </div>
          </div>

          <div class="ai-query-input-area">
            <div class="ai-query-input-wrapper">
              <textarea 
                id="ai-query-input" 
                class="ai-query-input" 
                placeholder="Ask a question about your knowledge graph..."
                rows="1"
              ></textarea>
              <button id="ai-query-send-btn" class="ai-query-send-btn">
                <span>Send</span>
                <span>🚀</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  attachEventListeners() {
    // Settings
    document.getElementById('ai-query-scope')?.addEventListener('change', (e) => {
      this.settings.scope = e.target.value;
    });

    document.getElementById('ai-query-k')?.addEventListener('change', (e) => {
      this.settings.k = parseInt(e.target.value) || 8;
    });

    // Send button
    document.getElementById('ai-query-send-btn')?.addEventListener('click', () => {
      this.sendQuery();
    });

    // Enter to send (Shift+Enter for new line)
    document.getElementById('ai-query-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendQuery();
      }
    });

    // Auto-resize textarea
    document.getElementById('ai-query-input')?.addEventListener('input', (e) => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
    });
  }

  async sendQuery() {
    const input = document.getElementById('ai-query-input');
    const question = input.value.trim();
    
    if (!question || this.isProcessing) return;

    // Add user message
    this.addMessage('user', question);
    input.value = '';
    input.style.height = 'auto';

    // Show loading
    this.isProcessing = true;
    this.updateSendButton(true);
    this.showLoading();

    try {
      // Call Aura Agent endpoint
      const response = await API.post('/api/agent/invoke', {
        input: question,
        body: {
          // Additional parameters can be passed here if needed
        }
      });

      this.hideLoading();

      // Parse and display response
      this.handleAgentResponse(response, question);

    } catch (error) {
      console.error('AI Query error:', error);
      this.hideLoading();
      this.addMessage('assistant', 'Sorry, I encountered an error processing your question. Please try again.', {
        error: true,
        errorMessage: error.message
      });
    } finally {
      this.isProcessing = false;
      this.updateSendButton(false);
    }
  }

  handleAgentResponse(response, question) {
    // Extract answer from Aura Agent response
    let answerText = '';
    let sources = [];
    let thinkingTraces = [];
    let retrievedContext = {
      entities: [],
      documents: []
    };

    // Parse the Aura Agent response structure
    if (response.content && Array.isArray(response.content)) {
      // Extract thinking traces
      const thinkingItems = response.content.filter(item => item.type === 'thinking');
      thinkingTraces = thinkingItems.map(item => item.thinking);

      // Find text content
      const textContent = response.content.find(item => item.type === 'text');
      if (textContent) {
        answerText = textContent.text;
      }

      // Find tool results for context
      const toolResults = response.content.filter(item => 
        item.type === 'cypher_template_tool_result' || 
        item.type === 'vector_similarity_tool_result'
      );

      // Extract sources from tool results
      toolResults.forEach(result => {
        if (result.output && result.output.records) {
          result.output.records.forEach(record => {
            // Try to extract document/source information
            if (record.contract_name || record.document_title) {
              sources.push({
                title: record.contract_name || record.document_title,
                id: record.contract_id || record.document_id,
                type: 'document'
              });
            }
          });
        }
      });
    } else if (typeof response === 'string') {
      answerText = response;
    } else if (response.answer) {
      // Fallback to local GraphRAG format
      answerText = response.answer;
      
      if (response.entities) {
        retrievedContext.entities = response.entities.slice(0, 5);
      }
      if (response.documents) {
        retrievedContext.documents = response.documents.slice(0, 5);
      }
      if (response.sources) {
        sources = response.sources.slice(0, 10);
      }
    }

    // Add assistant message with metadata
    this.addMessage('assistant', answerText || 'I received your question but could not generate an answer.', {
      sources,
      retrievedContext,
      thinkingTraces,
      question
    });
  }

  addMessage(role, content, metadata = {}) {
    const messagesContainer = document.getElementById('ai-query-messages');
    if (!messagesContainer) return;

    // Remove empty state if present
    const emptyState = messagesContainer.querySelector('.ai-query-empty-state');
    if (emptyState) {
      emptyState.remove();
    }

    const message = {
      role,
      content,
      metadata,
      timestamp: new Date()
    };
    this.messages.push(message);

    const messageEl = this.createMessageElement(message);
    messagesContainer.appendChild(messageEl);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  createMessageElement(message) {
    const div = document.createElement('div');
    div.className = `ai-query-message ${message.role}`;

    const avatar = document.createElement('div');
    avatar.className = 'ai-query-message-avatar';
    avatar.textContent = message.role === 'user' ? '👤' : '🤖';

    const contentWrapper = document.createElement('div');
    contentWrapper.style.flex = '1';

    const content = document.createElement('div');
    content.className = 'ai-query-message-content';
    
    // Format content with markdown-like rendering
    content.innerHTML = this.formatMessageContent(message.content);

    contentWrapper.appendChild(content);

    // Add thinking traces if available (for assistant messages)
    if (message.role === 'assistant' && message.metadata.thinkingTraces && message.metadata.thinkingTraces.length > 0) {
      const thinkingEl = this.createThinkingElement(message.metadata.thinkingTraces);
      content.appendChild(thinkingEl);
    }

    // Add sources if available
    if (message.metadata.sources && message.metadata.sources.length > 0) {
      const sourcesEl = this.createSourcesElement(message.metadata.sources);
      content.appendChild(sourcesEl);
    }

    // Add retrieved context if available
    if (message.metadata.retrievedContext) {
      const contextEl = this.createContextElement(message.metadata.retrievedContext);
      content.appendChild(contextEl);
    }

    // Add error if present
    if (message.metadata.error) {
      const errorEl = document.createElement('div');
      errorEl.className = 'ai-query-error';
      errorEl.innerHTML = `<span>⚠️</span><span>${message.metadata.errorMessage || 'An error occurred'}</span>`;
      content.appendChild(errorEl);
    }

    const time = document.createElement('div');
    time.className = 'ai-query-message-time';
    time.textContent = this.formatTime(message.timestamp);
    contentWrapper.appendChild(time);

    div.appendChild(avatar);
    div.appendChild(contentWrapper);

    return div;
  }

  formatMessageContent(content) {
    // Simple markdown-like formatting
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    // Format tables if present
    if (formatted.includes('|')) {
      formatted = this.formatTable(formatted);
    }

    return formatted;
  }

  formatTable(content) {
    const lines = content.split('<br>');
    let inTable = false;
    let tableHTML = '';
    let result = [];

    for (let line of lines) {
      if (line.includes('|')) {
        if (!inTable) {
          inTable = true;
          tableHTML = '<table style="width:100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem;">';
        }
        const cells = line.split('|').map(c => c.trim()).filter(c => c);
        const isHeader = line.includes('---');
        
        if (!isHeader) {
          tableHTML += '<tr>';
          cells.forEach(cell => {
            tableHTML += `<td style="border: 1px solid #e5e7eb; padding: 0.5rem;">${cell}</td>`;
          });
          tableHTML += '</tr>';
        }
      } else {
        if (inTable) {
          tableHTML += '</table>';
          result.push(tableHTML);
          tableHTML = '';
          inTable = false;
        }
        result.push(line);
      }
    }

    if (inTable) {
      tableHTML += '</table>';
      result.push(tableHTML);
    }

    return result.join('<br>');
  }

  createThinkingElement(thinkingTraces) {
    const div = document.createElement('div');
    div.className = 'ai-query-thinking';

    const title = document.createElement('div');
    title.className = 'ai-query-thinking-title';
    title.innerHTML = '<span>💭</span><span>Agent Thinking</span>';
    div.appendChild(title);

    const content = document.createElement('div');
    content.className = 'ai-query-thinking-content';
    
    // Show first thinking trace by default, hide rest
    if (thinkingTraces.length > 0) {
      content.textContent = thinkingTraces[0];
      
      // If there are more traces, add a toggle button
      if (thinkingTraces.length > 1) {
        const toggle = document.createElement('button');
        toggle.className = 'ai-query-thinking-toggle';
        toggle.textContent = `Show ${thinkingTraces.length - 1} more thinking step${thinkingTraces.length > 2 ? 's' : ''}`;
        
        let expanded = false;
        toggle.addEventListener('click', () => {
          expanded = !expanded;
          if (expanded) {
            content.textContent = thinkingTraces.join('\n\n---\n\n');
            toggle.textContent = 'Show less';
          } else {
            content.textContent = thinkingTraces[0];
            toggle.textContent = `Show ${thinkingTraces.length - 1} more thinking step${thinkingTraces.length > 2 ? 's' : ''}`;
          }
        });
        
        div.appendChild(toggle);
      }
    }

    div.appendChild(content);
    return div;
  }

  createSourcesElement(sources) {
    const div = document.createElement('div');
    div.className = 'ai-query-sources';

    const title = document.createElement('div');
    title.className = 'ai-query-sources-title';
    title.textContent = `📚 Sources (${sources.length})`;
    div.appendChild(title);

    const list = document.createElement('div');
    list.className = 'ai-query-source-list';

    sources.forEach(source => {
      const item = document.createElement('div');
      item.className = 'ai-query-source-item';
      
      const icon = document.createElement('span');
      icon.className = 'ai-query-source-icon';
      icon.textContent = '📄';
      
      const text = document.createElement('span');
      text.className = 'ai-query-source-text';
      text.textContent = source.title || source.document_id || 'Unknown';
      
      item.appendChild(icon);
      item.appendChild(text);

      if (source.page) {
        const page = document.createElement('span');
        page.className = 'ai-query-source-page';
        page.textContent = `p.${source.page}`;
        item.appendChild(page);
      }

      list.appendChild(item);
    });

    div.appendChild(list);
    return div;
  }

  createContextElement(context) {
    const div = document.createElement('div');
    div.className = 'ai-query-context';

    const title = document.createElement('div');
    title.className = 'ai-query-context-title';
    title.innerHTML = '<span>🔍</span><span>Retrieved Context</span>';
    div.appendChild(title);

    const items = document.createElement('div');
    items.className = 'ai-query-context-items';

    if (context.entities && context.entities.length > 0) {
      context.entities.forEach(entity => {
        const chip = document.createElement('span');
        chip.className = 'ai-query-context-chip';
        chip.textContent = `${entity.name || entity.id} (${entity.type || 'Entity'})`;
        items.appendChild(chip);
      });
    }

    if (context.documents && context.documents.length > 0) {
      context.documents.forEach(doc => {
        const chip = document.createElement('span');
        chip.className = 'ai-query-context-chip';
        chip.textContent = `📄 ${doc.title || doc.id}`;
        items.appendChild(chip);
      });
    }

    div.appendChild(items);
    return div;
  }

  showLoading() {
    const messagesContainer = document.getElementById('ai-query-messages');
    if (!messagesContainer) return;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'ai-query-message assistant';
    loadingDiv.id = 'ai-query-loading-message';

    const avatar = document.createElement('div');
    avatar.className = 'ai-query-message-avatar';
    avatar.textContent = '🤖';

    const content = document.createElement('div');
    content.className = 'ai-query-message-content';
    
    const loading = document.createElement('div');
    loading.className = 'ai-query-loading';
    loading.innerHTML = '<div class="ai-query-loading-dot"></div><div class="ai-query-loading-dot"></div><div class="ai-query-loading-dot"></div>';
    
    content.appendChild(loading);
    loadingDiv.appendChild(avatar);
    loadingDiv.appendChild(content);
    messagesContainer.appendChild(loadingDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  hideLoading() {
    const loadingMessage = document.getElementById('ai-query-loading-message');
    if (loadingMessage) {
      loadingMessage.remove();
    }
  }

  updateSendButton(disabled) {
    const btn = document.getElementById('ai-query-send-btn');
    if (btn) {
      btn.disabled = disabled;
    }
  }

  formatTime(date) {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  clearMessages() {
    this.messages = [];
    const messagesContainer = document.getElementById('ai-query-messages');
    if (messagesContainer) {
      messagesContainer.innerHTML = `
        <div class="ai-query-empty-state">
          <div class="ai-query-empty-icon">💬</div>
          <div class="ai-query-empty-title">Start a Conversation</div>
          <div class="ai-query-empty-text">
            Ask me anything about your knowledge graph. I'll search through entities and documents to provide accurate, cited answers.
          </div>
        </div>
      `;
    }
  }
}
