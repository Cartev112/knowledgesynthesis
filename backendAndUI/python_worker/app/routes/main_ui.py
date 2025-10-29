"""
Main Unified UI - Knowledge Synthesis Platform
==============================================

MIGRATED TO NODE.JS SERVER
This route now redirects to the Node.js server which serves the frontend.
The UI has been migrated to:
- node-server/public/index.html
- node-server/public/css/*.css
- node-server/public/js/**/*.js

The Node.js server proxies API requests to this FastAPI backend.
"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse


router = APIRouter()


# Redirect to Node.js server for UI
@router.get("")
def serve_main_ui():
    """Redirect to Node.js server which now serves the frontend"""
    return RedirectResponse(url="http://127.0.0.1:3000/app")


# Keep the old HTML for reference (can be removed later)
_OLD_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Knowledge Synthesis Platform</title>
    
    <!-- ========================================
         CSS STYLES
         ======================================== -->
    <style>
      /* === BASE STYLES === */
      * { box-sizing: border-box; }
      html, body { height: 100%; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
      
      #header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      }
      
      #header h1 { margin: 0; font-size: 24px; font-weight: 600; }
      
      /* === HEADER & USER INFO === */
      #user-info {
        display: flex;
        align-items: center;
        gap: 12px;
        color: rgba(255,255,255,0.95);
      }
      
      #user-info button {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 6px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
      }
      
      #user-info button:hover { background: rgba(255,255,255,0.3); }
      
      /* === TAB NAVIGATION === */
      #tabs {
        display: flex;
        background: #f3f4f6;
        border-bottom: 2px solid #e5e7eb;
        padding: 0 24px;
      }
      
      .tab {
        padding: 14px 24px;
        cursor: pointer;
        border-bottom: 3px solid transparent;
        margin-bottom: -2px;
        font-weight: 500;
        color: #6b7280;
        transition: all 0.2s;
      }
      
      .tab:hover { color: #374151; }
      .tab.active { color: #667eea; border-bottom-color: #667eea; background: white; }
      
      .tab-content {
        display: none;
        height: calc(100vh - 120px);
        overflow: hidden;
      }
      
      .tab-content.active { display: block; }
      
      /* ==========================================
         INGESTION TAB STYLES
         ========================================== */
      #ingestion-panel {
        max-width: 1400px;
        margin: 20px auto;
        padding: 0 24px;
        height: calc(100vh - 180px);
        display: flex;
        align-items: center;
      }
      
      .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 24px 28px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        width: 100%;
      }
      
      .card h2 {
        margin: 0 0 20px 0;
        font-size: 20px;
        color: #111827;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
      }
      
      .ingestion-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 40px;
      }
      
      .custom-file-upload {
        display: inline-block;
        padding: 14px 28px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 15px;
        text-align: center;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
      }
      
      .custom-file-upload:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
      }
      
      .custom-file-upload:active {
        transform: translateY(0);
      }
      
      input[type="file"] {
        display: none;
      }
      
      .file-name-display {
        margin-top: 10px;
        padding: 10px 12px;
        background: #f3f4f6;
        border-radius: 6px;
        font-size: 13px;
        color: #374151;
        min-height: 40px;
        display: flex;
        align-items: center;
      }
      
      .form-group {
        margin-bottom: 16px;
      }
      
      .form-group label {
        display: block;
        font-weight: 600;
        margin-bottom: 6px;
        color: #374151;
      }
      
      .form-group .help-text {
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
      }
      
      input[type="file"],
      input[type="number"],
      input[type="text"],
      textarea,
      select {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        font-family: inherit;
      }
      
      textarea {
        resize: vertical;
        min-height: 100px;
      }
      
      .param-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      
      button.primary {
        background: #667eea;
        color: white;
        border: none;
        padding: 12px 32px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      button.primary:hover { background: #5568d3; }
      button.primary:disabled {
        background: #9ca3af;
        cursor: not-allowed;
      }
      
      /* Status Bar Styles - replaces button when active */
      #ingest-btn-container {
        margin-top: 16px;
        width: 100%;
      }
      
      #ingest-btn {
        width: 100%;
        padding: 14px;
        font-size: 16px;
      }
      
      #ingest-btn.as-status-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: default;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
      }
      
      #ingest-btn.as-status-bar .status-icon {
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      /* Viewport loading indicator animation */
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      #ingest-status {
        margin-top: 12px;
        padding: 12px;
        border-radius: 6px;
        display: none;
        font-size: 13px;
      }
      
      #ingest-status.success {
        display: block;
        background: #d1fae5;
        color: #065f46;
        border: 1px solid #6ee7b7;
      }
      
      #ingest-status.error {
        display: block;
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
      }
      
      #ingest-status.processing {
        display: block;
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #93c5fd;
      }
      
      /* Progress Bar Styles - now appears below status bar */
      .progress-container {
        margin-top: 8px;
        padding: 12px;
        background: #f9fafb;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        display: none;
      }
      
      .progress-container.active {
        display: block;
      }
      
      .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 13px;
        color: #374151;
        font-weight: 600;
      }
      
      .progress-bar-bg {
        width: 100%;
        height: 24px;
        background: #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        position: relative;
      }
      
      .progress-bar-fill {
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 12px;
        font-weight: 600;
      }
      
      .current-file-status {
        margin-top: 8px;
        font-size: 12px;
        color: #6b7280;
      }
      
      .file-list-status {
        margin-top: 12px;
        max-height: 200px;
        overflow-y: auto;
        border-top: 1px solid #e5e7eb;
        padding-top: 8px;
      }
      
      .file-status-item {
        padding: 6px 8px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .file-status-item.pending {
        background: #f3f4f6;
        color: #6b7280;
      }
      
      .file-status-item.processing {
        background: #dbeafe;
        color: #1e40af;
      }
      
      .file-status-item.success {
        background: #d1fae5;
        color: #065f46;
      }
      
      .file-status-item.error {
        background: #fee2e2;
        color: #991b1b;
      }
      
      /* ==========================================
         VIEWING TAB STYLES (Graph Visualization)
         ========================================== */
      #viewing-panel {
        position: relative;
        height: 100%;
        width: 100%;
        overflow: hidden;
      }
      
      #cy-container {
        position: relative;
        background: #fafafa;
        overflow: hidden;
        height: 100%;
        width: 100%;
      }
      
      #cy { 
        width: 100%; 
        height: 100%;
      }
      
      /* Legend Modal Overlay */
      #legend-modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        justify-content: center;
        align-items: center;
      }
      
      #legend-modal-overlay.visible {
        display: flex;
      }
      
      #legend-modal {
        background: white;
        border-radius: 12px;
        max-width: 600px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      }
      
      .legend-section {
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e5e7eb;
      }
      
      .legend-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
      }
      
      .legend-title {
        font-weight: 600;
        color: #374151;
        margin-bottom: 4px;
      }
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 4px 0;
        color: #6b7280;
      }
      
      .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid #d1d5db;
      }
      
      .legend-line {
        width: 24px;
        height: 3px;
        border-radius: 2px;
      }
      
      /* Floating Action Buttons */
      .fab-container {
        position: fixed;
        bottom: 24px;
        left: 24px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        z-index: 100;
      }
      
      .fab {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
        cursor: pointer;
        font-size: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
        position: relative;
      }
      
      .fab:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
      }
      
      .fab:active {
        transform: scale(0.95);
      }
      
      .fab.export {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4);
      }
      
      .fab.export:hover {
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.5);
      }
      
      .fab.review {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
      }
      
      .fab.review:hover {
        box-shadow: 0 6px 16px rgba(245, 158, 11, 0.5);
      }
      
      .fab.legend {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
      }
      
      .fab.legend:hover {
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
      }
      
      .fab-tooltip {
        position: absolute;
        left: 70px;
        background: #1f2937;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s;
        font-weight: 500;
      }
      
      .fab:hover .fab-tooltip {
        opacity: 1;
      }
      
      /* Hide FABs on non-viewing tabs */
      .fab-container.hidden {
        display: none;
      }
      
      .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
      }
      
      .status-unverified { background: #fef3c7; color: #92400e; }
      .status-verified { background: #d1fae5; color: #065f46; }
      .status-incorrect { background: #fee2e2; color: #991b1b; }
      
      /* === QUERY BUILDER STYLES === */
      .template-btn {
        width: 100%;
        padding: 12px 16px;
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        text-align: left;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .template-btn:hover {
        border-color: #8b5cf6;
        background: #f5f3ff;
        color: #7c3aed;
      }
      
      .query-result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        transition: all 0.2s;
      }
      
      .query-result-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-color: #8b5cf6;
      }
    </style>
    
    <!-- === EXTERNAL DEPENDENCIES === -->
    <script src="https://unpkg.com/cytoscape@3.29.2/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
    
    <style>
      /* ==========================================
         NEW VIEWER UI STYLES
         ========================================== */
      
      /* Edge & Node Tooltips */
      #edge-tooltip, #node-tooltip {
        position: fixed;
        background: white;
        border: 2px solid #8b5cf6;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        pointer-events: auto;
        display: none;
        max-width: 300px;
        font-size: 13px;
      }
      
      #edge-tooltip.visible, #node-tooltip.visible {
        display: block;
      }
      
      #edge-tooltip .tooltip-header, #node-tooltip .tooltip-header {
        font-weight: 600;
        color: #111827;
        margin-bottom: 8px;
        font-size: 14px;
      }
      
      #edge-tooltip .tooltip-relation {
        color: #8b5cf6;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
        display: block;
        margin: 4px 0;
      }
      
      #edge-tooltip .tooltip-info, #node-tooltip .tooltip-info {
        margin: 6px 0;
        color: #6b7280;
        font-size: 12px;
      }
      
      #edge-tooltip .tooltip-btn, #node-tooltip .tooltip-btn {
        margin-top: 10px;
        padding: 6px 12px;
        background: #8b5cf6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 500;
        width: 100%;
      }
      
      #edge-tooltip .tooltip-btn:hover, #node-tooltip .tooltip-btn:hover {
        background: #7c3aed;
      }
      
      /* Edge & Node Details Modals */
      #edge-modal-overlay, #node-modal-overlay, #document-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.6);
        z-index: 2000;
        display: none;
        align-items: center;
        justify-content: center;
      }
      
      #edge-modal-overlay.visible, #node-modal-overlay.visible, #document-modal-overlay.visible {
        display: flex;
      }
      
      #edge-modal, #node-modal, #document-modal {
        background: white;
        border-radius: 12px;
        max-width: 700px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      }
      
      #edge-modal .modal-header, #node-modal .modal-header, #document-modal .modal-header, #legend-modal .modal-header {
        padding: 20px 24px;
        border-bottom: 2px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        background: white;
        z-index: 1;
      }
      
      #edge-modal .modal-title, #node-modal .modal-title, #document-modal .modal-title, #legend-modal .modal-title {
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin: 0;
      }
      
      #edge-modal .modal-close, #node-modal .modal-close, #document-modal .modal-close, #legend-modal .modal-close {
        background: transparent;
        border: none;
        font-size: 28px;
        cursor: pointer;
        color: #6b7280;
        line-height: 1;
        padding: 0;
        width: 32px;
        height: 32px;
      }
      
      #edge-modal .modal-close:hover, #node-modal .modal-close:hover, #document-modal .modal-close:hover, #legend-modal .modal-close:hover {
        color: #111827;
      }
      
      #edge-modal .modal-body, #node-modal .modal-body, #document-modal .modal-body, #legend-modal .modal-body {
        padding: 24px;
      }
      
      #edge-modal .modal-section, #node-modal .modal-section, #document-modal .modal-section, #legend-modal .modal-section {
        margin-bottom: 20px;
      }
      
      #edge-modal .modal-section-title, #node-modal .modal-section-title, #document-modal .modal-section-title, #legend-modal .modal-section-title {
        font-size: 14px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
      }
      
      #edge-modal .modal-section-content, #node-modal .modal-section-content, #document-modal .modal-section-content, #legend-modal .modal-section-content {
        font-size: 14px;
        color: #374151;
        line-height: 1.6;
      }
      
      #edge-modal .modal-relation {
        display: inline-block;
        background: #ede9fe;
        color: #7c3aed;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      
      #edge-modal .modal-badge, #node-modal .modal-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 4px;
      }
      
      #edge-modal .badge-verified, #node-modal .badge-verified {
        background: #d1fae5;
        color: #065f46;
      }
      
      #edge-modal .badge-unverified, #node-modal .badge-unverified {
        background: #f3f4f6;
        color: #6b7280;
      }
      
      #edge-modal .badge-negative {
        background: #fee2e2;
        color: #991b1b;
      }
      
      #edge-modal .original-text-box {
        background: #f9fafb;
        border-left: 4px solid #8b5cf6;
        padding: 16px;
        border-radius: 6px;
        font-style: italic;
        color: #374151;
        line-height: 1.7;
      }
      
      /* Dynamic Index Panel */
      #index-panel {
        position: fixed;
        right: 0;
        top: 115px;
        bottom: 0;
        width: 320px;
        background: white;
        border-left: 2px solid #e5e7eb;
        box-shadow: -4px 0 12px rgba(0,0,0,0.05);
        overflow-y: auto;
        padding: 20px;
        z-index: 100;
        transition: transform 0.3s ease;
      }
      
      #index-panel.hidden {
        transform: translateX(100%);
      }
      
      #index-panel .index-header {
        display: flex;
        flex-direction: column;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #8b5cf6;
      }
      
      #index-panel .index-title {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
        margin: 0 0 4px 0;
      }
      
      #index-panel .index-count {
        font-size: 12px;
        color: #6b7280;
        font-weight: 500;
      }
      
      #index-panel .index-section {
        margin-bottom: 24px;
      }
      
      #index-panel .index-section-title {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      
      #index-panel .index-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      
      #index-panel .index-item {
        padding: 8px 12px;
        margin-bottom: 4px;
        background: #f9fafb;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 13px;
        color: #374151;
        border-left: 3px solid transparent;
      }
      
      #index-panel .index-item:hover {
        background: #ede9fe;
        border-left-color: #8b5cf6;
        transform: translateX(4px);
      }
      
      #index-panel .index-item.highlighted {
        background: #ede9fe;
        border-left-color: #7c3aed;
        font-weight: 600;
      }
      
      /* Document Items in Index */
      #index-panel .doc-item {
        padding: 10px 12px;
        margin-bottom: 6px;
        background: #fef3c7;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 13px;
        color: #92400e;
        border-left: 3px solid transparent;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      #index-panel .doc-item:hover {
        background: #fde68a;
        border-left-color: #f59e0b;
        transform: translateX(4px);
      }
      
      #index-panel .doc-item.active {
        background: #fde68a;
        border-left-color: #d97706;
        font-weight: 600;
      }
      
      #index-panel .doc-toggle {
        width: 16px;
        height: 16px;
        border: 2px solid #d97706;
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 10px;
        background: white;
      }
      
      #index-panel .doc-item.active .doc-toggle {
        background: #f59e0b;
        color: white;
      }
      
      #index-panel .doc-name {
        flex: 1;
        font-weight: 500;
      }
      
      #index-panel .index-item-type {
        font-size: 10px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-left: 6px;
      }
      
      #index-panel .index-relationship {
        padding: 6px 10px;
        margin-bottom: 3px;
        background: #f9fafb;
        border-radius: 4px;
        font-size: 12px;
        color: #6b7280;
        line-height: 1.4;
      }
      
      #index-panel .index-relationship .rel-arrow {
        color: #8b5cf6;
        font-weight: 700;
        margin: 0 4px;
      }
      
      /* Index Toggle Button */
      #index-toggle-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
        cursor: pointer;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 200;
        transition: all 0.3s;
      }
      
      #index-toggle-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
      }
      
      #index-toggle-btn:active {
        transform: scale(0.95);
      }
      
      #index-toggle-btn.index-visible {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
      }
      
      /* Visual Legend Toggle Button */
      #legend-toggle-btn {
        position: fixed;
        bottom: 24px;
        right: 100px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        cursor: pointer;
        font-size: 24px;
        align-items: center;
        justify-content: center;
        z-index: 99;
        transition: all 0.3s;
      }
      
      #legend-toggle-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
      }
      
      #legend-toggle-btn:active {
        transform: scale(0.95);
      }
    </style>
  </head>
  <body>
    <!-- ========================================
         HTML STRUCTURE
         ======================================== -->
    
    <!-- === HEADER === -->
    <div id="header">
      <h1>Knowledge Synthesis Platform</h1>
      <div id="user-info">
        <span>👤 <span id="username">Guest</span></span>
        <button onclick="logout()">Logout</button>
      </div>
    </div>
    
    <!-- === TAB NAVIGATION === -->
    <div id="tabs">
      <div class="tab active" onclick="switchTab('ingestion')">📤 Ingestion</div>
      <div class="tab" onclick="switchTab('viewing')">🔍 Viewing</div>
      <div class="tab" onclick="switchTab('query-builder')">🔎 Query Builder</div>
      <div class="tab" onclick="window.open('/review-ui', '_blank')">✅ Review Queue</div>
    </div>
    
    <!-- ==========================================
         INGESTION TAB
         ========================================== -->
    <div id="ingestion-tab" class="tab-content active">
      <div id="ingestion-panel">
        <div class="card">
          <h2>📤 Document Ingestion & Knowledge Extraction</h2>
          
          <div class="ingestion-grid">
            <!-- Left Column: Document Upload -->
            <div>
              <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #374151; font-weight: 600;">Document Source</h3>
              
              <div class="form-group">
                <label>Upload PDF File(s)</label>
                <label for="pdf-file" class="custom-file-upload">
                  📄 Choose PDF Files
                </label>
                <input type="file" id="pdf-file" accept=".pdf" multiple onchange="displayFileName()" />
                <div id="file-name" class="file-name-display">No files selected</div>
              </div>
              
              <div class="form-group">
                <label>Or Paste Text Directly</label>
                <textarea id="text-input" placeholder="Paste your document text here..." style="min-height: 90px;"></textarea>
                <div class="help-text">You can paste raw text instead of uploading a file</div>
              </div>
              
              <div class="form-group">
                <label>Extraction Context (Optional)</label>
                <textarea id="extraction-context" placeholder="e.g., I'm interested in proteins and their functional relationships, drug-target interactions, or disease mechanisms..." style="min-height: 80px;"></textarea>
                <div class="help-text">Guide the AI: describe what types of relationships you're most interested in</div>
              </div>
            </div>
            
            <!-- Right Column: Extraction Parameters -->
            <div>
              <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #374151; font-weight: 600;">Extraction Settings</h3>
              
              <div class="form-group">
                <label style="display: flex; align-items: center; cursor: pointer; user-select: none;">
                  <input type="checkbox" id="use-graph-context" style="width: auto; margin-right: 10px; cursor: pointer;" onchange="toggleGraphContext()" />
                  <span style="font-weight: 600;">Use Selected Graph as Context</span>
                </label>
                <div class="help-text" id="graph-context-help" style="color: #9ca3af;">
                  Select nodes/edges in the Viewer, or filter by documents/relationships, then specify your extraction intent below
                </div>
                <div id="graph-context-status" style="display: none; margin-top: 8px; padding: 10px; background: #dbeafe; border-left: 3px solid #3b82f6; border-radius: 4px; font-size: 13px; color: #1e40af;">
                  <strong>Context Ready:</strong> <span id="graph-context-count">0</span> concepts selected
                </div>
                
                <!-- Context Intent Options (shown when context is enabled) -->
                <div id="context-intent-options" style="display: none; margin-top: 12px; padding: 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;">
                  <div style="font-weight: 600; margin-bottom: 8px; color: #374151; font-size: 13px;">Extraction Intent:</div>
                  <div style="display: flex; flex-direction: column; gap: 8px;">
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 13px;">
                      <input type="checkbox" id="intent-complements" style="width: auto; margin-right: 8px; cursor: pointer;" checked />
                      <span>Find relationships that <strong>complement</strong> existing knowledge</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 13px;">
                      <input type="checkbox" id="intent-conflicts" style="width: auto; margin-right: 8px; cursor: pointer;" checked />
                      <span>Find relationships that <strong>conflict with</strong> existing knowledge</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 13px;">
                      <input type="checkbox" id="intent-extends" style="width: auto; margin-right: 8px; cursor: pointer;" checked />
                      <span>Find relationships that <strong>extend</strong> existing knowledge</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 13px;">
                      <input type="checkbox" id="intent-distinct" style="width: auto; margin-right: 8px; cursor: pointer;" />
                      <span>Find relationships <strong>distinct from</strong> existing knowledge</span>
                    </label>
                  </div>
                  <div class="help-text" style="margin-top: 8px; font-size: 12px;">
                    Select one or more intents to guide extraction. If none selected, extraction will be neutral.
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>Max Concepts</label>
                <input type="number" id="max-concepts" value="100" min="10" max="500" />
                <div class="help-text">Maximum number of entities to extract (10-500)</div>
              </div>
              
              <div class="form-group">
                <label>Max Relationships</label>
                <input type="number" id="max-relationships" value="50" min="10" max="200" />
                <div class="help-text">Maximum number of triplets to extract (10-200)</div>
              </div>
              
              <div class="form-group">
                <label>Extraction Model</label>
                <select id="model-select">
                  <option value="gpt-4o-mini">GPT-4o Mini (Fast, Cost-effective)</option>
                  <option value="gpt-4o">GPT-4o (Higher Quality)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
                <div class="help-text">AI model for knowledge extraction</div>
              </div>
              
              <div id="ingest-btn-container">
                <button class="primary" id="ingest-btn" onclick="ingestDocument()">
                  🚀 Extract Knowledge
                </button>
              </div>
              
              <!-- Progress Bar -->
              <div id="progress-container" class="progress-container">
                <div class="progress-header">
                  <span id="progress-text">Processing...</span>
                  <span id="progress-count">0 / 0</span>
                </div>
                <div class="progress-bar-bg">
                  <div id="progress-bar-fill" class="progress-bar-fill" style="width: 0%;">
                    <span id="progress-percentage">0%</span>
                  </div>
                </div>
                <div id="current-file-status" class="current-file-status"></div>
                <div id="file-list-status" class="file-list-status"></div>
              </div>
              
              <div id="ingest-status"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- ==========================================
         VIEWING TAB (Graph Visualization)
         ========================================== -->
    <div id="viewing-tab" class="tab-content">
      <div id="viewing-panel">
        <div id="cy-container">
          <div id="cy"></div>
          
    <!-- Edge Hover Tooltip -->
    <div id="edge-tooltip">
      <div class="tooltip-header">
        <span id="tooltip-source"></span>
        <span class="tooltip-relation" id="tooltip-relation"></span>
        <span id="tooltip-target"></span>
            </div>
      <div class="tooltip-info" id="tooltip-confidence"></div>
      <div class="tooltip-info" id="tooltip-significance"></div>
      <button class="tooltip-btn" id="tooltip-read-more">📖 Read More</button>
            </div>
    
    <!-- Node Hover Tooltip -->
    <div id="node-tooltip">
      <div class="tooltip-header" id="node-tooltip-label"></div>
      <div class="tooltip-info" id="node-tooltip-type"></div>
      <div class="tooltip-info" id="node-tooltip-significance"></div>
      <button class="tooltip-btn" id="node-tooltip-read-more">📖 Read More</button>
              </div>

    <!-- Edge Details Modal -->
    <div id="edge-modal-overlay">
      <div id="edge-modal">
        <div class="modal-header">
          <h2 class="modal-title">Relationship Details</h2>
          <button class="modal-close" onclick="closeEdgeModal()">×</button>
              </div>
        <div class="modal-body" id="edge-modal-content">
          <!-- Content populated dynamically -->
        </div>
      </div>
    </div>
    
    <!-- Node Details Modal -->
    <div id="node-modal-overlay">
      <div id="node-modal">
        <div class="modal-header">
          <h2 class="modal-title">Node Details</h2>
          <button class="modal-close" onclick="closeNodeModal()">×</button>
        </div>
        <div class="modal-body" id="node-modal-content">
          <!-- Content populated dynamically -->
        </div>
      </div>
    </div>
    
    <!-- Document Details Modal -->
    <div id="document-modal-overlay">
      <div id="document-modal">
        <div class="modal-header">
          <h2 class="modal-title">Document Details</h2>
          <button class="modal-close" onclick="closeDocumentModal()">×</button>
        </div>
        <div class="modal-body" id="document-modal-content">
          <!-- Content populated dynamically -->
        </div>
      </div>
    </div>
    
    <!-- Visual Legend Modal -->
    <div id="legend-modal-overlay">
      <div id="legend-modal">
        <div class="modal-header">
          <h2 class="modal-title">📊 Visual Guide</h2>
          <button class="modal-close" onclick="closeLegendModal()">×</button>
        </div>
        <div class="modal-body">
          <div class="legend-section">
            <div class="modal-section-title">Node Colors</div>
            <div class="modal-section-content">
              <div class="legend-item">
                <div class="legend-color" style="background: #667eea;"></div>
                <span>Default Entity</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #dc2626;"></div>
                <span>Searched/Highlighted</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #f59e0b;"></div>
                <span>Neighbor</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #8b5cf6;"></div>
                <span>Multi-Selected</span>
              </div>
            </div>
          </div>
          
          <div class="legend-section">
            <div class="modal-section-title">Node Size</div>
            <div class="modal-section-content">
              <div class="legend-item">
                <span style="font-size: 10px;">●</span>
                <span>Low significance (1-2)</span>
              </div>
              <div class="legend-item">
                <span style="font-size: 14px;">●</span>
                <span>Medium significance (3)</span>
              </div>
              <div class="legend-item">
                <span style="font-size: 18px;">●</span>
                <span>High significance (4-5)</span>
              </div>
            </div>
          </div>
          
          <div class="legend-section">
            <div class="modal-section-title">Edge Styles</div>
            <div class="modal-section-content">
              <div class="legend-item">
                <div class="legend-line" style="background: #94a3b8;"></div>
                <span>Unverified</span>
              </div>
              <div class="legend-item">
                <div class="legend-line" style="background: #059669;"></div>
                <span>Verified</span>
              </div>
              <div class="legend-item">
                <div class="legend-line" style="background: #dc2626; border: 1px dashed #dc2626; background: transparent;"></div>
                <span>Incorrect</span>
              </div>
              <div class="legend-item">
                <div class="legend-line" style="background: #94a3b8; border-top: 2px dotted #94a3b8; background: transparent;"></div>
                <span>Negative relation</span>
              </div>
            </div>
          </div>
          
          <div class="legend-section">
            <div class="modal-section-title">Edge Width</div>
            <div class="modal-section-content">
              <span style="font-size: 13px;">Width increases with significance + source count</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Floating Action Buttons (only visible on viewing tab when nodes selected) -->
    <div class="fab-container hidden" id="fab-container">
      <button class="fab" onclick="openManualRelationshipFab()" title="Create Relationship">
        <span>➕</span>
        <span class="fab-tooltip">Create Relationship</span>
      </button>
      <button class="fab" onclick="openShortestPathFab()" title="Shortest Path">
        <span>🔍</span>
        <span class="fab-tooltip">Shortest Path</span>
      </button>
      <button class="fab export" onclick="openExportFab()" title="Export">
        <span>💾</span>
        <span class="fab-tooltip">Export</span>
      </button>
      <button class="fab review" onclick="openReviewFab()" title="Review">
        <span>✅</span>
        <span class="fab-tooltip">Review Queue</span>
      </button>
    </div>
    
    <!-- Visual Legend Toggle Button (always visible on viewer page) -->
    <button id="legend-toggle-btn" onclick="toggleLegend()" title="Visual Guide" style="display: none;">
      📊
    </button>
            
    <!-- Dynamic Index Panel -->
    <div id="index-panel" class="hidden">
      <div class="index-header">
        <h3 class="index-title">📋 Graph Index</h3>
        <div class="index-count" id="index-count">0 concepts, 0 relationships, 0 documents</div>
              </div>
      
      <!-- Index Filters -->
      <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
        <select id="index-view-filter" onchange="filterIndex()" style="width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; margin-bottom: 8px;">
          <option value="all">All Items</option>
          <option value="documents">Documents Only</option>
          <option value="concepts">Concepts Only</option>
          <option value="relationships">Relationships Only</option>
        </select>
        <select id="index-type-filter" onchange="filterIndex()" style="width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;">
          <option value="">All Types</option>
          <!-- Populated dynamically -->
        </select>
              </div>
      
      <div class="index-section" id="documents-section">
        <div class="index-section-title">
          📄 Documents (<span id="documents-count">0</span>)
              </div>
        <div id="documents-list">
          <!-- Populated dynamically -->
        </div>
      </div>
      
      <div class="index-section" id="concepts-section">
        <div class="index-section-title">
          🔵 Concepts (<span id="concepts-count">0</span>)
        </div>
        <ul class="index-list" id="concepts-list">
          <!-- Populated dynamically -->
        </ul>
      </div>
      
      <div class="index-section" id="relationships-section">
        <div class="index-section-title">
          🔗 Relationships (<span id="relationships-count">0</span>)
        </div>
        <div id="relationships-list">
          <!-- Populated dynamically -->
        </div>
      </div>
    </div>

    <!-- Index Toggle Button -->
    <button id="index-toggle-btn" onclick="toggleIndex()" title="Toggle Index">
      📋
              </button>
    
    <!-- ==========================================
         QUERY BUILDER TAB
         ========================================== -->
    <div id="query-builder-tab" class="tab-content">
      <div style="max-width: 1400px; margin: 20px auto; padding: 0 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: calc(100vh - 180px);">
        
        <!-- Left Panel: Query Builder -->
        <div style="display: flex; flex-direction: column; gap: 16px; overflow-y: auto;">
          
          <!-- Pattern Builder Section -->
          <div class="card">
            <h2 style="margin: 0 0 16px 0; font-size: 20px; color: #111827; border-bottom: 2px solid #8b5cf6; padding-bottom: 8px;">
              🔧 Pattern Builder
            </h2>
            
            <!-- Pattern Visual Preview -->
            <div id="pattern-preview" style="background: #f9fafb; border: 2px dashed #d1d5db; border-radius: 8px; padding: 20px; margin-bottom: 20px; min-height: 80px; display: flex; align-items: center; justify-content: center; font-family: monospace; font-size: 14px; color: #374151;">
              Select a template or build your own pattern
            </div>
            
            <!-- Node 1 -->
            <div style="margin-bottom: 16px;">
              <label style="display: block; font-weight: 600; margin-bottom: 6px; color: #374151; font-size: 14px;">
                📍 First Node Type
              </label>
              <select id="node1-type" onchange="updatePatternPreview()" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                <option value="">-- Any Type --</option>
                <!-- Options will be populated dynamically from database -->
              </select>
              
              <label style="display: block; font-weight: 500; margin-top: 8px; margin-bottom: 4px; color: #6b7280; font-size: 12px;">
                Filter by name (optional)
              </label>
              <input type="text" id="node1-name" placeholder="e.g., Aspirin" onkeyup="updatePatternPreview()" style="width: 100%; padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;" />
              </div>
            
            <!-- Relationship -->
            <div style="margin-bottom: 16px;">
              <label style="display: block; font-weight: 600; margin-bottom: 6px; color: #374151; font-size: 14px;">
                ➡️ Relationship Type
              </label>
              <select id="relationship-type" onchange="updatePatternPreview()" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                <option value="">-- Any Relationship --</option>
                <!-- Options will be populated dynamically from database -->
              </select>
            </div>
            
            <!-- Node 2 -->
            <div style="margin-bottom: 20px;">
              <label style="display: block; font-weight: 600; margin-bottom: 6px; color: #374151; font-size: 14px;">
                📍 Second Node Type
              </label>
              <select id="node2-type" onchange="updatePatternPreview()" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                <option value="">-- Any Type --</option>
                <!-- Options will be populated dynamically from database -->
              </select>
              
              <label style="display: block; font-weight: 500; margin-top: 8px; margin-bottom: 4px; color: #6b7280; font-size: 12px;">
                Filter by name (optional)
              </label>
              <input type="text" id="node2-name" placeholder="e.g., Cancer" onkeyup="updatePatternPreview()" style="width: 100%; padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;" />
            </div>
            
            <!-- Advanced Options -->
            <div style="margin-bottom: 20px; padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px;">
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; color: #92400e;">
                <input type="checkbox" id="verified-only-query" onchange="updatePatternPreview()" />
                <strong>Show only verified relationships</strong>
              </label>
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; color: #92400e; margin-top: 8px;">
                <input type="checkbox" id="high-confidence-only" onchange="updatePatternPreview()" />
                <strong>High confidence only (≥0.8)</strong>
              </label>
            </div>
            
            <!-- Result Limit -->
            <div style="margin-bottom: 20px;">
              <label style="display: block; font-weight: 600; margin-bottom: 6px; color: #374151; font-size: 14px;">
                📊 Result Limit
              </label>
              <select id="result-limit" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                <option value="10">10 results</option>
                <option value="25">25 results</option>
                <option value="50" selected>50 results</option>
                <option value="100">100 results</option>
                <option value="500">500 results</option>
              </select>
            </div>
            
            <!-- Execute Button -->
            <button onclick="executePatternQuery()" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);">
              🚀 Execute Query
            </button>
            
            <button onclick="clearQueryBuilder()" style="width: 100%; margin-top: 8px; padding: 8px; background: #6b7280; color: white; border: none; border-radius: 6px; font-size: 14px; cursor: pointer;">
              🔄 Clear
              </button>
            </div>
          
          <!-- Help Section -->
          <div class="card" style="background: #eff6ff; border: 1px solid #bfdbfe;">
            <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #1e40af;">
              💡 How to Use
            </h3>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #1e40af; line-height: 1.6;">
              <li>Select node types and/or relationship type</li>
              <li>Leave fields blank to match <strong>anything</strong></li>
              <li>Use name filters to narrow results</li>
              <li>Any combination of filters works</li>
              <li>Results appear in the right panel</li>
            </ul>
          </div>
        </div>
        
        <!-- Right Panel: Results -->
        <div style="display: flex; flex-direction: column; gap: 16px; overflow-y: auto;">
          
          <!-- Results Header -->
          <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h2 style="margin: 0; font-size: 20px; color: #111827;">
                📋 Query Results
              </h2>
              <div id="result-count" style="font-size: 14px; color: #6b7280; font-weight: 500;">
                No query executed yet
          </div>
        </div>
          </div>
          
          <!-- Results List -->
          <div id="query-results" style="display: flex; flex-direction: column; gap: 12px;">
            <div style="text-align: center; padding: 60px 20px; color: #9ca3af;">
              <div style="font-size: 48px; margin-bottom: 16px;">🔎</div>
              <p style="font-size: 16px; margin: 0;">
                Build and execute a query to see results
              </p>
      </div>
    </div>
    
          <!-- Visualization Button -->
          <div id="visualize-section" style="display: none;">
            <button onclick="visualizeQueryResults()" style="width: 100%; padding: 12px; background: #059669; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer;">
              📊 Visualize Results in Graph
            </button>
          </div>
        </div>
        
      </div>
    </div>
    
    <!-- ==========================================
         MANUAL EDGE CREATION MODAL
         ========================================== -->
    <div id="create-edge-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 2000; align-items: center; justify-content: center;">
      <div style="background: white; border-radius: 12px; padding: 24px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #e5e7eb;">
          <h2 style="margin: 0; font-size: 20px; color: #111827;">Create Manual Relationship</h2>
          <button onclick="closeCreateEdgeModal()" style="background: transparent; border: none; font-size: 24px; cursor: pointer; color: #6b7280; padding: 0;">×</button>
        </div>
        
        <form id="create-edge-form" onsubmit="saveManualEdge(event)">
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 14px;">From (Subject)</label>
            <input type="text" id="manual-from" readonly style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; background: #f9fafb;" />
          </div>
          
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 14px;">Relationship Type</label>
            <input type="text" id="manual-relation" list="manual-predicate-suggestions" required style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;" />
            <datalist id="manual-predicate-suggestions">
              <option value="targets">
              <option value="inhibits">
              <option value="activates">
              <option value="regulates">
              <option value="binds_to">
              <option value="causes">
              <option value="treats">
              <option value="associated_with">
              <option value="located_in">
              <option value="part_of">
            </datalist>
          </div>
          
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 14px;">To (Object)</label>
            <input type="text" id="manual-to" readonly style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; background: #f9fafb;" />
          </div>
          
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 14px;">Evidence / Source Text</label>
            <textarea id="manual-evidence" required style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; min-height: 80px; resize: vertical;" placeholder="Provide the text or citation that supports this relationship..."></textarea>
          </div>
          
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 14px;">Confidence (0-1)</label>
            <input type="number" id="manual-confidence" min="0" max="1" step="0.1" value="0.9" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;" />
          </div>
          
          <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
            <button type="button" onclick="closeCreateEdgeModal()" style="padding: 10px 20px; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; background: #f3f4f6; color: #374151;">Cancel</button>
            <button type="submit" style="padding: 10px 20px; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; background: #8b5cf6; color: white;">Create Relationship</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- ========================================
         JAVASCRIPT LOGIC
         ======================================== -->
    <script>
      // ==========================================
      // GLOBAL STATE & INITIALIZATION
      // ==========================================
      
      // Global state variables
      let currentUser = null;
      let cy = null;
      let acState = { open: false, index: -1, items: [] };
      let selectedNodes = new Set(); // Track multi-selected nodes for review
      let manualEdgeNodes = { node1: null, node2: null }; // Track nodes for manual edge creation
      let currentEdgeData = null; // Store current edge data for modal
      let indexVisible = false; // Track index panel visibility
      
      // Viewport-based loading state
      let currentDocIds = [];
      let isLoading = false;
      let loadedNodes = new Set();
      let viewportUpdateTimeout = null;
      let lastViewport = null;
      let viewportMode = false; // Whether to use viewport-based loading
      
      // ==========================================
      // NEW VIEWER UI FUNCTIONS
      // ==========================================
      
      // Toggle Index Panel
      function toggleIndex() {
        const panel = document.getElementById('index-panel');
        const btn = document.getElementById('index-toggle-btn');
        indexVisible = !indexVisible;
        
        if (indexVisible) {
          panel.classList.remove('hidden');
          btn.classList.add('index-visible');
        } else {
          panel.classList.add('hidden');
          btn.classList.remove('index-visible');
        }
      }
      
      // Store index data globally for filtering
      let indexData = { nodes: [], edges: [], documents: [] };
      let activeDocuments = new Set(); // Track which documents are toggled on
      
      // Populate Index with current graph data
      async function populateIndex() {
        if (!cy) return;
        
        const nodes = cy.nodes();
        const edges = cy.edges();
        
        // Store data for filtering
        indexData.nodes = nodes.map(n => ({
          id: n.id(),
          label: n.data().label,
          type: n.data().type || 'Entity',
          sources: n.data().sources || []
        }));
        
        indexData.edges = edges.map(e => ({
          source: cy.getElementById(e.data().source).data().label,
          target: cy.getElementById(e.data().target).data().label,
          relation: e.data().relation || 'relates to',
          sources: e.data().sources || []
        }));
        
        // Fetch documents
        try {
          const res = await fetch('/query/documents');
          const data = await res.json();
          indexData.documents = data.documents || [];
          
          // Initialize all documents as active (toggled on) by default
          if (activeDocuments.size === 0) {
            indexData.documents.forEach(doc => {
              activeDocuments.add(doc.id);
            });
          }
        } catch (e) {
          console.error('Failed to load documents for index:', e);
          indexData.documents = [];
        }
        
        // Update counts
        document.getElementById('index-count').textContent = 
          `${nodes.length} concepts, ${edges.length} relationships, ${indexData.documents.length} documents`;
        document.getElementById('concepts-count').textContent = nodes.length;
        document.getElementById('relationships-count').textContent = edges.length;
        document.getElementById('documents-count').textContent = indexData.documents.length;
        
        // Populate type filter dropdown
        const typeFilter = document.getElementById('index-type-filter');
        const types = new Set();
        nodes.forEach(n => types.add(n.data().type || 'Entity'));
        edges.forEach(e => types.add(e.data().relation || 'relates to'));
        
        typeFilter.innerHTML = '<option value="">All Types</option>' + 
          Array.from(types).sort().map(t => `<option value="${t}">${t}</option>`).join('');
        
        // Render items
        renderIndexItems();
      }
      
      // Render index items (called by populateIndex and filterIndex)
      function renderIndexItems() {
        const viewFilter = document.getElementById('index-view-filter').value;
        const typeFilter = document.getElementById('index-type-filter').value;
        
        // Show/hide sections based on view filter
        document.getElementById('documents-section').style.display = 
          (viewFilter === 'all' || viewFilter === 'documents') ? 'block' : 'none';
        document.getElementById('concepts-section').style.display = 
          (viewFilter === 'all' || viewFilter === 'concepts') ? 'block' : 'none';
        document.getElementById('relationships-section').style.display = 
          (viewFilter === 'all' || viewFilter === 'relationships') ? 'block' : 'none';
        
        // Render documents
        const documentsList = document.getElementById('documents-list');
        if (documentsList) {
          documentsList.innerHTML = '';
          
          (indexData.documents || []).forEach(doc => {
          const div = document.createElement('div');
          div.className = 'doc-item';
          if (activeDocuments.has(doc.id)) {
            div.classList.add('active');
          }
          
          // Create toggle checkbox
          const toggleDiv = document.createElement('div');
          toggleDiv.className = 'doc-toggle';
          toggleDiv.textContent = activeDocuments.has(doc.id) ? '✓' : '';
          toggleDiv.onclick = (e) => {
            e.stopPropagation();
            toggleDocument(doc.id);
          };
          
          // Create name span
          const nameDiv = document.createElement('div');
          nameDiv.className = 'doc-name';
          nameDiv.textContent = doc.title || doc.id;
          nameDiv.onclick = (e) => {
            e.stopPropagation();
            showDocumentModal(doc.id);
          };
          
          div.appendChild(toggleDiv);
          div.appendChild(nameDiv);
          
          // Hover to highlight
          div.onmouseenter = () => highlightDocumentElements(doc.id, true);
          div.onmouseleave = () => highlightDocumentElements(doc.id, false);
          
          documentsList.appendChild(div);
          });
        }
        
        // Filter and render concepts
        const conceptsList = document.getElementById('concepts-list');
        conceptsList.innerHTML = '';
        
        const filteredNodes = indexData.nodes.filter(n => 
          !typeFilter || n.type === typeFilter
        );
        
        filteredNodes.forEach(node => {
          const li = document.createElement('li');
          li.className = 'index-item';
          li.innerHTML = `${node.label}<span class="index-item-type">${node.type}</span>`;
          li.onclick = () => highlightAndZoomToNode(node.id);
          conceptsList.appendChild(li);
        });
        
        document.getElementById('concepts-count').textContent = filteredNodes.length;
        
        // Filter and render relationships
        const relsList = document.getElementById('relationships-list');
        relsList.innerHTML = '';
        
        const filteredEdges = indexData.edges.filter(e => 
          !typeFilter || e.relation === typeFilter
        );
        
        filteredEdges.forEach(edge => {
          const div = document.createElement('div');
          div.className = 'index-relationship';
          div.innerHTML = `${edge.source}<span class="rel-arrow">→</span>${edge.target}`;
          div.title = edge.relation;
          relsList.appendChild(div);
        });
        
        document.getElementById('relationships-count').textContent = filteredEdges.length;
      }
      
      // Filter index based on dropdowns
      function filterIndex() {
        renderIndexItems();
      }
      
      // Document highlighting functions
      function highlightDocumentElements(docId, highlight) {
        if (!cy) return;
        
        // Find all nodes and edges from this document
        cy.elements().forEach(el => {
          const sources = el.data().sources || [];
          const hasDoc = sources.some(s => (typeof s === 'object' ? s.id : s) === docId);
          
          if (hasDoc) {
            if (highlight) {
              el.addClass('highlighted');
            } else {
              el.removeClass('highlighted');
            }
          }
        });
      }
      
      // Toggle document visibility
      function toggleDocument(docId) {
        // Toggle the document on/off
        if (activeDocuments.has(docId)) {
          activeDocuments.delete(docId);
          console.log(`Document ${docId} toggled OFF`);
        } else {
          activeDocuments.add(docId);
          console.log(`Document ${docId} toggled ON`);
        }
        
        // Apply filter to show/hide elements
        applyDocumentFilter();
        
        // Re-render index to update toggle icons
        renderIndexItems();
      }
      
      // Apply document filter to show/hide graph elements
      function applyDocumentFilter() {
        if (!cy) return;
        
        console.log('=== Applying Document Filter ===');
        console.log('Active documents:', Array.from(activeDocuments));
        console.log('Total documents:', indexData.documents.length);
        
        // If all documents are active, show everything
        if (activeDocuments.size === indexData.documents.length) {
          cy.elements().style('display', 'element');
          console.log('All documents active - showing all elements');
          return;
        }
        
        let hiddenNodes = 0;
        let visibleNodes = 0;
        
        // Filter nodes based on active documents
        cy.nodes().forEach(node => {
          const sources = node.data().sources || [];
          const hasActiveDoc = sources.some(s => {
            const sourceId = typeof s === 'object' ? s.id : s;
            return activeDocuments.has(sourceId);
          });
          
          if (hasActiveDoc) {
            node.style('display', 'element');
            visibleNodes++;
          } else {
            node.style('display', 'none');
            hiddenNodes++;
          }
        });
        
        console.log(`Nodes: ${visibleNodes} visible, ${hiddenNodes} hidden`);
        
        let hiddenEdges = 0;
        let visibleEdges = 0;
        
        // Filter edges based on active documents
        cy.edges().forEach(edge => {
          const sources = edge.data().sources || [];
          const hasActiveDoc = sources.some(s => {
            const sourceId = typeof s === 'object' ? s.id : s;
            return activeDocuments.has(sourceId);
          });
          
          // Also hide edge if either endpoint is hidden
          const sourceNode = cy.getElementById(edge.data().source);
          const targetNode = cy.getElementById(edge.data().target);
          const endpointsVisible = sourceNode.style('display') === 'element' && targetNode.style('display') === 'element';
          
          if (hasActiveDoc && endpointsVisible) {
            edge.style('display', 'element');
            visibleEdges++;
          } else {
            edge.style('display', 'none');
            hiddenEdges++;
          }
        });
        
        console.log(`Edges: ${visibleEdges} visible, ${hiddenEdges} hidden`);
        console.log('=== Filter Complete ===');
      }
      
      // Show document details modal
      async function showDocumentModal(docId) {
        const modal = document.getElementById('document-modal-overlay');
        const content = document.getElementById('document-modal-content');
        
        try {
          // Fetch document data with its nodes and relationships
          const res = await fetch(`/query/graph_by_docs?doc_ids=${docId}`);
          if (!res.ok) throw new Error('Failed to fetch document data');
          
          const data = await res.json();
          
          // Find document metadata
          const doc = indexData.documents.find(d => d.id === docId);
          
          let html = `
            <div class="modal-section">
              <div class="modal-section-title">Document Information</div>
              <div class="modal-section-content">
                <strong>Title:</strong> ${doc?.title || 'Untitled'}<br>
                <strong>ID:</strong> ${doc?.id || docId}<br>
                ${doc?.created_by ? `<strong>Created by:</strong> ${doc.created_by}<br>` : ''}
                ${doc?.created_at ? `<strong>Created:</strong> ${new Date(doc.created_at).toLocaleString()}<br>` : ''}
              </div>
            </div>
            
            <div class="modal-section">
              <div class="modal-section-title">Extracted Knowledge</div>
              <div class="modal-section-content">
                <strong>Concepts:</strong> ${data.nodes?.length || 0}<br>
                <strong>Relationships:</strong> ${data.relationships?.length || 0}
              </div>
            </div>
          `;
          
          // List concepts
          if (data.nodes && data.nodes.length > 0) {
            html += `
              <div class="modal-section">
                <div class="modal-section-title">Concepts Extracted</div>
                <div class="modal-section-content">
                  ${data.nodes.slice(0, 20).map(n => `<div style="padding: 4px 0;">🔵 ${n.label || n.id}</div>`).join('')}
                  ${data.nodes.length > 20 ? `<div style="margin-top: 8px; color: #6b7280;">... and ${data.nodes.length - 20} more</div>` : ''}
                </div>
              </div>
            `;
          }
          
          // List relationships
          if (data.relationships && data.relationships.length > 0) {
            html += `
              <div class="modal-section">
                <div class="modal-section-title">Relationships Extracted</div>
                <div class="modal-section-content">
                  ${data.relationships.slice(0, 15).map(r => {
                    const source = data.nodes.find(n => n.id === r.source);
                    const target = data.nodes.find(n => n.id === r.target);
                    return `<div style="padding: 4px 0; font-size: 13px;">
                      ${source?.label || r.source} <span style="color: #8b5cf6; font-weight: 600;">→ ${r.relation}</span> → ${target?.label || r.target}
                    </div>`;
                  }).join('')}
                  ${data.relationships.length > 15 ? `<div style="margin-top: 8px; color: #6b7280;">... and ${data.relationships.length - 15} more</div>` : ''}
                </div>
              </div>
            `;
          }
          
          content.innerHTML = html;
          modal.classList.add('visible');
        } catch (e) {
          console.error('Error loading document details:', e);
          content.innerHTML = `<div class="modal-section"><div class="modal-section-content" style="color: #dc2626;">Failed to load document details</div></div>`;
          modal.classList.add('visible');
        }
      }
      
      function closeDocumentModal() {
        document.getElementById('document-modal-overlay').classList.remove('visible');
      }
      
      // Highlight and zoom to a node
      function clearAllHighlights() {
        if (!cy) return;
        
        // Clear highlights in index
        document.querySelectorAll('.index-item').forEach(item => {
          item.classList.remove('highlighted');
        });
        
        // Clear highlights in graph
        cy.elements().removeClass('highlighted neighbor');
        
        console.log('All highlights cleared');
      }
      
      function highlightAndZoomToNode(nodeId) {
        if (!cy) return;
        
        const node = cy.getElementById(nodeId);
        if (!node || node.length === 0) return;
        
        // Clear previous highlights
        clearAllHighlights();
        
        // Highlight in index
        const items = document.querySelectorAll('.index-item');
        items.forEach(item => {
          if (item.textContent.includes(node.data().label)) {
            item.classList.add('highlighted');
          }
        });
        
        // Highlight and zoom in graph
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        cy.animate({
          center: { eles: node },
          zoom: 2,
          duration: 500
        });
      }
      
      // Show edge tooltip on hover
      function showEdgeTooltip(edge, event) {
        const tooltip = document.getElementById('edge-tooltip');
        const data = edge.data();
        
        // DEBUG: Log edge data to check original_text
        console.log('🔍 Edge data analysis:', {
          relation: data.relation,
          original_text: data.original_text,
          has_original_text: !!data.original_text,
          original_text_type: typeof data.original_text,
          original_text_length: data.original_text ? data.original_text.length : 0,
          all_keys: Object.keys(data),
          full_data: data
        });
        
        // Populate tooltip
        document.getElementById('tooltip-source').textContent = cy.getElementById(data.source).data().label;
        document.getElementById('tooltip-relation').textContent = data.relation || 'relates to';
        document.getElementById('tooltip-target').textContent = cy.getElementById(data.target).data().label;
        document.getElementById('tooltip-confidence').textContent = 
          `Confidence: ${data.confidence ? (data.confidence * 100).toFixed(0) + '%' : 'N/A'}`;
        document.getElementById('tooltip-significance').textContent = 
          `Significance: ${data.significance ? data.significance + '/5' : 'N/A'}`;
        
        // Tooltip positioning - always starts at cursor
        const tooltipWidth = 300; // Max width from CSS
        const tooltipHeight = 180; // Estimated height
        
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        const mouseX = event.originalEvent.clientX;
        const mouseY = event.originalEvent.clientY;
        
        // Default: bottom-right of cursor (touching cursor)
        let left = mouseX;
        let top = mouseY;
        
        // If tooltip would go off right edge, position to left of cursor
        if (left + tooltipWidth > windowWidth - 10) {
          left = mouseX - tooltipWidth;
        }
        
        // If tooltip would go off bottom edge, position above cursor
        if (top + tooltipHeight > windowHeight - 10) {
          top = mouseY - tooltipHeight;
        }
        
        // Ensure tooltip doesn't go off left or top edges
        left = Math.max(10, left);
        top = Math.max(10, top);
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
        tooltip.classList.add('visible');
        
        // Store edge data for modal
        currentEdgeData = data;
        isOverEdge = true;
        
        // Clear any pending hide timeout
        if (hideTooltipTimeout) {
          clearTimeout(hideTooltipTimeout);
          hideTooltipTimeout = null;
        }
        
        // Add click handler to Read More button
        document.getElementById('tooltip-read-more').onclick = () => {
          hideEdgeTooltip();
          showEdgeModal(data);
        };
      }
      
      // Track if mouse is over tooltip or edge
      let isOverTooltip = false;
      let isOverEdge = false;
      let hideTooltipTimeout = null;
      
      // Hide edge tooltip
      function hideEdgeTooltip() {
        const tooltip = document.getElementById('edge-tooltip');
        tooltip.classList.remove('visible');
        isOverEdge = false;
        isOverTooltip = false;
      }
      
      // Schedule tooltip hide with delay
      function scheduleHideTooltip() {
        if (hideTooltipTimeout) {
          clearTimeout(hideTooltipTimeout);
        }
        hideTooltipTimeout = setTimeout(() => {
          if (!isOverTooltip && !isOverEdge) {
            hideEdgeTooltip();
          }
        }, 200); // 200ms delay
      }
      
      // Show edge details modal
      function showEdgeModal(data) {
        const modal = document.getElementById('edge-modal-overlay');
        const content = document.getElementById('edge-modal-content');
        
        // DEBUG: Log modal data
        console.log('Modal data:', {
          original_text: data.original_text,
          original_text_type: typeof data.original_text,
          original_text_length: data.original_text ? data.original_text.length : 0,
          has_original_text: !!data.original_text,
          all_fields: data
        });
        
        const sourceLabel = cy.getElementById(data.source).data().label;
        const targetLabel = cy.getElementById(data.target).data().label;
        
        // Build modal content
        let html = `
          <div class="modal-section">
            <div class="modal-section-title">Relationship</div>
            <div class="modal-section-content">
              <strong>${sourceLabel}</strong>
              <span class="modal-relation">${data.relation || 'relates to'}</span>
              <strong>${targetLabel}</strong>
            </div>
          </div>
          
          <div class="modal-section">
            <div class="modal-section-title">Status & Metadata</div>
            <div class="modal-section-content">
              <span class="modal-badge ${data.status === 'verified' ? 'badge-verified' : 'badge-unverified'}">
                ${data.status === 'verified' ? '✓ Verified' : '⏳ Unverified'}
              </span>
              ${data.polarity === 'negative' ? '<span class="modal-badge badge-negative">⚠ Negative</span>' : ''}
              <div style="margin-top: 12px;">
                <strong>Confidence:</strong> ${data.confidence ? (data.confidence * 100).toFixed(0) + '%' : 'N/A'}<br>
                <strong>Significance:</strong> ${data.significance ? data.significance + '/5' : 'N/A'}
                ${data.page_number ? `<br><strong>Page:</strong> ${data.page_number}` : ''}
              </div>
            </div>
          </div>
        `;
        
        // Add original text if available (check for non-null, non-empty string)
        if (data.original_text && data.original_text.trim && data.original_text.trim().length > 0) {
          html += `
            <div class="modal-section">
              <div class="modal-section-title">Original Text</div>
              <div class="modal-section-content">
                <div class="original-text-box">
                  "${data.original_text}"
                </div>
              </div>
            </div>
          `;
          console.log('✅ Original text section added to modal');
        } else {
          console.log('❌ No original text available:', {
            value: data.original_text,
            type: typeof data.original_text,
            is_null: data.original_text === null,
            is_undefined: data.original_text === undefined
          });
        }
        
        // Add sources
        if (data.sources && data.sources.length > 0) {
          html += `
            <div class="modal-section">
              <div class="modal-section-title">Sources</div>
              <div class="modal-section-content">
          `;
          data.sources.forEach(source => {
            html += `<div style="margin-bottom: 8px;">
              📄 <strong>${source.title || source.id}</strong>
              ${source.created_by_first_name ? `<br>&nbsp;&nbsp;&nbsp;by ${source.created_by_first_name} ${source.created_by_last_name}` : ''}
            </div>`;
          });
          html += `</div></div>`;
        }
        
        content.innerHTML = html;
        modal.classList.add('visible');
      }
      
      // Close edge modal
      function closeEdgeModal() {
        const modal = document.getElementById('edge-modal-overlay');
        modal.classList.remove('visible');
      }
      
      // Node tooltip and modal functions
      let isOverNode = false;
      let hideNodeTooltipTimeout = null;
      let isOverNodeTooltip = false;
      
      function showNodeTooltip(node, event) {
        const tooltip = document.getElementById('node-tooltip');
        const data = node.data();
        
        // Populate tooltip
        document.getElementById('node-tooltip-label').textContent = data.label || data.id;
        document.getElementById('node-tooltip-type').textContent = `Type: ${data.type || 'Entity'}`;
        document.getElementById('node-tooltip-significance').textContent = 
          `Significance: ${data.significance ? data.significance + '/5' : 'N/A'}`;
        
        // Tooltip positioning
        const tooltipWidth = 300;
        const tooltipHeight = 150;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        const mouseX = event.originalEvent.clientX;
        const mouseY = event.originalEvent.clientY;
        
        let left = mouseX;
        let top = mouseY;
        
        if (left + tooltipWidth > windowWidth - 10) {
          left = mouseX - tooltipWidth;
        }
        if (top + tooltipHeight > windowHeight - 10) {
          top = mouseY - tooltipHeight;
        }
        
        left = Math.max(10, left);
        top = Math.max(10, top);
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
        tooltip.classList.add('visible');
        
        isOverNode = true;
        
        if (hideNodeTooltipTimeout) {
          clearTimeout(hideNodeTooltipTimeout);
          hideNodeTooltipTimeout = null;
        }
        
        // Add click handler to Read More button
        document.getElementById('node-tooltip-read-more').onclick = () => {
          hideNodeTooltip();
          showNodeModal(data);
        };
      }
      
      function hideNodeTooltip() {
        const tooltip = document.getElementById('node-tooltip');
        tooltip.classList.remove('visible');
        isOverNode = false;
        isOverNodeTooltip = false;
      }
      
      function scheduleHideNodeTooltip() {
        if (hideNodeTooltipTimeout) {
          clearTimeout(hideNodeTooltipTimeout);
        }
        hideNodeTooltipTimeout = setTimeout(() => {
          if (!isOverNodeTooltip && !isOverNode) {
            hideNodeTooltip();
          }
        }, 200);
      }
      
      function showNodeModal(data) {
        const modal = document.getElementById('node-modal-overlay');
        const content = document.getElementById('node-modal-content');
        
        const sources = data.sources || [];
        let sourcesHtml = '';
        if (sources.length === 0 || !sources || (sources.length === 1 && !sources[0].id)) {
          sourcesHtml = '<div style="color: #ef4444;">No sources recorded</div>';
        } else {
          sourcesHtml = `
            <strong>${sources.length} document(s)</strong>
            <div style="margin-top: 8px;">
              ${sources.map(s => {
                const title = (typeof s === 'object' && s.title) ? s.title : s;
                const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
                const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
                const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
                return `<div style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}${userName}</div>`;
              }).join('')}
            </div>
          `;
        }
        
        let significanceHtml = '';
        if (data.significance) {
          const stars = '⭐'.repeat(data.significance);
          const emptyStars = '☆'.repeat(5 - data.significance);
          significanceHtml = `
            <div class="modal-section">
              <div class="modal-section-title">Significance</div>
              <div class="modal-section-content" style="font-size: 18px; color: #f59e0b;">
                ${stars}${emptyStars}
                <span style="font-size: 12px; color: #6b7280; margin-left: 8px;">(${data.significance}/5)</span>
              </div>
            </div>
          `;
        }
        
        let html = `
          <div class="modal-section">
            <div class="modal-section-title">Node Label</div>
            <div class="modal-section-content" style="font-weight: 600; font-size: 18px;">
              ${data.label || data.id}
            </div>
          </div>
          
          <div class="modal-section">
            <div class="modal-section-title">Type</div>
            <div class="modal-section-content">
              ${data.type || 'Entity'}
            </div>
          </div>
          
          ${significanceHtml}
          
          <div class="modal-section">
            <div class="modal-section-title">ID</div>
            <div class="modal-section-content" style="font-family: monospace; font-size: 12px;">
              ${data.id}
            </div>
          </div>
          
          <div class="modal-section">
            <div class="modal-section-title">Sources</div>
            <div class="modal-section-content">
              ${sourcesHtml}
            </div>
          </div>
        `;
        
        content.innerHTML = html;
        modal.classList.add('visible');
      }
      
      function closeNodeModal() {
        const modal = document.getElementById('node-modal-overlay');
        modal.classList.remove('visible');
      }
      
      // Close modal when clicking overlay
      document.addEventListener('DOMContentLoaded', () => {
        const edgeOverlay = document.getElementById('edge-modal-overlay');
        edgeOverlay.addEventListener('click', (e) => {
          if (e.target === edgeOverlay) {
            closeEdgeModal();
          }
        });
        
        const nodeOverlay = document.getElementById('node-modal-overlay');
        nodeOverlay.addEventListener('click', (e) => {
          if (e.target === nodeOverlay) {
            closeNodeModal();
          }
        });
        
        const docOverlay = document.getElementById('document-modal-overlay');
        docOverlay.addEventListener('click', (e) => {
          if (e.target === docOverlay) {
            closeDocumentModal();
          }
        });
        
        const legendOverlay = document.getElementById('legend-modal-overlay');
        legendOverlay.addEventListener('click', (e) => {
          if (e.target === legendOverlay) {
            closeLegendModal();
          }
        });
        
        // Node tooltip hover handling
        const nodeTooltip = document.getElementById('node-tooltip');
        nodeTooltip.addEventListener('mouseenter', () => {
          isOverNodeTooltip = true;
          if (hideNodeTooltipTimeout) {
            clearTimeout(hideNodeTooltipTimeout);
          }
        });
        nodeTooltip.addEventListener('mouseleave', () => {
          isOverNodeTooltip = false;
          scheduleHideNodeTooltip();
        });
        
      });
      
      // Global ESC key handler to clear node selection (outside DOMContentLoaded)
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          console.log('ESC key pressed');
          
          let clearedSomething = false;
          
          // Clear multi-selected nodes (Shift+Click)
          if (selectedNodes && selectedNodes.size > 0) {
            clearSelection();
            console.log('Selection cleared via ESC key');
            clearedSomething = true;
          }
          
          // Clear highlighted nodes (from index click)
          clearAllHighlights();
          
          if (clearedSomething) {
            console.log('Highlights and selection cleared');
          }
        }
      });
      
      // Initialize
      async function init() {
        await checkAuth();
        await loadDocuments();
        // Don't initialize cytoscape or load data until viewing tab is opened
        // This prevents the horizontal line issue
      }
      
      async function checkAuth() {
        try {
          const res = await fetch('/api/auth/me', {
            credentials: 'include'  // Include cookies
          });
          if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            document.getElementById('username').textContent = currentUser.username || currentUser.user_id;
          } else {
            // Not authenticated, redirect to login
            window.location.href = '/login';
          }
        } catch (e) {
          console.error('Auth check failed:', e);
          window.location.href = '/login';
        }
      }
      
      let graphInitialized = false;
      
      // ==========================================
      // FAB HANDLER FUNCTIONS
      // ==========================================
      
      function openManualRelationshipFab() {
        // Check if exactly 2 nodes are selected
        if (selectedNodes.size !== 2) {
          alert('Please select exactly 2 nodes:\\n\\n1. Shift+Click on the first node\\n2. Shift+Click on the second node\\n3. Click this button to create a relationship');
          return;
        }
        
        // Convert selected nodes to array and populate manualEdgeNodes
        const selectedArray = Array.from(selectedNodes);
        const node1 = cy.getElementById(selectedArray[0]);
        const node2 = cy.getElementById(selectedArray[1]);
        
        manualEdgeNodes.node1 = {
          id: node1.id(),
          label: node1.data().label,
          node: node1
        };
        manualEdgeNodes.node2 = {
          id: node2.id(),
          label: node2.data().label,
          node: node2
        };
        
        openCreateEdgeModal();
      }
      
      function openShortestPathFab() {
        const source = prompt('Enter source concept name:');
        if (!source) return;
        const target = prompt('Enter target concept name:');
        if (!target) return;
        findShortestPathManual(source, target);
      }
      
      async function findShortestPathManual(source, target) {
        const verifiedOnly = false; // Can be made configurable
        
        try {
          const response = await fetch(`/api/pathway/shortest-path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}&verified_only=${verifiedOnly}`);
          
          if (!response.ok) {
            throw new Error('Pathway search failed');
          }
          
          const data = await response.json();
          
          if (!data.path_found) {
            alert(data.message || 'No path found between these concepts');
            return;
          }
          
          // Visualize the path
          renderGraph({
            nodes: data.nodes,
            relationships: data.relationships
          });
          
          // Highlight the path
          setTimeout(() => {
            if (cy) {
              cy.nodes().removeClass('highlighted neighbor');
              cy.nodes().addClass('highlighted');
              cy.edges().style('line-color', '#8b5cf6').style('target-arrow-color', '#8b5cf6').style('width', 4);
            }
          }, 500);
          
          alert(`Found path with ${data.path_length} hop(s) between ${data.source} and ${data.target}!`);
        } catch (e) {
          alert('Error finding path: ' + e.message);
        }
      }
      
      function openExportFab() {
        const format = prompt('Enter format (json, csv, graphml):', 'json');
        if (!format) return;
        exportGraphWithFormat(format);
      }
      
      async function exportGraphWithFormat(format) {
        if (!cy) {
          alert('No graph loaded to export');
          return;
        }
        
        const nodes = [];
        const edges = [];
        
        cy.nodes().forEach(node => {
          nodes.push({
            id: node.id(),
            label: node.data('label'),
            type: node.data('type'),
            significance: node.data('significance'),
            sources: node.data('sources')
          });
        });
        
        cy.edges().forEach(edge => {
          edges.push({
            id: edge.id(),
            source: edge.data('source'),
            target: edge.data('target'),
            relation: edge.data('relation'),
            status: edge.data('status'),
            polarity: edge.data('polarity'),
            confidence: edge.data('confidence'),
            significance: edge.data('significance'),
            sources: edge.data('sources')
          });
        });
        
        try {
          const response = await fetch('/api/export/graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              format: format,
              nodes: nodes,
              edges: edges
            })
          });
          
          if (!response.ok) {
            throw new Error('Export failed');
          }
          
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `knowledge_graph_${new Date().toISOString().split('T')[0]}.${format}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          alert(`Graph exported successfully as ${format.toUpperCase()}!`);
        } catch (e) {
          alert('Export failed: ' + e.message);
        }
      }
      
      function openReviewFab() {
        window.open('/review-ui', '_blank');
      }
      
      // ==========================================
      // TAB SWITCHING & NAVIGATION
      // ==========================================
      
      function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        event.target.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
        
        // Show/hide index and legend buttons based on tab
        const indexToggleBtn = document.getElementById('index-toggle-btn');
        const legendToggleBtn = document.getElementById('legend-toggle-btn');
        
        if (tabName === 'viewing') {
          indexToggleBtn.style.display = 'flex';
          legendToggleBtn.style.display = 'flex';
          
          if (!graphInitialized) {
            // First time opening viewing tab - initialize everything
            console.log('Initializing graph for first time...');
            // Use requestAnimationFrame to ensure DOM is ready
            requestAnimationFrame(() => {
              initCytoscape();
              setTimeout(async () => {
                if (cy) {
                  cy.resize();
                }
                await loadAllData();
                graphInitialized = true;
              }, 150);
            });
          } else if (cy) {
            // Already initialized, just resize and fit
            requestAnimationFrame(() => {
              cy.resize();
              cy.fit(undefined, 20);
            });
            setTimeout(() => {
              cy.resize();
              updateFabVisibility(); // Update FABs when switching back to viewing tab
            }, 100);
          }
        } else {
          indexToggleBtn.style.display = 'none';
          legendToggleBtn.style.display = 'none';
          updateFabVisibility(); // Hide FABs when leaving viewing tab
          
          if (tabName === 'query-builder') {
            // Load schema when opening query builder for the first time
            if (!window.queryBuilderInitialized) {
              loadGraphSchema();
              window.queryBuilderInitialized = true;
            }
          }
        }
      }

      // ==========================================
      // AUTOCOMPLETE SEARCH FUNCTIONALITY
      // ==========================================
      const acBox = () => document.getElementById('search-autocomplete');
      const acInput = () => document.getElementById('search-input');

      function debounce(fn, ms) {
        let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
      }

      function renderAutocomplete() {
        const box = acBox();
        if (!acState.open || !acState.items.length) { box.style.display = 'none'; return; }
        const html = acState.items.map((it, i) => `
          <div data-index="${i}" style="padding: 8px 10px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; ${i===acState.index?'background:#eef2ff;':''}">
            <div>
              <div style="font-weight:600; color:#111827">${it.label}</div>
              <div style="font-size: 12px; color:#6b7280">${it.type || 'Entity'}</div>
            </div>
            ${typeof it.score === 'number' ? `<span style="font-size: 12px; color:#9ca3af;">${it.score.toFixed(2)}</span>` : ''}
          </div>
        `).join('');
        box.innerHTML = html;
        box.style.display = 'block';

        // bind clicks
        Array.from(box.children).forEach(el => {
          el.addEventListener('mousedown', (e) => {
            const idx = parseInt(el.getAttribute('data-index'));
            selectAutocomplete(idx);
            e.preventDefault();
          });
        });
      }

        // Wire input events (only if search input exists)
      document.addEventListener('DOMContentLoaded', () => {
        const input = acInput();
        if (input) {
          input.addEventListener('input', fetchAutocomplete);
          input.addEventListener('focus', fetchAutocomplete);
          input.addEventListener('blur', () => setTimeout(closeAutocomplete, 150));
          input.addEventListener('keydown', (e) => {
            if (!acState.open) return;
            if (e.key === 'ArrowDown') { e.preventDefault(); moveAutocomplete(1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); moveAutocomplete(-1); }
            else if (e.key === 'Enter') { e.preventDefault(); selectAutocomplete(acState.index); }
            else if (e.key === 'Escape') { closeAutocomplete(); }
          });
        }
      });

      function openAutocomplete(items) {
        acState.items = items;
        acState.index = items.length ? 0 : -1;
        acState.open = items.length > 0;
        renderAutocomplete();
      }

      function closeAutocomplete() {
        acState.open = false;
        acState.index = -1;
        renderAutocomplete();
      }

      function moveAutocomplete(delta) {
        if (!acState.open || !acState.items.length) return;
        acState.index = (acState.index + delta + acState.items.length) % acState.items.length;
        renderAutocomplete();
      }

      function selectAutocomplete(index) {
        if (index < 0 || index >= acState.items.length) return;
        const item = acState.items[index];
        acInput().value = item.label;
        closeAutocomplete();
        searchConcept();
      }

      const fetchAutocomplete = debounce(async () => {
        const q = acInput().value.trim();
        // If empty, show everything by reloading full graph
        if (!q) {
          closeAutocomplete();
          await loadAllData();
          return;
        }
        try {
          const res = await fetch(`/query/autocomplete?q=${encodeURIComponent(q)}&limit=10`);
          if (!res.ok) { closeAutocomplete(); return; }
          const data = await res.json();
          openAutocomplete(data.results || []);
          // Re-filter the graph in real-time based on query text
          await filterGraphBySearch(q);
        } catch (e) { closeAutocomplete(); }
      }, 200);

      
      async function logout() {
        try {
          await fetch('/api/auth/logout', { 
            method: 'POST',
            credentials: 'include'
          });
        } catch (e) {
          console.error('Logout failed:', e);
        }
        window.location.href = '/login';
      }
      
      // ==========================================
      // DOCUMENT INGESTION FUNCTIONS
      // ==========================================
      
      function toggleGraphContext() {
        const checkbox = document.getElementById('use-graph-context');
        const statusDiv = document.getElementById('graph-context-status');
        const countSpan = document.getElementById('graph-context-count');
        
        console.log('toggleGraphContext called, checked:', checkbox.checked);
        
        if (checkbox.checked) {
          if (selectedNodes.size === 0) {
            alert('Please select nodes in the Viewer first.');
            checkbox.checked = false;
            return;
          }
          countSpan.textContent = selectedNodes.size;
          statusDiv.style.display = 'block';
          console.log('Graph context enabled with', selectedNodes.size, 'nodes');
        } else {
          statusDiv.style.display = 'none';
          console.log('Graph context disabled');
        }
      }
      
      async function getGraphContextText() {
        if (selectedNodes.size === 0) {
          console.log('No nodes selected for context');
          return null;
        }
        
        try {
          const nodeIds = Array.from(selectedNodes);
          console.log('Fetching subgraph for nodes:', nodeIds);
          
          const response = await fetch('/query/subgraph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_ids: nodeIds })
          });
          
          if (!response.ok) {
            console.error('Failed to fetch subgraph');
            return null;
          }
          
          const data = await response.json();
          console.log('Subgraph data received:', data);
          
          // Build context text using ONLY string concatenation, no template literals with variables
          let contextText = '=== EXISTING KNOWLEDGE GRAPH CONTEXT ===\\n\\n';
          contextText += 'This subgraph contains ' + data.nodes.length + ' entities and ' + data.relationships.length + ' relationships:\\n\\n';
          contextText += 'ENTITIES:\\n';
          
          data.nodes.forEach(node => {
            // Sanitize label to prevent any special characters
            const label = String(node.label || 'Unknown').replace(/[^\\w\\s-]/g, '');
            const type = String(node.type || 'Concept').replace(/[^\\w\\s-]/g, '');
            contextText += '- ' + label + ' (' + type + ')\\n';
          });
          
          contextText += '\\nRELATIONSHIPS:\\n';
          
          data.relationships.forEach(rel => {
            const sourceNode = data.nodes.find(n => n.id === rel.source);
            const targetNode = data.nodes.find(n => n.id === rel.target);
            const sourceName = String(sourceNode ? sourceNode.label : rel.source).replace(/[^\\w\\s-]/g, '');
            const targetName = String(targetNode ? targetNode.label : rel.target).replace(/[^\\w\\s-]/g, '');
            const relation = String(rel.relation || 'RELATED_TO').replace(/[^\\w\\s-]/g, '');
            
            contextText += '- ' + sourceName + ' -> [' + relation + '] -> ' + targetName + '\\n';
          });
          
          contextText += '\\n=== END CONTEXT ===\\n\\n';
          
          console.log('Context text built, length:', contextText.length);
          return contextText;
          
        } catch (error) {
          console.error('Error getting graph context:', error);
          return null;
        }
      }
      
      function displayFileName() {
        const fileInput = document.getElementById('pdf-file');
        const fileNameDisplay = document.getElementById('file-name');
        
        if (fileInput.files && fileInput.files.length > 0) {
          if (fileInput.files.length === 1) {
            const fileName = fileInput.files[0].name;
            const fileSize = (fileInput.files[0].size / 1024 / 1024).toFixed(2); // MB
            fileNameDisplay.innerHTML = `<span style="color: #059669; font-weight: 600;">✓</span> ${fileName} <span style="color: #6b7280; font-size: 12px;">(${fileSize} MB)</span>`;
          } else {
            const totalSize = Array.from(fileInput.files).reduce((sum, file) => sum + file.size, 0);
            const totalSizeMB = (totalSize / 1024 / 1024).toFixed(2);
            fileNameDisplay.innerHTML = `<span style="color: #059669; font-weight: 600;">✓</span> ${fileInput.files.length} files selected <span style="color: #6b7280; font-size: 12px;">(${totalSizeMB} MB total)</span>`;
          }
        } else {
          fileNameDisplay.textContent = 'No files selected';
        }
      }
      
      async function ingestDocument() {
        const pdfFiles = document.getElementById('pdf-file').files;
        const text = document.getElementById('text-input').value.trim();
        let extractionContext = document.getElementById('extraction-context').value.trim();
        const maxConcepts = parseInt(document.getElementById('max-concepts').value);
        const maxRelationships = parseInt(document.getElementById('max-relationships').value);
        const model = document.getElementById('model-select').value;
        const useGraphContext = document.getElementById('use-graph-context').checked;
        
        if (pdfFiles.length === 0 && !text) {
          showStatus('error', 'Please upload PDF file(s) or paste text');
          return;
        }
        
        // Get graph context if checkbox is checked
        if (useGraphContext) {
          console.log('Graph context is enabled, fetching...');
          const graphContext = await getGraphContextText();
          if (graphContext) {
            console.log('Graph context fetched successfully');
            // Prepend graph context to user extraction context
            if (extractionContext) {
              extractionContext = graphContext + 'USER FOCUS: ' + extractionContext;
            } else {
              extractionContext = graphContext;
            }
          } else {
            showStatus('error', 'Failed to load graph context. Please try again or uncheck the option.');
            return;
          }
        }
        
        const btn = document.getElementById('ingest-btn');
        convertButtonToStatusBar('Queuing...');
        btn.disabled = true;
        
        // Handle text input (single document)
        if (!pdfFiles.length && text) {
          showStatus('processing', 'Queuing text for processing...');
          try {
            const response = await fetch('/api/ingest/text_async', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text,
                document_title: title || 'Text Upload',
                document_id: `user-${currentUser.user_id}-${Date.now()}`,
                user_id: currentUser.user_id,
                user_first_name: currentUser.first_name || '',
                user_last_name: currentUser.last_name || '',
                user_email: currentUser.email || '',
                max_concepts: maxConcepts,
                max_relationships: maxRelationships,
                extraction_context: extractionContext
              })
            });
            
            if (!response.ok) {
              const error = await response.json();
              throw new Error(error.detail || 'Failed to queue job');
            }
            
            const result = await response.json();
            showStatus('processing', `✓ Job queued! ID: ${result.job_id}`);
            
            // Poll for job completion
            await pollJobStatus(result.job_id, 'text');
            
            // Clear form
            document.getElementById('text-input').value = '';
            document.getElementById('extraction-context').value = '';
            await loadDocuments();
          } catch (e) {
            showStatus('error', '✗ Error: ' + e.message);
          } finally {
            restoreButton();
            btn.disabled = false;
          }
          return;
        }
        
        // Handle PDF file(s) - multiple files with progress bar
        if (pdfFiles.length > 0) {
          showProgress(true);
          hideStatus();
          
          const files = Array.from(pdfFiles);
          const totalFiles = files.length;
          const results = {
            successful: 0,
            failed: 0,
            totalTriplets: 0,
            jobIds: []
          };
          
          // Initialize file list status
          const fileListEl = document.getElementById('file-list-status');
          fileListEl.innerHTML = files.map((file, index) => 
            `<div id="file-status-${index}" class="file-status-item pending">
              <span>⏳</span>
              <span>${file.name}</span>
            </div>`
          ).join('');
          
          try {
            // Stage 1: Queue all files
            updateProgress(10, 100, 'Queuing files...');
            updateStatusBar('Queuing files for processing...');
            
            for (let i = 0; i < files.length; i++) {
              const file = files[i];
              const fileStatusEl = document.getElementById(`file-status-${i}`);
              
              // Calculate progress for queuing stage
              const queueProgress = 10 + ((i / totalFiles) * 20); // 10-30%
              updateProgress(queueProgress, 100, `Queuing: ${file.name}`);
              updateStatusBar(`Queuing ${i + 1}/${totalFiles}: ${file.name}`);
              
              fileStatusEl.className = 'file-status-item processing';
              fileStatusEl.innerHTML = `<span>📤</span><span>Queuing: ${file.name}</span>`;
              
              try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('user_id', currentUser.user_id);
                formData.append('user_first_name', currentUser.first_name || '');
                formData.append('user_last_name', currentUser.last_name || '');
                formData.append('user_email', currentUser.email || '');
                formData.append('max_concepts', maxConcepts);
                formData.append('max_relationships', maxRelationships);
                if (extractionContext) formData.append('extraction_context', extractionContext);
                
                const response = await fetch('/api/ingest/pdf_async', {
                  method: 'POST',
                  body: formData
                });
                
                if (!response.ok) {
                  const error = await response.json();
                  throw new Error(error.detail || 'Failed to queue job');
                }
                
                const result = await response.json();
                results.jobIds.push({
                  jobId: result.job_id,
                  fileName: file.name,
                  index: i
                });
                
                fileStatusEl.innerHTML = `<span>⏳</span><span>Queued: ${file.name}</span>`;
                
              } catch (e) {
                results.failed++;
                fileStatusEl.className = 'file-status-item error';
                fileStatusEl.innerHTML = `<span>✗</span><span>${file.name} - ${e.message}</span>`;
                console.error('Queue error:', e);
              }
            }
            
            // Stage 2: Poll all jobs for completion
            updateProgress(30, 100, 'Processing files...');
            updateStatusBar('Processing files in background...');
            
            const pollingPromises = results.jobIds.map(async (jobInfo) => {
              const { jobId, fileName, index } = jobInfo;
              const fileStatusEl = document.getElementById(`file-status-${index}`);
              
              try {
                // Poll for this specific job
                const jobResult = await pollJobStatus(jobId, 'pdf', fileName, index, totalFiles);
                
                if (jobResult.success) {
                  results.successful++;
                  results.totalTriplets += jobResult.triplets_written || 0;
                  
                  fileStatusEl.className = 'file-status-item success';
                  const extracted = jobResult.triplets_extracted || 0;
                  const written = jobResult.triplets_written || 0;
                  fileStatusEl.innerHTML = `<span>✓</span><span>${fileName} (${written} relationships)</span>`;
                } else {
                  results.failed++;
                  fileStatusEl.className = 'file-status-item error';
                  fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${jobResult.error}</span>`;
                }
              } catch (e) {
                results.failed++;
                fileStatusEl.className = 'file-status-item error';
                fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${e.message}</span>`;
                console.error('Polling error:', e);
              }
            });
            
            // Wait for all jobs to complete
            await Promise.all(pollingPromises);
            
            // Show final summary
            updateProgress(100, 100, 'All files processed!');
            updateStatusBar('✓ Complete!');
            setTimeout(() => {
              showProgress(false);
              restoreButton();
              if (results.failed === 0) {
                showStatus('success', 
                  `✓ All ${results.successful} file(s) processed successfully! Total: ${results.totalTriplets} relationships extracted.`
                );
              } else {
                showStatus('error', 
                  `⚠ Processed ${results.successful} file(s) successfully, ${results.failed} failed. Total: ${results.totalTriplets} relationships extracted.`
                );
              }
            }, 1500);
            
            // Clear form
            document.getElementById('pdf-file').value = '';
            document.getElementById('extraction-context').value = '';
            displayFileName();
            await loadDocuments();
            
          } catch (e) {
            showProgress(false);
            showStatus('error', '✗ Error: ' + e.message);
          } finally {
            restoreButton();
            btn.disabled = false;
          }
        }
      }
      
      // New function to poll job status
      async function pollJobStatus(jobId, type, fileName = null, fileIndex = null, totalFiles = null) {
        const maxAttempts = 300; // 5 minutes max (1 second intervals)
        let attempts = 0;
        
        return new Promise((resolve, reject) => {
          const pollInterval = setInterval(async () => {
            attempts++;
            
            try {
              const response = await fetch(`/api/ingest/job/${jobId}`);
              
              if (!response.ok) {
                throw new Error('Failed to check job status');
              }
              
              const job = await response.json();
              
              // Update progress for this specific file if it's a PDF
              if (type === 'pdf' && fileName && fileIndex !== null && totalFiles) {
                const fileProgressStart = 30 + ((fileIndex / totalFiles) * 60); // 30-90%
                const fileProgressEnd = 30 + (((fileIndex + 1) / totalFiles) * 60);
                
                if (job.status === 'processing') {
                  const progress = fileProgressStart + ((fileProgressEnd - fileProgressStart) * 0.5);
                  updateProgress(progress, 100, `Processing: ${fileName}`);
                  updateStatusBar(`Processing ${fileIndex + 1}/${totalFiles}: ${fileName}`);
                } else if (job.status === 'completed') {
                  updateProgress(fileProgressEnd, 100, `Complete: ${fileName}`);
                }
              } else if (type === 'text') {
                // Update status for text processing
                if (job.status === 'processing') {
                  showStatus('processing', `Processing text... (Job: ${jobId})`);
                } else if (job.status === 'completed') {
                  showStatus('success', `✓ Success! Extracted ${job.triplets_extracted} relationships.`);
                }
              }
              
              if (job.status === 'completed') {
                clearInterval(pollInterval);
                resolve({
                  success: true,
                  triplets_extracted: job.triplets_extracted,
                  triplets_written: job.triplets_written,
                  document_title: job.document_title
                });
              } else if (job.status === 'failed') {
                clearInterval(pollInterval);
                resolve({
                  success: false,
                  error: job.error_message || 'Processing failed'
                });
              } else if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                resolve({
                  success: false,
                  error: 'Job timed out after 5 minutes'
                });
              }
              
            } catch (e) {
              if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                reject(e);
              }
            }
          }, 1000); // Poll every second
        });
      }
      
      function convertButtonToStatusBar(statusText) {
        const btn = document.getElementById('ingest-btn');
        btn.classList.add('as-status-bar');
        btn.innerHTML = `
          <span>${statusText}</span>
          <span class="status-icon">⚙️</span>
        `;
        btn.onclick = null; // Disable click while processing
      }
      
      function updateStatusBar(statusText) {
        const btn = document.getElementById('ingest-btn');
        if (btn.classList.contains('as-status-bar')) {
          btn.innerHTML = `
            <span>${statusText}</span>
            <span class="status-icon">⚙️</span>
          `;
        }
      }
      
      function restoreButton() {
        const btn = document.getElementById('ingest-btn');
        btn.classList.remove('as-status-bar');
        btn.innerHTML = '🚀 Extract Knowledge';
        btn.onclick = ingestDocument;
      }
      
      function showProgress(show) {
        const progressContainer = document.getElementById('progress-container');
        if (show) {
          progressContainer.classList.add('active');
        } else {
          progressContainer.classList.remove('active');
        }
      }
      
      function updateProgress(current, total, statusText) {
        const percentage = Math.round((current / total) * 100);
        document.getElementById('progress-bar-fill').style.width = percentage + '%';
        document.getElementById('progress-percentage').textContent = percentage + '%';
        document.getElementById('progress-count').textContent = `${current} / ${total}`;
        document.getElementById('progress-text').textContent = statusText;
        document.getElementById('current-file-status').textContent = statusText;
      }
      
      function simulateProgress(startPercent, endPercent, total, baseStatusText) {
        let currentPercent = startPercent;
        const increment = (endPercent - startPercent) / 60; // 60 steps over ~60 seconds
        const statusMessages = [
          'Analyzing document structure...',
          'Extracting text content...',
          'Identifying entities...',
          'Finding relationships...',
          'Validating triplets...',
          'Processing relationships...'
        ];
        
        return setInterval(() => {
          if (currentPercent < endPercent) {
            currentPercent += increment;
            const statusIndex = Math.floor((currentPercent - startPercent) / (endPercent - startPercent) * statusMessages.length);
            const statusText = statusMessages[Math.min(statusIndex, statusMessages.length - 1)];
            
            updateProgress(currentPercent, total, `${baseStatusText} - ${statusText}`);
          }
        }, 1000); // Update every second
      }
      
      function hideStatus() {
        const statusEl = document.getElementById('ingest-status');
        statusEl.className = '';
        statusEl.textContent = '';
      }
      
      function showStatus(type, message) {
        const statusEl = document.getElementById('ingest-status');
        statusEl.className = type;
        statusEl.textContent = message;
      }
      
      // ==========================================
      // GRAPH VIEWING & VISUALIZATION FUNCTIONS
      // ==========================================
      function initCytoscape() {
        cytoscape.use(cytoscapeDagre);
        
        cy = cytoscape({
          container: document.getElementById('cy'),
          elements: [],
          wheelSensitivity: 0.2,
          minZoom: 0.1,
          maxZoom: 3,
          // Performance optimizations
          textureOnViewport: true,
          motionBlur: false,
          motionBlurOpacity: 0.2,
          hideEdgesOnViewport: false,
          hideLabelsOnViewport: false,
          pixelRatio: 'auto',
          style: [
            {
              selector: 'node',
              style: {
                'label': 'data(label)',
                'font-size': '12px',
                'text-wrap': 'wrap',
                'text-max-width': 150,
                'text-halign': 'center',
                'text-valign': 'center',
                'background-color': '#667eea',
                'color': '#ffffff',
                'text-outline-color': '#667eea',
                'text-outline-width': 2,
                // Size based on significance: 40px (sig=1) to 80px (sig=5)
                'width': function(ele) {
                  const sig = ele.data('significance');
                  return sig ? (30 + sig * 10) : 50;
                },
                'height': function(ele) {
                  const sig = ele.data('significance');
                  return sig ? (30 + sig * 10) : 50;
                },
                'border-width': 2,
                'border-color': '#5568d3'
              }
            },
            {
              selector: 'edge',
              style: {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                // Width based on BOTH significance AND source count
                'width': function(ele) {
                  const sig = ele.data('significance');
                  const sources = ele.data('sources') || [];
                  const sourceCount = sources.length;
                  
                  // Base width from significance (1.8 to 5px)
                  let width = sig ? (1 + sig * 0.8) : 2.5;
                  
                  // Bonus from multiple sources (+0.5px per additional source, max +2px)
                  if (sourceCount > 1) {
                    width += Math.min((sourceCount - 1) * 0.5, 2);
                  }
                  
                  return width;
                },
                'line-color': '#94a3b8',
                'target-arrow-color': '#94a3b8',
                'label': 'data(relation)',
                'font-size': '11px',
                'color': '#374151',
                'text-background-color': '#ffffff',
                'text-background-opacity': 0.8,
                'text-background-padding': 3,
                'edge-text-rotation': 'autorotate'
              }
            },
            {
              selector: 'edge[status = "verified"]',
              style: {
                'line-color': '#059669',
                'target-arrow-color': '#059669',
                'width': 3.5
              }
            },
            {
              selector: 'edge[status = "incorrect"]',
              style: {
                'line-color': '#dc2626',
                'target-arrow-color': '#dc2626',
                'line-style': 'dashed',
                'width': 2
              }
            },
            {
              selector: 'edge[polarity = "negative"]',
              style: {
                'line-style': 'dotted'
              }
            },
            {
              selector: 'node.highlighted',
              style: {
                'background-color': '#dc2626',
                'border-color': '#991b1b',
                'border-width': 4,
                'z-index': 999
              }
            },
            {
              selector: 'node.neighbor',
              style: {
                'background-color': '#f59e0b',
                'border-color': '#d97706',
                'border-width': 3
              }
            },
            {
              selector: 'node.multi-selected',
              style: {
                'background-color': '#8b5cf6',
                'border-color': '#7c3aed',
                'border-width': 4
              }
            },
            {
              selector: 'node.manual-selected',
              style: {
                'background-color': '#10b981',
                'border-color': '#059669',
                'border-width': 4,
                'border-style': 'dashed'
              }
            },
            {
              selector: 'node:selected',
              style: {
                'background-color': '#1d4ed8',
                'border-color': '#1e40af',
                'border-width': 3
              }
            },
            {
              selector: 'edge:selected',
              style: {
                'line-color': '#1d4ed8',
                'target-arrow-color': '#1d4ed8',
                'width': 4
              }
            }
          ]
        });
        
        // Node click handler with multi-select support
        cy.on('tap', 'node', function(evt) {
          const node = evt.target;
          const nodeId = node.id();
          const nodeLabel = node.data('label');
          
          // Check if shift key is pressed for multi-select
          if (evt.originalEvent && evt.originalEvent.shiftKey) {
            // Toggle selection
            if (selectedNodes.has(nodeId)) {
              selectedNodes.delete(nodeId);
              node.removeClass('multi-selected');
            } else {
              selectedNodes.add(nodeId);
              node.addClass('multi-selected');
            }
            updateSelectionInfo();
          } else if (evt.originalEvent && evt.originalEvent.ctrlKey) {
            // Ctrl+Click for manual edge creation
            console.log('Ctrl+Click detected on node:', nodeLabel);
            if (!manualEdgeNodes.node1) {
              manualEdgeNodes.node1 = { id: nodeId, label: nodeLabel, node: node };
              node.addClass('manual-selected');
              document.getElementById('selected-node-1').innerHTML = `Node 1: <span style="color: #10b981; font-weight: 600;">✓ ${nodeLabel}</span>`;
              console.log('Set node 1:', nodeLabel);
            } else if (!manualEdgeNodes.node2) {
              manualEdgeNodes.node2 = { id: nodeId, label: nodeLabel, node: node };
              node.addClass('manual-selected');
              document.getElementById('selected-node-2').innerHTML = `Node 2: <span style="color: #10b981; font-weight: 600;">✓ ${nodeLabel}</span>`;
              document.getElementById('create-edge-btn').disabled = false;
              console.log('Set node 2:', nodeLabel, '- Button enabled');
            } else {
              console.log('Both nodes already selected. Clear selection first.');
              alert('Both nodes already selected. Click "Clear Selection" first.');
            }
          } else {
            // Regular click - show details
            showNodeDetails(evt);
          }
        });
        
        // Edge hover tooltip with delay
        // Node tooltip handlers
        cy.on('mouseover', 'node', (evt) => {
          isOverNode = true;
          if (hideNodeTooltipTimeout) {
            clearTimeout(hideNodeTooltipTimeout);
          }
          showNodeTooltip(evt.target, evt);
        });
        
        cy.on('mouseout', 'node', () => {
          isOverNode = false;
          scheduleHideNodeTooltip();
        });
        
        // Edge tooltip handlers
        cy.on('mouseover', 'edge', (evt) => {
          isOverEdge = true;
          if (hideTooltipTimeout) {
            clearTimeout(hideTooltipTimeout);
          }
          showEdgeTooltip(evt.target, evt);
        });
        
        cy.on('mouseout', 'edge', () => {
          isOverEdge = false;
          scheduleHideTooltip();
        });
        
        // Keep old tap for backwards compatibility (now opens modal directly)
        cy.on('tap', 'edge', (evt) => {
          hideEdgeTooltip();
          showEdgeModal(evt.target.data());
        });
        
        // Tooltip mouse events - keep visible when hovering over tooltip
        const tooltip = document.getElementById('edge-tooltip');
        tooltip.addEventListener('mouseenter', () => {
          isOverTooltip = true;
          if (hideTooltipTimeout) {
            clearTimeout(hideTooltipTimeout);
          }
        });
        
        tooltip.addEventListener('mouseleave', () => {
          isOverTooltip = false;
          scheduleHideTooltip();
        });
        
        // Hide details on background click
        cy.on('tap', (evt) => {
          if (evt.target === cy) {
            hideDetails();
          }
        });

        // Keep a copy of all elements for in-memory filtering
        cy.scratch('_allElements', []);
      }
      
      async function loadDocuments() {
        try {
          const res = await fetch('/query/documents');
          const data = await res.json();
          const docs = data.documents || [];
          
          // Documents are now loaded in populateIndex, not in a select dropdown
          return docs;
        } catch (e) {
          console.error('Failed to load documents:', e);
          return [];
        }
      }
      
      async function loadAllData() {
        try {
          // Add cache-busting parameter to ensure fresh data
          const timestamp = new Date().getTime();
          const res = await fetch(`/query/all?t=${timestamp}`);
          const data = await res.json();
          
          // DEBUG: Check if original_text is in the API response
          if (data.relationships && data.relationships.length > 0) {
            const sampleRel = data.relationships[0];
            console.log('🔍 API Response sample relationship:', {
              relation: sampleRel.relation,
              original_text: sampleRel.original_text,
              has_original_text: !!sampleRel.original_text,
              all_keys: Object.keys(sampleRel)
            });
          }
          
          // Raw graph data loaded
          
          const nodeCount = (data.nodes || []).length;
          const edgeCount = (data.relationships || []).length;
          
          if (nodeCount === 0 && edgeCount === 0) {
            // No data yet - show helpful message
            alert('No data in the knowledge graph yet. Upload a document in the Ingestion tab to get started!');
            return;
          }
          
          // Check if we should use viewport-based loading for large graphs
          if (nodeCount > 200) {
            console.log('Large graph detected, enabling viewport-based loading');
            viewportMode = true;
            currentDocIds = []; // Load all documents
            await loadInitialViewport();
          } else {
            // Small graph - load everything at once
            viewportMode = false;
            if (cy) {
              cy.resize();
            }
            renderGraph(data);
          }
        } catch (e) {
          console.error('Failed to load all data:', e);
          alert('Failed to load graph data: ' + e.message);
        }
      }
      
      async function loadSelectedDocuments() {
        const select = document.getElementById('doc-select');
        const selected = Array.from(select.selectedOptions).map(o => o.value);
        
        if (selected.length === 0) {
          alert('Please select at least one document');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const url = `/query/graph_by_docs?doc_ids=${selected.join(',')}&verified_only=${verifiedOnly}`;
          const res = await fetch(url);
          const data = await res.json();
          
          renderGraph(data);
        } catch (e) {
          alert('Failed to load graph: ' + e.message);
        }
      }
      
      async function searchConcept() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) {
          alert('Please enter a search term');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const url = `/query/search/concept?name=${encodeURIComponent(query)}&verified_only=${verifiedOnly}`;
          const res = await fetch(url);
          const data = await res.json();
          
          // Check if we got data
          if (!data.nodes || data.nodes.length === 0) {
            alert('No results found for: ' + query);
            return;
          }
          
          renderGraph(data);
          
          // Highlight the searched node(s) and their neighbors
          setTimeout(() => {
            highlightSearchResults(query);
          }, 500);
        } catch (e) {
          alert('Search failed: ' + e.message);
        }
      }
      
      function highlightSearchResults(query) {
        if (!cy) return;
        
        const queryLower = query.toLowerCase();
        
        // Remove previous highlights
        cy.nodes().removeClass('highlighted neighbor');
        
        // Find matching nodes
        const matchedNodes = cy.nodes().filter(node => {
          const label = (node.data('label') || '').toLowerCase();
          return label.includes(queryLower);
        });
        
        if (matchedNodes.length === 0) return;
        
        // Highlight matched nodes
        matchedNodes.addClass('highlighted');
        
        // Highlight their neighbors
        matchedNodes.forEach(node => {
          node.neighborhood('node').addClass('neighbor');
        });
        
        // Fit view to highlighted nodes
        cy.fit(matchedNodes, 50);
      }
      
      function renderGraph(data) {
        const elements = [];
        
        (data.nodes || []).forEach(n => {
          elements.push({
            data: {
              id: n.id,
              label: n.label || n.id,
              type: n.type,
              sources: n.sources,
              significance: n.significance
            }
          });
        });
        
        (data.relationships || []).forEach(r => {
          elements.push({
            data: {
              id: r.id,
              source: r.source,
              target: r.target,
              relation: r.relation,
              status: r.status || 'unverified',
              polarity: r.polarity || 'positive',
              confidence: r.confidence,
              significance: r.significance,
              sources: r.sources,
              page_number: r.page_number,
              original_text: r.original_text,
              reviewed_by_first_name: (r.reviewed_by_first_name ?? null),
              reviewed_by_last_name: (r.reviewed_by_last_name ?? null),
              reviewed_at: (r.reviewed_at ?? null)
            }
          });
        });
        
        cy.elements().remove();
        
        if (elements.length === 0) {
          // Show empty state
          document.getElementById('details-content').innerHTML = `
            <p style="color: #6b7280; text-align: center; padding: 20px;">
              No data to display.<br><br>
              Select documents and click "Load Graph" or use the search function.
            </p>
          `;
          return;
        }
        
        cy.add(elements);
        // Apply filters (including negative toggle) after elements are added
        filterGraphBySearch(document.getElementById('search-input')?.value || '');
        // Save full set for client-side filtering
        cy.scratch('_allElements', elements);
        
        // Use a better layout based on graph size
        const nodeCount = (data.nodes || []).length;
        let layoutConfig;
        
        if (nodeCount > 200) {
          // For very large graphs, use a faster layout with fewer iterations
          layoutConfig = {
            name: 'cose',
            idealEdgeLength: 80,
            nodeOverlap: 30,
            refresh: 20,
            fit: true,
            padding: 20,
            randomize: false,
            componentSpacing: 80,
            nodeRepulsion: 600000,
            edgeElasticity: 80,
            nestingFactor: 5,
            gravity: 100,
            numIter: 500, // Reduced iterations for speed
            initialTemp: 150,
            coolingFactor: 0.9,
            minTemp: 1.0
          };
        } else if (nodeCount > 50) {
          // For large graphs, use force-directed layout
          layoutConfig = {
            name: 'cose',
            idealEdgeLength: 100,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
          };
        } else {
          // For smaller graphs, also use force-directed layout for better spreading
          layoutConfig = {
            name: 'cose',
            idealEdgeLength: 120,
            nodeOverlap: 10,
            refresh: 20,
            fit: true,
            padding: 40,
            randomize: false,
            componentSpacing: 120,
            nodeRepulsion: 200000,
            edgeElasticity: 120,
            nestingFactor: 5,
            gravity: 80,
            numIter: 800,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
          };
        }
        
        // Ensure container is properly sized before layout
        cy.resize();
        
        const layout = cy.layout(layoutConfig);
        layout.run();
        
        // Fit after layout completes
        layout.on('layoutstop', () => {
          setTimeout(async () => {
            cy.fit(undefined, 30);
            // Populate index after graph is rendered
            await populateIndex();
            
            // Enable viewport-based loading for large graphs
            if (viewportMode && nodeCount > 200) {
              enableViewportLoading();
            }
          }, 50);
        });
      }
      
      // ==========================================
      // VIEWPORT-BASED LOADING FUNCTIONS
      // ==========================================
      
      function getViewportBounds() {
        const extent = cy.extent();
        return {
          minX: extent.x1,
          minY: extent.y1,
          maxX: extent.x2,
          maxY: extent.y2
        };
      }
      
      function getZoomLevel() {
        return cy.zoom();
      }
      
      async function loadInitialViewport() {
        if (!cy) return;
        
        // Get initial viewport bounds
        const viewport = getViewportBounds();
        const zoomLevel = getZoomLevel();
        
        console.log('Loading initial viewport:', viewport, 'zoom:', zoomLevel);
        
        // Load initial data for the viewport
        await loadViewportData(viewport, zoomLevel);
      }
      
      async function loadViewportData(viewport, zoomLevel, centerNodeId = null) {
        if (isLoading || currentDocIds.length === 0) return;
        
        isLoading = true;
        showLoadingIndicator('Loading viewport data...');
        console.log('Loading viewport data...');
        
        try {
          const verifiedParam = document.getElementById('verified-only')?.checked ? '&verified_only=true' : '';
          const centerParam = centerNodeId ? `&center_node_id=${encodeURIComponent(centerNodeId)}` : '';
          const docIdsParam = currentDocIds.length > 0 ? `&doc_ids=${encodeURIComponent(currentDocIds.join(','))}` : '';
          const url = `/query/viewport?min_x=${viewport.minX}&min_y=${viewport.minY}&max_x=${viewport.maxX}&max_y=${viewport.maxY}&zoom_level=${zoomLevel}${verifiedParam}${centerParam}${docIdsParam}`;
          
          const res = await fetch(url);
          if (!res.ok) throw new Error('Failed to fetch viewport data');
          
          const data = await res.json();
          
          // Add new nodes and edges
          const newElements = toCytoscapeElements(data);
          const existingIds = new Set(cy.elements().map(el => el.id()));
          const elementsToAdd = newElements.filter(el => !existingIds.has(el.data.id));
          
          if (elementsToAdd.length > 0) {
            cy.add(elementsToAdd);
            elementsToAdd.forEach(el => {
              if (el.data.id) loadedNodes.add(el.data.id);
            });
            console.log(`Added ${elementsToAdd.length} new elements to viewport`);
          }
          
        } catch (e) {
          console.error('Error loading viewport:', e.message);
        } finally {
          isLoading = false;
          hideLoadingIndicator();
        }
      }
      
      async function loadNodeNeighborhood(nodeId) {
        if (isLoading) return;
        
        isLoading = true;
        console.log('Loading neighborhood for node:', nodeId);
        
        try {
          const verifiedParam = document.getElementById('verified-only')?.checked ? '&verified_only=true' : '';
          const url = `/query/neighborhood?node_id=${encodeURIComponent(nodeId)}&max_hops=2${verifiedParam}`;
          
          const res = await fetch(url);
          if (!res.ok) throw new Error('Failed to fetch neighborhood');
          
          const data = await res.json();
          
          // Add new nodes and edges
          const newElements = toCytoscapeElements(data);
          const existingIds = new Set(cy.elements().map(el => el.id()));
          const elementsToAdd = newElements.filter(el => !existingIds.has(el.data.id));
          
          if (elementsToAdd.length > 0) {
            cy.add(elementsToAdd);
            elementsToAdd.forEach(el => {
              if (el.data.id) loadedNodes.add(el.data.id);
            });
            console.log(`Added ${elementsToAdd.length} neighborhood elements`);
          }
          
        } catch (e) {
          console.error('Error loading neighborhood:', e.message);
        } finally {
          isLoading = false;
        }
      }
      
      function scheduleViewportUpdate() {
        if (viewportUpdateTimeout) {
          clearTimeout(viewportUpdateTimeout);
        }
        
        viewportUpdateTimeout = setTimeout(() => {
          const viewport = getViewportBounds();
          const zoomLevel = getZoomLevel();
          
          // Only update if viewport has changed significantly
          if (!lastViewport || 
              Math.abs(viewport.minX - lastViewport.minX) > 100 ||
              Math.abs(viewport.minY - lastViewport.minY) > 100 ||
              Math.abs(viewport.maxX - lastViewport.maxX) > 100 ||
              Math.abs(viewport.maxY - lastViewport.maxY) > 100 ||
              Math.abs(zoomLevel - lastViewport.zoomLevel) > 0.2) {
            
            lastViewport = { ...viewport, zoomLevel };
            loadViewportData(viewport, zoomLevel);
          }
        }, 500); // Debounce viewport updates
      }
      
      function enableViewportLoading() {
        if (!cy) return;
        
        console.log('Enabling viewport-based loading');
        
        // Add event listeners for viewport changes
        cy.on('pan', scheduleViewportUpdate);
        cy.on('zoom', scheduleViewportUpdate);
        
        // Add click handler for neighborhood loading
        cy.on('tap', 'node', function(evt) {
          if (viewportMode && !evt.originalEvent?.shiftKey && !evt.originalEvent?.ctrlKey) {
            const nodeId = evt.target.id();
            if (!loadedNodes.has(nodeId)) {
              loadNodeNeighborhood(nodeId);
            }
          }
        });
      }
      
      function toCytoscapeElements(graph) {
        const elements = [];
        
        (graph.nodes || []).forEach(n => {
          elements.push({
            data: {
              id: n.id,
              label: n.label || n.id,
              type: n.type,
              sources: n.sources,
              significance: n.significance
            }
          });
        });
        
        (graph.relationships || []).forEach(r => {
          elements.push({
            data: {
              id: r.id,
              source: r.source,
              target: r.target,
              relation: r.relation,
              status: r.status || 'unverified',
              polarity: r.polarity || 'positive',
              confidence: r.confidence,
              significance: r.significance,
              sources: r.sources,
              page_number: r.page_number,
              original_text: r.original_text,
              reviewed_by_first_name: (r.reviewed_by_first_name ?? null),
              reviewed_by_last_name: (r.reviewed_by_last_name ?? null),
              reviewed_at: (r.reviewed_at ?? null)
            }
          });
        });
        
        return elements;
      }
      
      // Loading indicator functions
      function showLoadingIndicator(message = 'Loading...') {
        let indicator = document.getElementById('viewport-loading-indicator');
        if (!indicator) {
          indicator = document.createElement('div');
          indicator.id = 'viewport-loading-indicator';
          indicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 8px;
          `;
          document.body.appendChild(indicator);
        }
        
        indicator.innerHTML = `
          <div style="width: 16px; height: 16px; border: 2px solid #ffffff; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
          ${message}
        `;
        indicator.style.display = 'flex';
      }
      
      function hideLoadingIndicator() {
        const indicator = document.getElementById('viewport-loading-indicator');
        if (indicator) {
          indicator.style.display = 'none';
        }
      }
      
      // Show/hide FABs based on manual node selection
      function updateFabVisibility() {
        const fabContainer = document.getElementById('fab-container');
        if (!fabContainer) return;
        
        // Check if we're on viewing tab
        const viewingTab = document.getElementById('viewing-tab');
        const isViewingTab = viewingTab && viewingTab.classList.contains('active');
        
        // Check if nodes are manually selected (Shift+Click)
        const hasSelection = selectedNodes && selectedNodes.size > 0;
        
        if (isViewingTab && hasSelection) {
          fabContainer.classList.remove('hidden');
        } else {
          fabContainer.classList.add('hidden');
        }
      }

      async function filterGraphBySearch(q) {
        if (!cy) return;
        const term = (q || '').trim().toLowerCase();
        const showNegative = document.getElementById('show-negative')?.checked === true;
        const verifiedOnly = document.getElementById('verified-only')?.checked === true;
        
        // If no search term, show everything and remove highlights
        if (!term) {
          cy.nodes().removeClass('highlighted neighbor').style('display', 'element');
          cy.edges().forEach(e => {
            const edgePolarity = String(e.data('polarity') || 'positive').toLowerCase();
            const polarityOk = showNegative ? true : edgePolarity !== 'negative';
            const statusOk = verifiedOnly ? (String(e.data('status') || '') === 'verified') : true;
            e.style('display', (polarityOk && statusOk) ? 'element' : 'none');
          });
          return;
        }

        // Step 1: Find matching nodes (nodes that match the search term)
        const matchingNodes = cy.nodes().filter(n => {
          const label = String(n.data('label') || '').toLowerCase();
          return label.includes(term);
        });
        
        // Step 2: Find neighbors of matching nodes (1-hop away)
        const neighbors = matchingNodes.neighborhood('node');
        
        // Step 3: Combine matching nodes + their neighbors
        const nodesToShow = matchingNodes.union(neighbors);
        
        // Step 4: Hide all nodes first, remove old highlights, then show only relevant ones
        cy.nodes().removeClass('highlighted neighbor').style('display', 'none');
        nodesToShow.style('display', 'element');
        
        // Step 5: Apply visual highlighting
        // Matched nodes get RED highlight
        matchingNodes.addClass('highlighted');
        // Neighbors get ORANGE highlight
        neighbors.addClass('neighbor');

        // Step 6: Show edges between visible nodes
        cy.edges().forEach(e => {
          const src = e.source();
          const tgt = e.target();
          // Show edge if BOTH endpoints are visible
          const endpointsVisible = src.style('display') !== 'none' && tgt.style('display') !== 'none';
          const edgePolarity = String(e.data('polarity') || 'positive').toLowerCase();
          const polarityOk = showNegative ? true : edgePolarity !== 'negative';
          const statusOk = verifiedOnly ? (String(e.data('status') || '') === 'verified') : true;
          const keep = endpointsVisible && polarityOk && statusOk;
          e.style('display', keep ? 'element' : 'none');
        });
      }
      
      function showNodeDetails(evt) {
        const node = evt.target;
        const data = node.data();
        
        console.log('Node clicked:', data);
        console.log('Node sources:', data.sources);
        
        // Show details panel
        showDetailsPanel();
        
        const detailsContent = document.getElementById('details-content');
        if (!detailsContent) {
          console.error('details-content element not found!');
          return;
        }
        
        const sources = data.sources || [];
        console.log('Sources array:', sources, 'Length:', sources.length);
        console.log('First source details:', sources[0]);
        let sourcesHtml = '';
        if (sources.length === 0 || !sources || (sources.length === 1 && !sources[0].id)) {
          sourcesHtml = '<div class="detail-value" style="color: #ef4444;">No sources recorded</div>';
        } else {
          sourcesHtml = `
            <div class="detail-value" style="font-weight: 600;">${sources.length} document(s)</div>
            <div style="margin-top: 8px; font-size: 12px; color: #6b7280;">
              ${sources.map(s => {
                const title = (typeof s === 'object' && s.title) ? s.title : s;
                const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
                const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
                const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
                return `<div style="padding: 4px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}<span style="color: #6b7280; font-size: 12px;">${userName}</span></div>`;
              }).join('')}
            </div>
          `;
        }
        
        // Significance display
        let significanceHtml = '';
        if (data.significance) {
          const stars = '⭐'.repeat(data.significance);
          const emptyStars = '☆'.repeat(5 - data.significance);
          significanceHtml = `
            <div class="detail-section">
              <div class="detail-label">Significance</div>
              <div class="detail-value" style="font-size: 18px; color: #f59e0b;">
                ${stars}${emptyStars}
                <span style="font-size: 12px; color: #6b7280; margin-left: 8px;">(${data.significance}/5)</span>
              </div>
            </div>
          `;
        }
        
        detailsContent.innerHTML = `
          <div class="detail-section">
            <div class="detail-label">Node</div>
            <div class="detail-value" style="font-weight: 600; font-size: 16px;">${data.label}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Type</div>
            <div class="detail-value">${data.type || 'N/A'}</div>
          </div>
          ${significanceHtml}
          <div class="detail-section">
            <div class="detail-label">ID</div>
            <div class="detail-value" style="font-family: monospace; font-size: 12px;">${data.id}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Sources</div>
            ${sourcesHtml}
          </div>
        `;
      }
      
      function showEdgeDetails(evt) {
        const edge = evt.target;
        const data = edge.data();
        
        console.log('Edge clicked:', data);
        
        // Show details panel
        showDetailsPanel();
        
        const statusClass = `status-${data.status || 'unverified'}`;
        const sources = data.sources || [];
        
        let sourcesHtml = '';
        if (sources.length === 0) {
          sourcesHtml = '<div class="detail-value" style="color: #ef4444;">No sources recorded</div>';
        } else {
          sourcesHtml = `
            <div class="detail-value" style="font-weight: 600;">${sources.length} document(s)</div>
            <div style="margin-top: 8px; font-size: 12px; color: #6b7280;">
              ${sources.map(s => {
                // s is now an object with {id, title, created_by_first_name, created_by_last_name}
                const title = (typeof s === 'object' && s.title) ? s.title : s;
                const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
                const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
                const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
                return `<div style="padding: 4px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}<span style="color: #6b7280; font-size: 12px;">${userName}</span></div>`;
              }).join('')}
            </div>
          `;
        }
        
        // Build reviewer info if available
        let reviewerHtml = '';
        if (data.status === 'verified' || data.status === 'incorrect') {
          const reviewerFirstName = data.reviewed_by_first_name || '';
          const reviewerLastName = data.reviewed_by_last_name || '';
          const reviewerName = reviewerFirstName && reviewerLastName ? 
            `${reviewerFirstName} ${reviewerLastName}` : 
            (reviewerFirstName || reviewerLastName || 'Unknown');
          
          const reviewDate = data.reviewed_at ? new Date(data.reviewed_at).toLocaleString() : 'N/A';
          const actionText = data.status === 'verified' ? 'Verified' : 'Flagged';
          
          reviewerHtml = `
            <div class="detail-section">
              <div class="detail-label">${actionText} By</div>
              <div class="detail-value">
                <div style="font-weight: 600;">${reviewerName}</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">${reviewDate}</div>
              </div>
            </div>
          `;
        }
        
        // Significance display for relationships
        let relSignificanceHtml = '';
        if (data.significance) {
          const stars = '⭐'.repeat(data.significance);
          const emptyStars = '☆'.repeat(5 - data.significance);
          relSignificanceHtml = `
            <div class="detail-section">
              <div class="detail-label">Significance</div>
              <div class="detail-value" style="font-size: 18px; color: #f59e0b;">
                ${stars}${emptyStars}
                <span style="font-size: 12px; color: #6b7280; margin-left: 8px;">(${data.significance}/5)</span>
              </div>
            </div>
          `;
        }
        
        // Page number display
        let pageNumberHtml = '';
        if (data.page_number) {
          pageNumberHtml = `
            <div class="detail-section">
              <div class="detail-label">Page Number</div>
              <div class="detail-value" style="font-weight: 600; color: #3b82f6;">
                📄 Page ${data.page_number}
              </div>
            </div>
          `;
        }
        
        document.getElementById('details-content').innerHTML = `
          <div class="detail-section">
            <div class="detail-label">Relationship</div>
            <div class="detail-value" style="font-weight: 600; font-size: 16px; color: #667eea;">${data.relation}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">From → To</div>
            <div class="detail-value" style="line-height: 1.6;">
              <div><strong>From:</strong> ${data.source}</div>
              <div><strong>To:</strong> ${data.target}</div>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Status</div>
            <div class="detail-value">
              <span class="status-badge ${statusClass}">${data.status || 'unverified'}</span>
            </div>
          </div>
          ${relSignificanceHtml}
          ${pageNumberHtml}
          ${reviewerHtml}
          <div class="detail-section">
            <div class="detail-label">Sources</div>
            ${sourcesHtml}
          </div>
        `;
      }
      
      function showDetailsPanel() {
        const panel = document.getElementById('details-panel');
        const viewingPanel = document.getElementById('viewing-panel');
        
        if (!panel || !viewingPanel) return;
        
        panel.classList.add('visible');
        viewingPanel.classList.add('details-visible');
        
        // Resize cytoscape multiple times to ensure it adapts
        if (cy) {
          requestAnimationFrame(() => {
            cy.resize();
            cy.fit(null, 50);
          });
          setTimeout(() => {
            cy.resize();
            cy.fit(null, 50);
          }, 100);
          setTimeout(() => {
            cy.resize();
          }, 350);
        }
      }
      
      function hideDetails() {
        const panel = document.getElementById('details-panel');
        const viewingPanel = document.getElementById('viewing-panel');
        
        if (!panel || !viewingPanel) return;
        
        panel.classList.remove('visible');
        viewingPanel.classList.remove('details-visible');
        
        if (cy) {
          cy.elements().unselect();
          
          // Resize cytoscape multiple times to ensure it adapts
          requestAnimationFrame(() => {
            cy.resize();
            cy.fit(null, 50);
          });
          setTimeout(() => {
            cy.resize();
            cy.fit(null, 50);
          }, 100);
          setTimeout(() => {
            cy.resize();
          }, 350);
        }
      }
      
      function updateSelectionInfo() {
        const count = selectedNodes.size;
        
        // Update FAB visibility based on selection
        updateFabVisibility();
        
        // Log selection for debugging
        if (count > 0) {
          console.log(`${count} node${count > 1 ? 's' : ''} selected`);
        }
      }
      
      // ==========================================
      // NODE SELECTION & REVIEW FUNCTIONS
      // ==========================================
      
      function clearSelection() {
        if (!cy) return;
        
        console.log('Clearing selection...');
        
        // Remove visual styling from all selected nodes
        cy.nodes('.multi-selected').forEach(node => {
          node.removeClass('multi-selected');
        });
        
        // Also unselect all nodes in Cytoscape
        cy.nodes().unselect();
        
        // Clear selection set
        selectedNodes.clear();
        
        // Update FAB visibility
        updateSelectionInfo();
        
        console.log('Selection cleared, nodes reset');
      }
      
      function reviewSelection() {
        if (selectedNodes.size === 0) {
          alert('Please select at least one node first (Shift+Click)');
          return;
        }
        
        // Convert Set to array and encode as URL parameter
        const nodeIds = Array.from(selectedNodes).join(',');
        const url = `/review-ui?filter_nodes=${encodeURIComponent(nodeIds)}`;
        
        // Open review queue in new tab with filtered nodes
        window.open(url, '_blank');
      }
      
      function toggleLegend() {
        const modal = document.getElementById('legend-modal-overlay');
        modal.classList.add('visible');
      }
      
      function closeLegendModal() {
        const modal = document.getElementById('legend-modal-overlay');
        modal.classList.remove('visible');
      }
      
      function clearManualSelection() {
        // Remove visual styling from nodes
        if (manualEdgeNodes.node1 && manualEdgeNodes.node1.node) {
          manualEdgeNodes.node1.node.removeClass('manual-selected');
        }
        if (manualEdgeNodes.node2 && manualEdgeNodes.node2.node) {
          manualEdgeNodes.node2.node.removeClass('manual-selected');
        }
        
        manualEdgeNodes = { node1: null, node2: null };
        document.getElementById('selected-node-1').innerHTML = 'Node 1: <span style="color: #9ca3af;">None</span>';
        document.getElementById('selected-node-2').innerHTML = 'Node 2: <span style="color: #9ca3af;">None</span>';
        document.getElementById('create-edge-btn').disabled = true;
      }
      
      function openCreateEdgeModal() {
        if (!manualEdgeNodes.node1 || !manualEdgeNodes.node2) {
          alert('Please select two nodes first (Ctrl+Click)');
          return;
        }
        
        document.getElementById('manual-from').value = manualEdgeNodes.node1.label;
        document.getElementById('manual-to').value = manualEdgeNodes.node2.label;
        document.getElementById('create-edge-modal').style.display = 'flex';
      }
      
      function closeCreateEdgeModal() {
        document.getElementById('create-edge-modal').style.display = 'none';
        document.getElementById('create-edge-form').reset();
      }
      
      async function saveManualEdge(event) {
        event.preventDefault();
        
        const relation = document.getElementById('manual-relation').value;
        const evidence = document.getElementById('manual-evidence').value;
        const confidence = parseFloat(document.getElementById('manual-confidence').value);
        
        try {
          const payload = {
            subject_id: manualEdgeNodes.node1.id,
            subject_name: manualEdgeNodes.node1.label,
            object_id: manualEdgeNodes.node2.id,
            object_name: manualEdgeNodes.node2.label,
            relation: relation,
            evidence: evidence,
            confidence: confidence,
            created_by: currentUser?.email || currentUser?.user_id || 'expert-user',
            created_by_first_name: currentUser?.first_name || '',
            created_by_last_name: currentUser?.last_name || ''
          };
          
          const response = await fetch('/api/manual/relationship', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          if (!response.ok) {
            throw new Error('Failed to create relationship');
          }
          
          closeCreateEdgeModal();
          clearManualSelection();
          alert('Manual relationship created successfully!');
          
          // Reload the graph to show the new relationship
          await loadAllData();
        } catch (e) {
          alert('Error creating relationship: ' + e.message);
        }
      }
      
      // ==========================================
      // PATHWAY DISCOVERY FUNCTIONS
      // ==========================================
      
      async function findShortestPath() {
        const source = document.getElementById('pathway-source').value.trim();
        const target = document.getElementById('pathway-target').value.trim();
        
        if (!source || !target) {
          alert('Please enter both source and target concepts');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const response = await fetch(`/api/pathway/shortest-path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}&verified_only=${verifiedOnly}`);
          
          if (!response.ok) {
            throw new Error('Pathway search failed');
          }
          
          const data = await response.json();
          
          if (!data.path_found) {
            alert(data.message || 'No path found between these concepts');
            return;
          }
          
          // Visualize the path
          renderGraph({
            nodes: data.nodes,
            relationships: data.relationships
          });
          
          // Highlight the path
          setTimeout(() => {
            if (cy) {
              cy.nodes().removeClass('highlighted neighbor');
              cy.nodes().addClass('highlighted');
              cy.edges().style('line-color', '#8b5cf6').style('target-arrow-color', '#8b5cf6').style('width', 4);
            }
          }, 500);
          
          alert(`Found path with ${data.path_length} hop(s) between ${data.source} and ${data.target}!`);
        } catch (e) {
          alert('Error finding path: ' + e.message);
        }
      }
      
      async function findAllPaths() {
        const source = document.getElementById('pathway-source').value.trim();
        const target = document.getElementById('pathway-target').value.trim();
        
        if (!source || !target) {
          alert('Please enter both source and target concepts');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const response = await fetch(`/api/pathway/all-paths?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}&max_paths=5&verified_only=${verifiedOnly}`);
          
          if (!response.ok) {
            throw new Error('Pathway search failed');
          }
          
          const data = await response.json();
          
          if (data.paths_found === 0) {
            alert(data.message || 'No paths found between these concepts');
            return;
          }
          
          // Combine all paths into one graph for visualization
          const allNodes = new Map();
          const allRels = new Map();
          
          data.paths.forEach(path => {
            path.nodes.forEach(node => {
              allNodes.set(node.id, node);
            });
            path.relationships.forEach(rel => {
              allRels.set(rel.id, rel);
            });
          });
          
          // Visualize all paths
          renderGraph({
            nodes: Array.from(allNodes.values()),
            relationships: Array.from(allRels.values())
          });
          
          // Highlight the paths
          setTimeout(() => {
            if (cy) {
              cy.nodes().removeClass('highlighted neighbor');
              cy.nodes().addClass('highlighted');
              cy.edges().style('line-color', '#6366f1').style('target-arrow-color', '#6366f1').style('width', 3);
            }
          }, 500);
          
          alert(`Found ${data.paths_found} path(s) between ${data.paths[0].source} and ${data.paths[0].target}!`);
        } catch (e) {
          alert('Error finding paths: ' + e.message);
        }
      }
      
      // ==========================================
      // QUERY BUILDER FUNCTIONS
      // ==========================================
      
      let currentQueryResults = null;
      
      async function loadGraphSchema() {
        try {
          const response = await fetch('/api/pathway/schema');
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          
          const data = await response.json();
          console.log('Schema loaded:', data);
          
          // Populate node type dropdowns
          const node1Select = document.getElementById('node1-type');
          const node2Select = document.getElementById('node2-type');
          
          // Clear existing options except "Any Type"
          node1Select.innerHTML = '<option value="">-- Any Type --</option>';
          node2Select.innerHTML = '<option value="">-- Any Type --</option>';
          
          // Add node types from database
          const nodeTypes = data.node_types || [];
          nodeTypes.forEach(type => {
            const option1 = document.createElement('option');
            option1.value = type;
            option1.textContent = type;
            node1Select.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = type;
            option2.textContent = type;
            node2Select.appendChild(option2);
          });
          
          // Populate relationship type dropdown
          const relSelect = document.getElementById('relationship-type');
          relSelect.innerHTML = '<option value="">-- Any Relationship --</option>';
          
          const relTypes = data.relationship_types || [];
          relTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            relSelect.appendChild(option);
          });
          
          console.log(`Loaded ${nodeTypes.length} node types and ${relTypes.length} relationship types`);
          
        } catch (e) {
          console.error('Failed to load graph schema:', e);
          alert('Failed to load schema from database. The dropdowns may be empty. Error: ' + e.message);
        }
      }
      
      function updatePatternPreview() {
        const node1Type = document.getElementById('node1-type').value || 'Entity';
        const node2Type = document.getElementById('node2-type').value || 'Entity';
        const relType = document.getElementById('relationship-type').value || 'ANY';
        const node1Name = document.getElementById('node1-name').value;
        const node2Name = document.getElementById('node2-name').value;
        
        let preview = `(${node1Type}`;
        if (node1Name) preview += `: "${node1Name}"`;
        preview += `)`;
        
        preview += ` -[${relType}]-> `;
        
        preview += `(${node2Type}`;
        if (node2Name) preview += `: "${node2Name}"`;
        preview += `)`;
        
        document.getElementById('pattern-preview').innerHTML = preview;
      }
      
      async function executePatternQuery() {
        const node1Type = document.getElementById('node1-type').value;
        const node2Type = document.getElementById('node2-type').value;
        const relType = document.getElementById('relationship-type').value;
        const node1Name = document.getElementById('node1-name').value;
        const node2Name = document.getElementById('node2-name').value;
        const limit = parseInt(document.getElementById('result-limit').value);
        const verifiedOnly = document.getElementById('verified-only-query').checked;
        const highConfidence = document.getElementById('high-confidence-only').checked;
        
        const requestBody = {
          node1_type: node1Type || null,
          node2_type: node2Type || null,
          relationship: relType || null,
          node1_name: node1Name || null,
          node2_name: node2Name || null,
          verified_only: verifiedOnly,
          high_confidence: highConfidence,
          limit: limit
        };
        
        try {
          document.getElementById('result-count').textContent = 'Executing query...';
          document.getElementById('query-results').innerHTML = '<div style="text-align: center; padding: 40px; color: #6b7280;">Loading results...</div>';
          
          const response = await fetch('/api/pathway/pattern', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
          });
          
          if (!response.ok) {
            throw new Error('Query execution failed');
          }
          
          const data = await response.json();
          
          if (!data.success) {
            throw new Error(data.message || 'Query failed');
          }
          
          currentQueryResults = data.matches || [];
          displayQueryResults(currentQueryResults);
          
        } catch (e) {
          document.getElementById('result-count').textContent = 'Error';
          document.getElementById('query-results').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
              <div style="font-size: 32px; margin-bottom: 12px;">⚠️</div>
              <p>Error: ${e.message}</p>
            </div>
          `;
          alert('Query execution failed: ' + e.message);
        }
      }
      
      function displayQueryResults(results) {
        const resultsContainer = document.getElementById('query-results');
        const resultCount = document.getElementById('result-count');
        
        if (!results || results.length === 0) {
          resultCount.textContent = '0 results';
          resultsContainer.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #9ca3af;">
              <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
              <p style="font-size: 16px; margin: 0;">
                No matches found for this pattern
              </p>
              <p style="font-size: 13px; margin-top: 8px; color: #6b7280;">
                Try adjusting your query parameters
              </p>
            </div>
          `;
          document.getElementById('visualize-section').style.display = 'none';
          return;
        }
        
        resultCount.textContent = `${results.length} result${results.length > 1 ? 's' : ''}`;
        
        let html = '';
        results.forEach((match, idx) => {
          const statusColor = match.relationship.status === 'verified' ? '#059669' : '#f59e0b';
          const confidenceBar = Math.round((match.relationship.confidence || 0.5) * 100);
          
          html += `
            <div class="query-result-card">
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <div style="flex: 1;">
                  <div style="font-weight: 600; color: #111827; font-size: 15px; margin-bottom: 4px;">
                    ${escapeHtml(match.node1.name)} 
                    <span style="color: #8b5cf6; font-size: 13px;">→</span> 
                    ${escapeHtml(match.node2.name)}
                  </div>
                  <div style="font-size: 12px; color: #6b7280;">
                    ${match.node1.type} → <strong>${match.relationship.type}</strong> → ${match.node2.type}
                  </div>
                </div>
                <div style="text-align: right;">
                  <span style="display: inline-block; padding: 3px 8px; background: ${statusColor}; color: white; border-radius: 4px; font-size: 11px; font-weight: 600;">
                    ${match.relationship.status || 'unverified'}
                  </span>
                </div>
              </div>
              
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #f3f4f6;">
                <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">Confidence</div>
                <div style="background: #f3f4f6; border-radius: 4px; height: 6px; overflow: hidden;">
                  <div style="background: #8b5cf6; height: 100%; width: ${confidenceBar}%;"></div>
                </div>
                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">${confidenceBar}%</div>
              </div>
            </div>
          `;
        });
        
        resultsContainer.innerHTML = html;
        document.getElementById('visualize-section').style.display = 'block';
      }
      
      function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      }
      
      function clearQueryBuilder() {
        document.getElementById('node1-type').value = '';
        document.getElementById('node2-type').value = '';
        document.getElementById('relationship-type').value = '';
        document.getElementById('node1-name').value = '';
        document.getElementById('node2-name').value = '';
        document.getElementById('verified-only-query').checked = false;
        document.getElementById('high-confidence-only').checked = false;
        document.getElementById('result-limit').value = '50';
        
        document.getElementById('pattern-preview').innerHTML = 'Select a template or build your own pattern';
        document.getElementById('result-count').textContent = 'No query executed yet';
        document.getElementById('query-results').innerHTML = `
          <div style="text-align: center; padding: 60px 20px; color: #9ca3af;">
            <div style="font-size: 48px; margin-bottom: 16px;">🔎</div>
            <p style="font-size: 16px; margin: 0;">
              Build and execute a query to see results
            </p>
          </div>
        `;
        document.getElementById('visualize-section').style.display = 'none';
        currentQueryResults = null;
      }
      
      function visualizeQueryResults() {
        if (!currentQueryResults || currentQueryResults.length === 0) {
          alert('No results to visualize');
          return;
        }
        
        // Extract nodes and relationships from query results
        const nodesMap = new Map();
        const relationships = [];
        
        currentQueryResults.forEach(match => {
          // Add node1
          if (!nodesMap.has(match.node1.id)) {
            nodesMap.set(match.node1.id, {
              id: match.node1.id,
              name: match.node1.name,
              type: match.node1.type
            });
          }
          
          // Add node2
          if (!nodesMap.has(match.node2.id)) {
            nodesMap.set(match.node2.id, {
              id: match.node2.id,
              name: match.node2.name,
              type: match.node2.type
            });
          }
          
          // Add relationship
          relationships.push({
            source: match.node1.id,
            target: match.node2.id,
            relation: match.relationship.type,
            confidence: match.relationship.confidence,
            status: match.relationship.status,
            polarity: 'positive'
          });
        });
        
        // Switch to viewing tab
        switchTab('viewing');
        
        // Render the graph
        setTimeout(() => {
          renderGraph({
            nodes: Array.from(nodesMap.values()),
            relationships: relationships
          });
        }, 300);
      }
      
      // ==========================================
      // GRAPH EXPORT FUNCTIONALITY
      // ==========================================
      
      async function exportGraph() {
        if (!cy) {
          alert('No graph loaded to export');
          return;
        }
        
        const format = document.getElementById('export-format').value;
        const nodes = [];
        const edges = [];
        
        // Collect visible nodes and edges from Cytoscape
        cy.nodes().forEach(node => {
          nodes.push({
            id: node.id(),
            label: node.data('label'),
            type: node.data('type'),
            significance: node.data('significance'),
            sources: node.data('sources')
          });
        });
        
        cy.edges().forEach(edge => {
          edges.push({
            id: edge.id(),
            source: edge.data('source'),
            target: edge.data('target'),
            relation: edge.data('relation'),
            status: edge.data('status'),
            polarity: edge.data('polarity'),
            confidence: edge.data('confidence'),
            significance: edge.data('significance'),
            sources: edge.data('sources')
          });
        });
        
        try {
          const response = await fetch('/api/export/graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              format: format,
              nodes: nodes,
              edges: edges
            })
          });
          
          if (!response.ok) {
            throw new Error('Export failed');
          }
          
          // Get filename from response headers or use default
          const contentDisposition = response.headers.get('Content-Disposition');
          let filename = `knowledge_graph_${new Date().toISOString().split('T')[0]}.${format}`;
          if (contentDisposition) {
            const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
            if (matches) filename = matches[1];
          }
          
          // Download the file
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          alert(`Graph exported successfully as ${format.toUpperCase()}!`);
        } catch (e) {
          alert('Export failed: ' + e.message);
        }
      }
      
      // ==========================================
      // EVENT LISTENERS & APPLICATION STARTUP
      // ==========================================
      
      // Wire filter checkboxes
      const showNegativeCheckbox = document.getElementById('show-negative');
      const verifiedOnlyCheckbox = document.getElementById('verified-only');
      
      if (showNegativeCheckbox) {
        showNegativeCheckbox.addEventListener('change', () => {
          filterGraphBySearch(document.getElementById('search-input')?.value || '');
        });
      }
      
      if (verifiedOnlyCheckbox) {
        verifiedOnlyCheckbox.addEventListener('change', () => {
          filterGraphBySearch(document.getElementById('search-input')?.value || '');
        });
      }

      // Initialize on load
      init();
    </script>
  </body>
</html>
""".strip()


@router.get("")
def serve_main_ui():
    """Serve the main unified UI with Ingestion and Viewing tabs."""
    return Response(
        content=HTML, 
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
