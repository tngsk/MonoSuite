# Mono Architecture and System Overview

This document outlines the core architecture, design principles, processing flow, and server capabilities of the Mono project. Mono is a build system that parses Markdown files and generates domain-specific, interactive, monolithic HTML files.

## 1. Core Principles and UX/UI Design

*   **Target Environment:** User browsers across various devices.
*   **Core Value:** Zero-dependency portability, immediate feedback, and precise media synchronization control.
*   **Fundamental Rule:** The minimal HTML text and explanatory images must be displayed and guaranteed even in offline environments to prevent information loss.
*   **Configuration Strategy:** "One-file portability" is a requirement for the output HTML, not the input. Settings are isolated in external files (e.g., `config.toml`) rather than embedded in Markdown frontmatter, preventing the mixing of external dependencies.
*   **UX/UI Design:**
    *   **Typography & Style:** Prioritizes participant readability using a DaisyUI-inspired CSS variable theme system (`themes.toml`).
    *   **Visual Feedback:** Provides immediate visual responses (e.g., color changes, checkmarks) to user inputs.
    *   **Accessibility:** Maintains semantic HTML structures and ensures full keyboard navigability.

## 2. Layered Architecture

To ensure maintainability and extendability, Mono adopts a layered module architecture:

1.  **Interface Layer (`src/main.py`, `config.py`)**: Handles CLI input/output and configuration parsing.
2.  **Processing Layer (`src/processors/`)**: Orchestrates the conversion process (`MarkdownProcessor`, `HTMLDocumentBuilder`, `PDFProcessor`).
3.  **Embedding Layer (`src/embedders/`)**: Responsible for embedding media as Base64 (`MediaEmbedder`) and injecting dynamic themes and CSS (`CSSEmbedder`).
4.  **Data I/O Layer (`src/handlers/`)**: Manages file read/write operations and MIME type resolution.
5.  **Component Templates Layer (`src/components/`)**: Manages Web Components (HTML/JS/CSS). The build process dynamically scans these and packs them into a single file ("Component-Based Split" architecture).

### Dependency Minimalism

*   **Parser:** `markdown` (Python) - standard and highly extensible.
*   **DOM Manipulation:** Python's standard `re` (regex) - ensures high-speed, memory-efficient stream-like replacement without heavy dependencies like `BeautifulSoup4`.
*   **Frontend Runtime:** Vanilla JS / Web Components without heavy frameworks. All JS/CSS are packed inline into the final HTML during conversion.
*   **Optional Heavy Dependencies:** Tools like Playwright (for PDF export) or Node.js (for math/syntax highlighting) are isolated. The system degrades gracefully if they are unavailable.

## 3. Conversion Processing Flow

The conversion from Markdown to a single HTML file is orchestrated by `MarkdownToHTMLConverter` in `src/converter.py`:

1.  **Read Markdown:** `FileHandler` reads the input file.
2.  **Markdown to HTML Conversion (`MarkdownProcessor`)**:
    *   Protects code blocks.
    *   Safely loads allowed component parsers (`src/components/*/parser.py`) to evaluate and replace custom directives.
    *   Applies standard Python-Markdown processing and custom extensions (`src/extensions/`).
    *   Restores code blocks.
3.  **Load CSS (`CSSEmbedder`)**: Reads external CSS files specified via `--css`.
4.  **Embed Media (`MediaEmbedder`)**: Extracts images and media resources, converts them to Base64, and inlines them.
5.  **Build HTML Document (`HTMLDocumentBuilder`)**: Assembles the final structure using templates (e.g., `base.html`), injecting headers, bodies, scripts, and styles.
6.  **Embed CSS (`CSSEmbedder`)**: Injects themes and user CSS into the assembled document.
7.  **Validate Output:** Checks file size (warns at >20MB, halts at >30MB unless `--force` is used) and saves the HTML.
8.  **Optional PDF Generation (`PDFProcessor`)**: Generates a PDF via Playwright if requested.

## 4. Server Architecture (FastAPI + SSE)

Mono provides a built-in server (`server.py`) for real-time synchronization and data collection.

*   **Execution:** `uv run server.py` (Defaults to `http://0.0.0.0:8000`).
*   **Endpoints:**
    *   `/api/sync/stream` & `/api/sync`: Server-Sent Events (SSE) for real-time state sync (e.g., scrolling positions via `mono-sync`).
    *   `/api/data` (POST): Receives event data (votes, reactions) from components and saves them to `data.jsonl`.
*   **Security:** Configured via `config.toml` under `[security]`. It includes CORS policies and a `max-upload-size` (default 1MB) to prevent DoS attacks.
*   **Concurrency:** File writes are serialized using an `asyncio.Queue` and a background worker task to prevent race conditions.

### Server-Integrated Components

*   **`mono-sync`**: The core hub component. It detects the host's scroll position and broadcasts it via SSE to participants. It also acts as an intermediary, capturing events from other components (like `mono-poll`) and sending them to `/api/data`.
*   **`mono-export`**: A floating utility to manually download `localStorage` data as JSON or sync it directly to `/api/data`. Enabled via `--export`.
*   **Interactive Components (e.g., `mono-poll`, `mono-reaction`, `mono-notebook`, `mono-session-join`)**: These emit events upon user interaction. If the server is offline, they gracefully degrade by falling back to `localStorage`.
